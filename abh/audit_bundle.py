from __future__ import annotations

from pathlib import Path

from .audits import load_audit
from .errors import validate_identifier
from .plans import load_plan, verification_freshness_summary
from .storage import audit_doc_path, audit_json_path, plan_doc_path, plan_json_path, root_dir, verification_path


def evidence_path(path: Path) -> str:
    return path.as_posix()


def audit_protocol_v2(plan_id: str, cwd: Path | None = None) -> dict[str, object]:
    """Self-contained audit package for agent-to-agent handoff.

    Includes everything an independent audit agent needs without
    exploring the repository: plan details, attractor invariants,
    changed files, verification breakdown, related memories, and
    pre-computed self-check results.
    """
    root = root_dir(cwd)
    plan = load_plan(plan_id, cwd)
    verification_summary = verification_freshness_summary(plan, cwd)

    # Attractor invariants
    from .attractors import active_attractor
    try:
        attractor = active_attractor(cwd)
        attractor_info: dict[str, object] = {"id": attractor.id, "title": attractor.title, "invariants": list(attractor.invariants)}
    except Exception:
        attractor_info = {"id": "", "title": "unavailable", "invariants": []}

    # Changed files since baseline
    changed_files: list[str] = []
    diff_summary = ""
    if getattr(plan, "baseline_commit", ""):
        import subprocess
        try:
            r = subprocess.run(
                ["git", "diff", "--name-only", plan.baseline_commit],
                cwd=root, text=True, capture_output=True, timeout=10,
            )
            if r.returncode == 0:
                changed_files = [p.strip() for p in r.stdout.splitlines() if p.strip()]
            r2 = subprocess.run(
                ["git", "diff", "--stat", plan.baseline_commit],
                cwd=root, text=True, capture_output=True, timeout=10,
            )
            if r2.returncode == 0:
                diff_summary = r2.stdout.strip().split("\n")[-1] if r2.stdout.strip() else ""
        except Exception:
            pass

    # Related memories
    from .navigation import _related_memories
    from .memory import load_memory as _load_mem
    related_memories = []
    for mem_id in _related_memories(plan, cwd)[:5]:
        try:
            mem = _load_mem(mem_id, cwd)
            related_memories.append({"id": mem.id, "summary": mem.summary, "memory_type": mem.memory_type})
        except Exception:
            pass

    # Self-check
    self_check = _compute_self_check(plan, verification_summary, changed_files)

    # Evidence paths
    evidence_paths: list[str] = []
    evidence_paths.append(evidence_path(plan_doc_path(plan.id, cwd)))
    evidence_paths.append(evidence_path(plan_json_path(plan.id, cwd)))
    latest_id = verification_summary.get("latest_id")
    if latest_id:
        evidence_paths.append(evidence_path(verification_path(str(latest_id), cwd)))
    for audit_id in plan.audit_ids:
        evidence_paths.append(evidence_path(audit_json_path(audit_id, cwd)))

    return {
        "protocol_version": "2",
        "plan": {
            "id": plan.id,
            "title": plan.title,
            "status": plan.status,
            "goals": list(plan.goals),
            "non_goals": list(plan.non_goals),
            "exit_criteria": list(plan.exit_criteria),
            "closure_evidence": list(plan.closure_evidence),
        },
        "attractor": attractor_info,
        "verification": {
            "id": latest_id,
            "result": verification_summary.get("result"),
            "stale": verification_summary.get("stale"),
            "reasons": verification_summary.get("reasons", []),
        },
        "changed_files": changed_files,
        "diff_summary": diff_summary,
        "related_memories": related_memories,
        "self_check": self_check,
        "evidence_paths": evidence_paths,
        "instructions": (
            "Read the evidence paths. Check goals against code changes, "
            "non-goals against implementation, exit criteria against verification. "
            "Verify the self_check claims adversarially. "
            "Return a JSON object: "
            '{"result": "pass|fail|partial|need_info", "rationale": "...", '
            '"independence": "independent|self_review|unknown", '
            '"findings": [{"severity": "low|medium|high", "title": "...", '
            '"evidence": "...", "recommendation": "..."}], '
            '"follow_ups": ["..."]}. '
            "Do NOT modify files. Return ONLY the JSON object."
        ),
    }


def _compute_self_check(plan, verification_summary, changed_files: list[str]) -> dict[str, object]:
    """Pre-audit self-check: exit criteria, non-goals, scope, evidence."""
    checks: list[dict[str, object]] = []

    # Exit criteria coverage
    exit_ok = len(plan.exit_criteria) > 0 and verification_summary.get("result") == "pass"
    checks.append({
        "check": "exit_criteria_covered",
        "status": "pass" if exit_ok else "fail",
        "detail": f"{len(plan.exit_criteria)} criteria, verification={verification_summary.get('result')}",
    })

    # Closure evidence
    evidence_ok = len(plan.closure_evidence) > 0
    checks.append({
        "check": "closure_evidence_present",
        "status": "pass" if evidence_ok else "fail",
        "detail": f"{len(plan.closure_evidence)} evidence items",
    })

    # Verification freshness
    stale = verification_summary.get("stale")
    reasons = verification_summary.get("reasons", [])
    git_only = set(reasons) <= {"git_commit_changed", "git_status_changed"} if reasons else True
    fresh_ok = not stale or git_only
    checks.append({
        "check": "verification_fresh",
        "status": "pass" if fresh_ok else "fail",
        "detail": f"stale={stale}, reasons={reasons}",
    })

    # Non-goal check: scan changed files against plan non-goals (advisory only)
    non_goal_violations = []
    for f in changed_files:
        f_base = f.split("/")[-1].lower().replace(".py", "").replace(".md", "")
        for ng in plan.non_goals:
            ng_lower = ng.lower()
            # Only flag if a significant keyword from the non-goal matches a filename
            for kw in ng_lower.split():
                if len(kw) > 4 and kw in f_base:
                    non_goal_violations.append(f"File {f} may relate to non-goal: {ng}")
                    break
    checks.append({
        "check": "non_goals_intact",
        "status": "info",
        "detail": f"{len(non_goal_violations)} potential concerns" if non_goal_violations else "no concerns detected",
        "violations": non_goal_violations[:5],
    })

    return {
        "all_pass": all(c["status"] == "pass" for c in checks),
        "checks": checks,
    }


def audit_bundle(plan_id: str, cwd: Path | None = None) -> dict[str, object]:
    validate_identifier(plan_id, "plan id")
    root = root_dir(cwd)
    plan = load_plan(plan_id, cwd)
    verification_summary = verification_freshness_summary(plan, cwd)
    latest_verification_id = verification_summary.get("latest_id")
    latest_verification_path = (
        evidence_path(verification_path(str(latest_verification_id), cwd)) if latest_verification_id else None
    )

    requested_audits: list[dict[str, object]] = []
    audit_evidence_paths: list[str] = []
    for audit_id in plan.audit_ids:
        audit = load_audit(audit_id, cwd)
        requested_audits.append(
            {
                "id": audit.id,
                "auditor": audit.auditor,
                "auditor_context": audit.auditor_context,
                "independence": audit.independence,
                "verification_id": audit.verification_id,
                "scope": audit.scope,
                "status": audit.status,
                "result": audit.result,
                "evidence": list(audit.evidence),
                "json_path": evidence_path(audit_json_path(audit.id, cwd)),
                "doc_path": evidence_path(audit_doc_path(audit.id, cwd)),
            }
        )
        audit_evidence_paths.extend(
            [evidence_path(audit_json_path(audit.id, cwd)), evidence_path(audit_doc_path(audit.id, cwd))]
        )

    evidence = {
        "plan": [evidence_path(plan_doc_path(plan.id, cwd)), evidence_path(plan_json_path(plan.id, cwd))],
        "latest_verification": latest_verification_path,
        "audits": audit_evidence_paths,
        "closure_evidence": list(plan.closure_evidence),
    }
    prompt = render_audit_prompt(
        root=root,
        plan_id=plan.id,
        plan_title=plan.title,
        evidence=evidence,
        verification_summary=verification_summary,
    )

    return {
        "schema_version": "1",
        "plan": {
            "id": plan.id,
            "title": plan.title,
            "status": plan.status,
            "attractor": plan.attractor,
            "goals": list(plan.goals),
            "non_goals": list(plan.non_goals),
            "exit_criteria": list(plan.exit_criteria),
        },
        "latest_verification": verification_summary,
        "requested_audits": requested_audits,
        "evidence": evidence,
        "prompt": prompt,
        "write_policy": "read_only; does not request, record, transition, close, or execute audits",
    }


def render_audit_prompt(
    *,
    root: Path,
    plan_id: str,
    plan_title: str,
    evidence: dict[str, object],
    verification_summary: dict[str, object],
) -> str:
    evidence_paths: list[str] = []
    for value in evidence.values():
        if isinstance(value, list):
            evidence_paths.extend(str(item) for item in value)
        elif value:
            evidence_paths.append(str(value))
    evidence_text = "; ".join(evidence_paths)
    stale = verification_summary.get("stale")
    stale_reasons = verification_summary.get("reasons", [])
    return (
        "Independent audit only. Do not modify files. "
        f"Repo: {root}. Audit {plan_id} ({plan_title}) against goals, non-goals, exit criteria, "
        "docs, code, and verification evidence. "
        f"Evidence: {evidence_text}. "
        f"Latest verification: result={verification_summary.get('result')}, "
        f"trust={verification_summary.get('trust_level')}, stale={stale}, reasons={stale_reasons}. "
        "Check that verification covers the exit criteria and that no non-goals were implemented. "
        "Semantic conservation: check whether any in-scope commitments disappeared, weakened, or moved "
        "to non-authoritative artifacts. Distinguish J-flow-only evidence that only routes or restates "
        "commitments from R-flow uncertainty reduction that proves, decides, or aligns commitments with "
        "authoritative owner docs and executable evidence. "
        "Return exactly: Result: pass|fail|partial|need_info\n"
        "Rationale: ...\n"
        "Findings:\n"
        "Severity|Title|Evidence|Recommendation. If no findings, Findings:\nnone"
    )
