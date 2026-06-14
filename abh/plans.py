from __future__ import annotations

import hashlib
import json
from pathlib import Path
from datetime import datetime

from .errors import AbhError, require_existing_path, validate_identifier
from .models import CommitmentPhaseState, CommitmentResidualPressure, PLAN_STATUSES, PlanRecord, utc_now
from .storage import (
    ensure_workspace,
    plan_doc_path,
    plan_json_path,
    plans_dir,
    read_json,
    write_json,
    write_json_markdown_pair,
)

PLAN_BOOKKEEPING_FIELDS = {"closure_evidence", "commitment_phase_state", "verification_runs", "audit_ids", "status", "doc_path", "updated_at"}

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"ready"},
    "ready": {"running", "blocked"},
    "running": {"blocked", "closing"},
    "blocked": {"running", "closing"},
    "closing": {"closed"},
    "closed": set(),
}

PLAN_VERIFICATION_FIELDS = (
    "title",
    "attractor",
    "baseline",
    "goals",
    "non_goals",
    "exit_criteria",
    "validation_checklist",
    "closure_evidence",
)


def list_plans(cwd: Path | None = None, *, limit: int | None = None, offset: int = 0, status: str | None = None) -> list[PlanRecord]:
    directory = plans_dir(cwd)
    if not directory.exists():
        return []
    plans: list[PlanRecord] = []
    for path in sorted(directory.glob("*.json")):
        plans.append(PlanRecord.from_dict(read_json(path)))
    if status:
        plans = [p for p in plans if p.status == status]
    if offset:
        plans = plans[offset:]
    if limit is not None:
        plans = plans[:limit]
    return plans


def load_plan(plan_id: str, cwd: Path | None = None) -> PlanRecord:
    validate_identifier(plan_id, "plan id")
    path = plan_json_path(plan_id, cwd)
    if not path.exists():
        raise AbhError(f"plan not found: {plan_id}")
    return PlanRecord.from_dict(read_json(path))


def save_plan(plan: PlanRecord, cwd: Path | None = None, write_doc: bool = True) -> PlanRecord:
    """Save a plan to disk.

    Raises AbhError if a closed plan is being modified in proof-bearing
    fields. Bookkeeping fields (closure_evidence, commitment_phase_state,
    etc.) are allowed to change after close.
    """
    if plan.status == "closed":
        plan_path = plan_json_path(plan.id, cwd)
        if plan_path.exists():
            existing = PlanRecord.from_dict(read_json(plan_path))
            if existing.status == "closed":
                current = plan.to_dict()
                prior = existing.to_dict()
                for key in sorted(set(prior) | set(current)):
                    if key in PLAN_BOOKKEEPING_FIELDS:
                        continue
                    if key in ("schema_version", "created_at"):
                        continue
                    if prior.get(key) != current.get(key):
                        raise AbhError(f"cannot modify closed plan {plan.id}: field {key!r} changed; reopen via transition if intentional")
    ensure_workspace(cwd)
    plan.updated_at = utc_now()
    if write_doc:
        doc_path = plan.doc_path or str(plan_doc_path(plan.id, cwd))
        plan.doc_path = doc_path
        doc = render_plan_markdown(plan)
        doc_file = Path(doc_path)
        write_json_markdown_pair(plan_json_path(plan.id, cwd), plan.to_dict(), doc_file, doc)
    else:
        write_json(plan_json_path(plan.id, cwd), plan.to_dict())
    return plan


def create_plan(
    *,
    plan_id: str,
    title: str,
    attractor: str,
    baseline: str,
    owner: str = "platform",
    status: str = "draft",
    goals: list[str] | None = None,
    non_goals: list[str] | None = None,
    exit_criteria: list[str] | None = None,
    validation_checklist: list[str] | None = None,
    closure_evidence: list[str] | None = None,
    commitment_phase_state: CommitmentPhaseState | None = None,
    cwd: Path | None = None,
) -> PlanRecord:
    ensure_workspace(cwd)
    validate_identifier(plan_id, "plan id")
    if status not in {"draft", "ready"}:
        raise AbhError("plan create only supports draft or ready status")
    plan_path = plan_json_path(plan_id, cwd)
    if plan_path.exists():
        raise AbhError(f"plan already exists: {plan_id}")
    if status == "ready":
        from .attractors import is_active_attractor_reference

        if not is_active_attractor_reference(attractor, cwd):
            raise AbhError("plan ready requires current active attractor id or path")
    else:
        require_existing_path(attractor, "attractor")
    plan = PlanRecord(
        id=plan_id,
        title=title,
        attractor=attractor,
        baseline=baseline,
        owner=owner,
        status=status,
        goals=list(goals or []),
        non_goals=list(non_goals or []),
        exit_criteria=list(exit_criteria or []),
        validation_checklist=list(validation_checklist or []),
        closure_evidence=list(closure_evidence or []),
        commitment_phase_state=commitment_phase_state or CommitmentPhaseState(),
        doc_path=str(plan_doc_path(plan_id, cwd)),
    )
    if status == "ready":
        validate_plan_ready(plan)
    return save_plan(plan, cwd=cwd, write_doc=True)


def append_unique(existing: list[str], additions: list[str] | None) -> list[str]:
    values = list(existing)
    for item in additions or []:
        if item not in values:
            values.append(item)
    return values


def update_plan_record(
    *,
    plan_id: str,
    goals: list[str] | None = None,
    non_goals: list[str] | None = None,
    exit_criteria: list[str] | None = None,
    validation_checklist: list[str] | None = None,
    remove_validation_checklist: list[str] | None = None,
    closure_evidence: list[str] | None = None,
    commitment_phase_state: CommitmentPhaseState | None = None,
    cwd: Path | None = None,
) -> PlanRecord:
    plan = load_plan(plan_id, cwd)
    if not any(
        (
            goals,
            non_goals,
            exit_criteria,
            validation_checklist,
            remove_validation_checklist,
            closure_evidence,
            commitment_phase_state,
        )
    ):
        raise AbhError("plan update requires at least one field to append")
    plan.goals = append_unique(plan.goals, goals)
    plan.non_goals = append_unique(plan.non_goals, non_goals)
    plan.exit_criteria = append_unique(plan.exit_criteria, exit_criteria)
    plan.validation_checklist = append_unique(plan.validation_checklist, validation_checklist)
    for item in remove_validation_checklist or []:
        plan.validation_checklist = [value for value in plan.validation_checklist if value != item]
    plan.closure_evidence = append_unique(plan.closure_evidence, closure_evidence)
    if commitment_phase_state is not None:
        state = plan.commitment_phase_state
        state.stable_state_now = append_unique(state.stable_state_now, commitment_phase_state.stable_state_now)
        state.active_change_pressure = append_unique(
            state.active_change_pressure,
            commitment_phase_state.active_change_pressure,
        )
        state.target_stable_state = append_unique(
            state.target_stable_state,
            commitment_phase_state.target_stable_state,
        )
        state.conversion_proof = append_unique(state.conversion_proof, commitment_phase_state.conversion_proof)
        for item in commitment_phase_state.residual_pressure:
            if item not in state.residual_pressure:
                state.residual_pressure.append(item)
    return save_plan(plan, cwd=cwd, write_doc=True)


def validate_plan_ready(plan: PlanRecord) -> None:
    missing: list[str] = []
    if not plan.title.strip():
        missing.append("title")
    if not plan.attractor.strip():
        missing.append("attractor")
    if not plan.baseline.strip():
        missing.append("baseline")
    if not plan.goals:
        missing.append("goals")
    if not plan.non_goals:
        missing.append("non_goals")
    if not plan.exit_criteria:
        missing.append("exit_criteria")
    if not plan.validation_checklist:
        missing.append("validation_checklist")
    if not plan.closure_evidence:
        missing.append("closure_evidence")
    if missing:
        raise AbhError(f"plan is not ready; missing: {', '.join(missing)}")
    from .attractors import is_active_attractor_reference

    if not is_active_attractor_reference(plan.attractor):
        raise AbhError("plan is not ready; attractor must reference current active attractor id or path")


def transition_plan(plan_id: str, target_status: str, cwd: Path | None = None) -> PlanRecord:
    if target_status not in PLAN_STATUSES:
        raise AbhError(f"invalid target status: {target_status}")
    plan = load_plan(plan_id, cwd)
    allowed = ALLOWED_TRANSITIONS[plan.status]
    if target_status not in allowed:
        raise AbhError(f"invalid transition: {plan.status} -> {target_status}")
    if target_status == "ready":
        validate_plan_ready(plan)
    if target_status == "closing":
        if not plan.verification_runs:
            raise AbhError("cannot move to closing without verification runs")
        from .verifications import load_verification

        latest = load_verification(plan.verification_runs[-1], cwd)
        if latest.result != "pass":
            raise AbhError("cannot move to closing without a passing verification run")
    plan.status = target_status
    return save_plan(plan, cwd)


def close_plan(plan_id: str, cwd: Path | None = None) -> PlanRecord:
    plan = load_plan(plan_id, cwd)
    passing_audit = None
    rejection_reasons: list[str] = []
    from .audits import load_audit

    for audit_id in plan.audit_ids:
        audit = load_audit(audit_id, cwd)
        if audit.result == "pass" and audit.status == "complete":
            reason = audit_close_blocker(plan, audit, cwd)
            if reason:
                rejection_reasons.append(f"{audit.id}: {reason}")
                continue
            passing_audit = audit
    if passing_audit is None:
        if rejection_reasons:
            raise AbhError(f"cannot close plan without independent fresh passing audit ({'; '.join(rejection_reasons)})")
        raise AbhError("cannot close plan without a passing audit")
    if not plan.closure_evidence:
        raise AbhError("cannot close plan without closure evidence")
    # Structural scope check: compare baseline vs current diff against plan scope.
    from .boundary import check_plan_scope
    scope_findings = check_plan_scope(plan_id=plan_id, cwd=cwd)
    if scope_findings:
        lines = "\n".join(f"  - [{f.severity}] {f.evidence}" for f in scope_findings)
        raise AbhError(f"plan scope violations detected; cannot close:\n{lines}")
    plan.status = "closed"
    if passing_audit.id not in plan.closure_evidence:
        plan.closure_evidence.append(passing_audit.id)
    return save_plan(plan, cwd)


def audit_close_blocker(plan: PlanRecord, audit, cwd: Path | None = None) -> str | None:
    if audit.independence != "independent":
        return "audit is not marked independent"
    if not audit.verification_id:
        return "audit is missing verification_id"
    summary = verification_freshness_summary(plan, cwd)
    latest_id = summary.get("latest_id")
    if audit.verification_id != latest_id:
        return "audit verification_id does not match latest verification"
    if summary.get("result") != "pass":
        return "latest verification is not passing"
    if summary.get("stale"):
        reasons = summary.get("reasons", [])
        return f"latest verification is stale: {reasons}"
    return None


def render_plan_markdown(plan: PlanRecord) -> str:
    def bullet_lines(values: list[str]) -> str:
        if not values:
            return "- "
        return "\n".join(f"- {value}" for value in values)

    def residual_lines(values: list[CommitmentResidualPressure]) -> str:
        if not values:
            return "- "
        return "\n".join(
            f"- {item.pressure} | Non-blocking rationale: {item.non_blocking_rationale}"
            for item in values
        )

    commitment = plan.commitment_phase_state

    return (
        f"# Plan: {plan.title}\n\n"
        "## Metadata\n\n"
        f"- ID: {plan.id}\n"
        f"- Status: {plan.status}\n"
        f"- Attractor: {plan.attractor}\n"
        f"- Baseline: {plan.baseline}\n"
        f"- Owner: {plan.owner}\n"
        f"- Created: {plan.created_at}\n"
        f"- Updated: {plan.updated_at}\n\n"
        "## Goals\n\n"
        f"{bullet_lines(plan.goals)}\n\n"
        "## Non-Goals\n\n"
        f"{bullet_lines(plan.non_goals)}\n\n"
        "## Exit Criteria\n\n"
        f"{bullet_lines(plan.exit_criteria)}\n\n"
        "## Commitment Phase State\n\n"
        "### Stable State Now\n\n"
        f"{bullet_lines(commitment.stable_state_now)}\n\n"
        "### Active Change Pressure\n\n"
        f"{bullet_lines(commitment.active_change_pressure)}\n\n"
        "### Target Stable State\n\n"
        f"{bullet_lines(commitment.target_stable_state)}\n\n"
        "### Conversion Proof\n\n"
        f"{bullet_lines(commitment.conversion_proof)}\n\n"
        "### Residual Pressure\n\n"
        f"{residual_lines(commitment.residual_pressure)}\n\n"
        "## Validation Checklist\n\n"
        f"{bullet_lines(plan.validation_checklist)}\n\n"
        "## Closure Evidence\n\n"
        f"{bullet_lines(plan.closure_evidence)}\n\n"
        "## Verification Runs\n\n"
        f"{bullet_lines(plan.verification_runs)}\n\n"
        "## Audits\n\n"
        f"{bullet_lines(plan.audit_ids)}\n"
    )


def plan_status_line(plan: PlanRecord) -> str:
    latest = plan.verification_runs[-1] if plan.verification_runs else "none"
    return (
        f"{plan.id} [{plan.status}]\n"
        f"title: {plan.title}\n"
        f"attractor: {plan.attractor}\n"
        f"baseline: {plan.baseline}\n"
        f"verification_runs: {len(plan.verification_runs)}\n"
        f"latest_verification: {latest}\n"
        f"audits: {len(plan.audit_ids)}"
    )


def plan_verification_payload(plan: PlanRecord) -> dict[str, object]:
    data = plan.to_dict()
    return {field: data[field] for field in PLAN_VERIFICATION_FIELDS}


def plan_verification_hash(plan: PlanRecord) -> str:
    payload = json.dumps(plan_verification_payload(plan), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def plan_verification_snapshot(plan: PlanRecord) -> dict[str, object]:
    payload = plan_verification_payload(plan)
    return {
        "updated_at": plan.updated_at,
        "content_hash": hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "payload": payload,
        "validation_checklist": list(plan.validation_checklist),
    }


def parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def verification_commands(run) -> list[str]:
    commands = run.environment.get("commands", [])
    if isinstance(commands, list):
        values: list[str] = []
        for item in commands:
            if isinstance(item, dict) and isinstance(item.get("command"), str):
                values.append(item["command"])
        if values:
            return values
    return [part.strip() for part in run.command.split(" && ") if part.strip()]


def verification_plan_snapshot(run) -> dict[str, object]:
    plan_snapshot = run.environment.get("plan")
    return plan_snapshot if isinstance(plan_snapshot, dict) else {}


def append_git_stale_reasons(reasons: list[str], run, cwd: Path | None = None) -> None:
    recorded_git = run.environment.get("git")
    if not isinstance(recorded_git, dict) or not recorded_git.get("available"):
        return

    from .verifications import git_metadata

    root = Path.cwd() if cwd is None else Path(cwd)
    current_git = git_metadata(root)
    if not current_git.get("available"):
        return
    if recorded_git.get("commit") != current_git.get("commit"):
        reasons.append("git_commit_changed")
    if recorded_git.get("status_hash") != current_git.get("status_hash"):
        reasons.append("git_status_changed")


def changed_git_status_paths(run, cwd: Path | None = None) -> list[str] | None:
    recorded_git = run.environment.get("git")
    if not isinstance(recorded_git, dict) or not recorded_git.get("available"):
        return None

    from .verifications import git_metadata, normalized_git_status

    root = Path.cwd() if cwd is None else Path(cwd)
    current_git = git_metadata(root)
    if not current_git.get("available"):
        return None
    if recorded_git.get("commit") != current_git.get("commit"):
        return None
    if recorded_git.get("status_hash") == current_git.get("status_hash"):
        return []

    import subprocess

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    if status.returncode != 0:
        return None
    paths: list[str] = []
    for line in normalized_git_status(status.stdout).splitlines():
        if len(line) < 4:
            continue
        raw_path = line[3:]
        paths.extend(part.strip().replace("\\", "/") for part in raw_path.split(" -> ") if part.strip())
    return sorted(set(paths))


def append_structure_stale_reasons(reasons: list[str], run, cwd: Path | None = None) -> None:
    """Append ``structure_changed`` to reasons if the import topology changed."""
    recorded_hash = run.environment.get("structure_hash")
    if not isinstance(recorded_hash, str):
        return
    root = Path.cwd() if cwd is None else Path(cwd)
    try:
        from .boundary import compute_structure_hash
        if compute_structure_hash(root) != recorded_hash:
            reasons.append("structure_changed")
    except Exception:
        pass


POST_CLOSE_DOC_SYNC_PATHS = {
    "docs/development-roadmap.md",
    "docs/task-board.md",
}


def changed_verification_fields(snapshot: dict[str, object], plan: PlanRecord) -> list[str] | None:
    payload = snapshot.get("payload")
    if not isinstance(payload, dict):
        return None
    current = plan_verification_payload(plan)
    return [field for field in PLAN_VERIFICATION_FIELDS if payload.get(field) != current.get(field)]


def close_bookkeeping_only(snapshot: dict[str, object], plan: PlanRecord, changed_fields: list[str] | None) -> bool:
    if plan.status != "closed" or changed_fields != ["closure_evidence"]:
        return False
    payload = snapshot.get("payload")
    if not isinstance(payload, dict):
        return False
    previous = payload.get("closure_evidence")
    if not isinstance(previous, list):
        return False
    prior_values = [str(item) for item in previous]
    current_values = [str(item) for item in plan.closure_evidence]
    added = [item for item in current_values if item not in prior_values]
    return bool(added) and all(item in plan.audit_ids for item in added)


def stale_reason_detail(
    reason: str,
    plan: PlanRecord,
    *,
    snapshot: dict[str, object] | None = None,
    git_status_paths: list[str] | None = None,
) -> dict[str, object]:
    category = "product_proof_drift"
    trigger = "product_or_validation_state"
    requires_fresh_verification = True
    changed_fields = changed_verification_fields(snapshot or {}, plan)
    if plan.status == "closed" and reason == "plan_updated_after_verification":
        if close_bookkeeping_only(snapshot or {}, plan, changed_fields):
            category = "governance_metadata_churn"
            trigger = "closed_plan_metadata"
            requires_fresh_verification = False
        else:
            trigger = "proof_bearing_plan_fields"
    elif reason == "git_status_changed":
        trigger = "repository_state"
        if plan.status == "closed" and git_status_paths and set(git_status_paths) <= POST_CLOSE_DOC_SYNC_PATHS:
            category = "governance_metadata_churn"
            trigger = "post_close_documentation_sync"
            requires_fresh_verification = False
    elif reason == "git_commit_changed":
        trigger = "repository_commit"
    elif reason == "validation_checklist_changed":
        trigger = "validation_checklist"
    elif reason == "structure_changed":
        trigger = "structural_topology"
    elif reason == "no_verification_runs":
        trigger = "missing_verification"
    detail = {
        "reason": reason,
        "category": category,
        "trigger": trigger,
        "requires_fresh_verification": requires_fresh_verification,
    }
    if changed_fields is not None:
        detail["changed_fields"] = changed_fields
    if git_status_paths is not None and reason == "git_status_changed":
        detail["changed_paths"] = git_status_paths
    return detail


def freshness_class_for(details: list[dict[str, object]]) -> str:
    if not details:
        return "fresh"
    if any(item.get("category") == "product_proof_drift" for item in details):
        return "product_proof_drift"
    if any(item.get("category") == "governance_metadata_churn" for item in details):
        return "governance_metadata_churn"
    return "unknown_stale"


def verification_freshness_summary(plan: PlanRecord, cwd: Path | None = None) -> dict[str, object]:
    if not plan.verification_runs:
        details = [stale_reason_detail("no_verification_runs", plan)]
        return {
            "latest_id": None,
            "result": None,
            "trust_level": "unknown",
            "stale": True,
            "reasons": ["no_verification_runs"],
            "reason_details": details,
            "freshness_class": freshness_class_for(details),
            "requires_fresh_verification": True,
        }

    from .verifications import load_verification

    latest = load_verification(plan.verification_runs[-1], cwd)
    reasons: list[str] = []
    snapshot = verification_plan_snapshot(latest)
    snapshot_hash = snapshot.get("content_hash")
    if isinstance(snapshot_hash, str) and snapshot_hash != plan_verification_hash(plan):
        reasons.append("plan_updated_after_verification")
    elif not snapshot_hash:
        plan_updated = parse_timestamp(plan.updated_at)
        verification_created = parse_timestamp(latest.created_at)
        if plan_updated and verification_created and plan_updated > verification_created:
            reasons.append("plan_updated_after_verification")
    if verification_commands(latest) != list(plan.validation_checklist):
        reasons.append("validation_checklist_changed")
    append_git_stale_reasons(reasons, latest, cwd)
    append_structure_stale_reasons(reasons, latest, cwd)
    git_status_paths = changed_git_status_paths(latest, cwd) if "git_status_changed" in reasons else None
    details = [
        stale_reason_detail(
            reason,
            plan,
            snapshot=snapshot,
            git_status_paths=git_status_paths if reason == "git_status_changed" else None,
        )
        for reason in reasons
    ]

    return {
        "latest_id": latest.id,
        "result": latest.result,
        "trust_level": latest.trust_level,
        "stale": bool(reasons),
        "reasons": reasons,
        "reason_details": details,
        "freshness_class": freshness_class_for(details),
        "requires_fresh_verification": any(bool(item.get("requires_fresh_verification")) for item in details),
    }
