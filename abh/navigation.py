from __future__ import annotations

from pathlib import Path

from .agent_setup import agent_setup_bundle
from .audits import load_audit
from .attractors import active_attractor
from .core import doctor
from .hooks import hook_profile
from .plans import list_plans, verification_freshness_summary
from .reporting import project_health_report
from .roadmap import list_roadmap_items


OWNER_DOCS = (
    "docs/index.md",
    "docs/context/source-of-truth.md",
    "docs/context/project-context.md",
    "docs/context/conventions.md",
    "docs/context/codebase-map.md",
)


def _related_memories(plan, cwd: Path | None = None) -> list[str]:
    """Find memory records with keyword overlap in plan goals/non-goals."""
    from .memory import list_memories

    plan_keywords: set[str] = set()
    for text in plan.goals + plan.non_goals:
        for word in text.lower().split():
            if len(word) > 3:
                plan_keywords.add(word)

    if not plan_keywords:
        return []

    related: list[str] = []
    for mem in list_memories(cwd):
        if mem.status != "active":
            continue
        mem_text = (mem.summary + " " + mem.context).lower()
        hits = sum(1 for kw in plan_keywords if kw in mem_text)
        if hits >= 2:
            related.append(mem.id)
    return related


def inject_related_memories(plan, cwd: Path | None = None) -> tuple[list[dict[str, object]], list[str]]:
    """Build related_memories and warnings for a plan. Shared by CLI and MCP."""
    from .memory import load_memory as _load_mem

    related_memories: list[dict[str, object]] = []
    warnings: list[str] = []
    for mem_id in _related_memories(plan, cwd)[:5]:
        try:
            mem = _load_mem(mem_id, cwd)
            related_memories.append({"id": mem.id, "summary": mem.summary, "memory_type": mem.memory_type})
            warnings.append(f"Related memory {mem.id}: {mem.summary[:100]}")
        except Exception:
            pass
    return related_memories, warnings


def _health_pressure_recommendation(cwd: Path | None = None) -> dict[str, object] | None:
    """Generate a recommendation from the most actionable health report pressure signal."""
    report = project_health_report(cwd)
    pressure = report.get("semantic_pressure", [])
    if not pressure:
        return None

    active = [s for s in pressure if s.get("status") == "active"]
    if not active:
        return None

    metrics = report.get("metrics", {})
    open_plan_count = metrics.get("plans", {}).get("open", 0)

    # Group by type
    by_type: dict[str, list[dict]] = {}
    for s in active:
        by_type.setdefault(str(s["type"]), []).append(s)

    # Priority: stale_proof (open plans only) → orphaned_memory → j_flow_only → repeated_leakage
    type_order = ["stale_proof", "orphaned_memory", "j_flow_only_evidence", "post_close_metadata_churn", "repeated_leakage"]
    for sig_type in type_order:
        signals = by_type.get(sig_type, [])
        if not signals:
            continue

        if sig_type == "stale_proof":
            # Only recommend for non-closed plans
            if open_plan_count == 0:
                continue

        # Sort by severity
        signals.sort(key=lambda s: {"high": 3, "medium": 2, "low": 1, "info": 0}.get(str(s.get("severity")), 0), reverse=True)
        top = signals[0]

        if sig_type == "stale_proof":
            plan_ids = top.get("related_plan_ids", [])
            if plan_ids:
                return {
                    "next_action": "run_stale_verification",
                    "recommended_command": f"abh verify run {plan_ids[0]} --json",
                    "requires_confirmation": False,
                    "rationale": f"{len(signals)} open plan(s) have stale verification; run fresh verification before audit or close. Start with {plan_ids[0]}.",
                    "source": {"pressure_type": sig_type, "stale_count": len(signals), "plan_id": plan_ids[0]},
                    "alternatives": ["abh plan list --json", "abh report health --json"],
                }
        elif sig_type == "orphaned_memory":
            memory_ids = top.get("related_memory_ids", [])
            return {
                "next_action": "triage_orphaned_memories",
                "recommended_command": "abh memory list",
                "requires_confirmation": False,
                "rationale": f"{len(signals)} active memories are orphaned (no tags or typed relationships). Add tags, related plans, or dismiss irrelevant ones so future agents can reuse them.",
                "source": {"pressure_type": sig_type, "orphaned_count": len(signals), "memory_ids": memory_ids[:5]},
                "alternatives": ["abh memory search --json", "abh report health --json"],
            }
        elif sig_type == "j_flow_only_evidence":
            return {
                "next_action": "attach_drift_to_memory",
                "recommended_command": "abh report health --json",
                "requires_confirmation": False,
                "rationale": f"{len(signals)} drift report(s) have no linked memory. Review via health report, then use 'abh memory add' to attach findings to active memory.",
                "source": {"pressure_type": sig_type, "j_flow_count": len(signals)},
                "alternatives": ["abh memory list", "abh drift plan-check <plan_id> --json"],
            }
        elif sig_type == "repeated_leakage":
            return {
                "next_action": "review_repeated_drift",
                "recommended_command": "abh report health --json",
                "requires_confirmation": False,
                "rationale": f"Drift pattern '{top.get('summary','')}' appears repeatedly. Review before starting related roadmap work.",
                "source": {"pressure_type": sig_type, "repeated_count": len(signals)},
                "alternatives": ["abh drift plan-check <plan_id> --json", "abh memory add --type divergent_pattern"],
            }
    return None


def _audit_id_for_plan(plan_id: str) -> str:
    if plan_id.startswith("plan-"):
        return f"audit-{plan_id.removeprefix('plan-')}"
    return f"audit-{plan_id}"


def _audit_request_command(plan_id: str, verification_id: str) -> str:
    audit_id = _audit_id_for_plan(plan_id)
    return (
        f'abh audit request {plan_id} --id {audit_id} --auditor human-independent-review '
        f'--scope "Independent audit of {plan_id}" '
        f"--evidence docs/plans/{plan_id}.md --evidence .abh/verifications/{verification_id}.json"
    )


def _roadmap_memory_warnings(item, cwd: Path | None = None) -> list[dict[str, object]]:
    """Search memory for prior failure records related to a roadmap item key."""
    from .memory import list_memories

    keywords = item.key.replace("-", " ").replace(".", " ").replace("_", " ").split()
    warnings: list[dict[str, object]] = []
    seen: set[str] = set()

    for mem in list_memories(cwd):
        if mem.status != "active":
            continue
        mem_text = (mem.summary + " " + mem.context + " " + " ".join(mem.related_plan_ids)).lower()
        hits = sum(1 for kw in keywords if kw in mem_text)
        if hits >= 1 and mem.id not in seen:
            seen.add(mem.id)
            warnings.append({
                "memory_id": mem.id,
                "summary": mem.summary[:120],
                "memory_type": mem.memory_type,
            })
    return warnings[:3]


def recommend_next_action(*, cwd: Path | None = None) -> dict[str, object]:
    plans = list_plans(cwd)
    open_plans = [plan for plan in plans if plan.status != "closed"]
    open_plans.sort(key=lambda plan: plan.created_at)
    active_plans = [plan for plan in open_plans if plan.status != "blocked"]
    blocked_plans = [plan for plan in open_plans if plan.status == "blocked"]

    if active_plans:
        plan = active_plans[0]
        related_memories = _related_memories(plan, cwd)
        memory_hint = ""
        if related_memories:
            memory_hint = f" Related memories: {', '.join(related_memories[:3])}."
        if plan.status == "draft":
            return {
                "next_action": "complete_plan_definition",
                "recommended_command": f"abh plan status {plan.id} --json",
                "requires_confirmation": False,
                "rationale": f"open draft plan {plan.id} should be completed or transitioned before materializing new work.{memory_hint}",
                "source": {"plan_id": plan.id, "plan_status": plan.status},
                "alternatives": ["abh plan update <plan-id> --json", "abh plan transition <plan-id> --to ready"],
            }
        if plan.status in {"ready", "running"}:
            verification = verification_freshness_summary(plan, cwd)
            if verification["result"] == "pass" and not verification["stale"]:
                latest_verification = str(verification["latest_id"])
                if not plan.audit_ids:
                    return {
                        "next_action": "request_audit",
                        "recommended_command": _audit_request_command(plan.id, latest_verification),
                        "requires_confirmation": False,
                        "rationale": f"plan {plan.id} has fresh passing verification and needs independent audit evidence.{memory_hint}",
                        "source": {
                            "plan_id": plan.id,
                            "plan_status": plan.status,
                            "latest_verification": latest_verification,
                            "verification_trust_level": verification["trust_level"],
                        },
                        "alternatives": [f"abh plan status {plan.id} --json", f"abh verify run {plan.id} --json"],
                    }
                try:
                    audit = load_audit(plan.audit_ids[-1], cwd)
                    if audit.status == "complete" and audit.result == "pass":
                        return {
                            "next_action": "transition_closing",
                            "recommended_command": f"abh plan transition {plan.id} --to closing",
                            "requires_confirmation": False,
                            "rationale": f"plan {plan.id} has fresh passing verification and passing audit evidence",
                            "source": {
                                "plan_id": plan.id,
                                "plan_status": plan.status,
                                "latest_verification": latest_verification,
                                "latest_audit": audit.id,
                            },
                            "alternatives": [f"abh plan status {plan.id} --json", f"abh close {plan.id}"],
                        }
                    return {
                        "next_action": "record_audit",
                        "recommended_command": f"abh audit record {audit.id} --result pass --rationale <rationale>",
                        "requires_confirmation": False,
                        "rationale": f"plan {plan.id} has an audit request that needs an independent verdict",
                        "source": {
                            "plan_id": plan.id,
                            "plan_status": plan.status,
                            "latest_verification": latest_verification,
                            "latest_audit": audit.id,
                            "audit_status": audit.status,
                            "audit_result": audit.result,
                        },
                        "alternatives": [f"abh plan status {plan.id} --json", f"abh audit list --json"],
                    }
                except Exception:
                    return {
                        "next_action": "inspect_audit",
                        "recommended_command": f"abh plan status {plan.id} --json",
                        "requires_confirmation": False,
                        "rationale": f"plan {plan.id} references audit evidence that could not be loaded",
                        "source": {
                            "plan_id": plan.id,
                            "plan_status": plan.status,
                            "latest_verification": latest_verification,
                            "audit_ids": list(plan.audit_ids),
                        },
                        "alternatives": [f"abh audit list --json", f"abh verify run {plan.id} --json"],
                    }
            return {
                "next_action": "run_verification",
                "recommended_command": f"abh verify run {plan.id} --json",
                "requires_confirmation": False,
                "rationale": f"open {plan.status} plan {plan.id} should gather fresh local verification evidence",
                "source": {"plan_id": plan.id, "plan_status": plan.status},
                "alternatives": [f"abh plan status {plan.id} --json", "abh audit request <plan-id> --id <audit-id>"],
            }
        if plan.status == "closing":
            return {
                "next_action": "close_plan",
                "recommended_command": f"abh close {plan.id}",
                "requires_confirmation": False,
                "rationale": f"plan {plan.id} is already closing; close after confirming passing audit evidence",
                "source": {"plan_id": plan.id, "plan_status": plan.status},
                "alternatives": [f"abh plan status {plan.id} --json", "abh audit list --json"],
            }

    queued = [item for item in list_roadmap_items(cwd) if item.status == "queued" and item.plan_id is None]
    if queued:
        item = queued[0]
        source: dict[str, object] = {"roadmap_key": item.key, "stage": item.stage, "title": item.title}
        rationale = f"no open plans; next queued roadmap item is {item.key}"
        if blocked_plans:
            source["blocked_plan_ids"] = [plan.id for plan in blocked_plans]
            rationale = f"no active open plans; next queued roadmap item is {item.key}"
        result: dict[str, object] = {
            "next_action": "materialize_roadmap_item",
            "recommended_command": f"abh roadmap materialize {item.key} --json",
            "requires_confirmation": False,
            "rationale": rationale,
            "source": source,
            "alternatives": ["abh roadmap list --json", "abh roadmap next-id --json"],
        }
        mem_warnings = _roadmap_memory_warnings(item, cwd)
        if mem_warnings:
            result["warnings"] = mem_warnings
        return result

    if blocked_plans:
        plan = blocked_plans[0]
        return {
            "next_action": "inspect_blocked_plan",
            "recommended_command": f"abh plan status {plan.id} --json",
            "requires_confirmation": False,
            "rationale": f"blocked plan {plan.id} is deferred until explicitly resumed",
            "source": {"plan_id": plan.id, "plan_status": plan.status},
            "alternatives": [f"abh plan transition {plan.id} --to running", "abh roadmap list --json"],
        }

    health_rec = _health_pressure_recommendation(cwd)
    if health_rec:
        return health_rec

    return {
        "next_action": "inspect_status",
        "recommended_command": "abh plan list --json",
        "requires_confirmation": False,
        "rationale": "no open plans or queued roadmap items were found",
        "source": {},
        "alternatives": ["abh doctor --json", "abh roadmap list --json"],
    }


def _check(check_id: str, label: str, passed: bool, details: dict[str, object], action: str) -> dict[str, object]:
    return {
        "id": check_id,
        "label": label,
        "status": "pass" if passed else "fail",
        "ok": passed,
        "details": details,
        "recommended_action": "" if passed else action,
    }


def onboarding_check(*, cwd: Path | None = None) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    try:
        attractor = active_attractor(cwd)
        checks.append(
            _check(
                "active_attractor",
                "Active attractor is available",
                True,
                {"id": attractor.id, "path": attractor.path},
                "abh attractor active --json",
            )
        )
    except Exception as exc:
        checks.append(_check("active_attractor", "Active attractor is available", False, {"error": str(exc)}, "abh attractor active --json"))

    root = Path.cwd() if cwd is None else Path(cwd)
    missing_owner_docs = [path for path in OWNER_DOCS if not (root / path).exists()]
    checks.append(
        _check(
            "owner_docs",
            "AGE owner docs are present",
            not missing_owner_docs,
            {"required": list(OWNER_DOCS), "missing": missing_owner_docs},
            "abh init --write --confirm --json",
        )
    )

    try:
        setup = agent_setup_bundle("codex", cwd=cwd)
        checks.append(
            _check(
                "agent_setup_export",
                "Agent setup export is available",
                True,
                {"agent": setup["agent"], "commands": setup["commands"]},
                "abh agent setup codex --json",
            )
        )
    except Exception as exc:
        checks.append(_check("agent_setup_export", "Agent setup export is available", False, {"error": str(exc)}, "abh agent setup codex --json"))

    profile = hook_profile()
    checks.append(
        _check(
            "hook_guardrails",
            "Hook guardrail commands are available",
            bool(profile.get("commands")),
            {"profile": profile["name"], "commands": profile["commands"]},
            "abh hooks profile --json",
        )
    )

    doctor_issues = doctor(cwd)
    checks.append(
        _check(
            "doctor",
            "Doctor consistency check passes",
            not doctor_issues,
            {"issues": doctor_issues},
            "abh doctor",
        )
    )

    closed_plans = [plan.id for plan in list_plans(cwd) if plan.status == "closed" and plan.verification_runs and plan.audit_ids]
    checks.append(
        _check(
            "closed_loop_evidence",
            "At least one verified and audited plan is closed",
            bool(closed_plans),
            {"closed_plans": closed_plans[:5], "total": len(closed_plans)},
            "complete one plan through verify, audit, and close",
        )
    )

    recommended_actions = [str(check["recommended_action"]) for check in checks if not check["ok"]]
    return {"ready": not recommended_actions, "checks": checks, "recommended_actions": recommended_actions}


def unified_status(*, cwd: Path | None = None) -> dict[str, object]:
    """Aggregate next_action, health posture, open plans, doctor, roadmap into one dashboard."""
    from .core import doctor as run_doctor
    from .plans import list_plans as get_plans
    from .roadmap import list_roadmap_items as get_roadmap_items

    next_result = recommend_next_action(cwd=cwd)
    health = project_health_report(cwd)
    plans = get_plans(cwd)
    roadmap_items = get_roadmap_items(cwd)

    open_plans = [p for p in plans if p.status != "closed"]
    active_pressure = health.get("semantic_pressure", [])
    doctor_issues = run_doctor(cwd)
    queued = [item for item in roadmap_items if item.status == "queued"]

    return {
        "repo_state": "idle" if not open_plans else "active",
        "open_plans": len(open_plans),
        "next_action": next_result.get("next_action"),
        "next_recommended_command": next_result.get("recommended_command"),
        "next_rationale": next_result.get("rationale"),
        "next_warnings": next_result.get("warnings", []),
        "health_posture": health.get("posture"),
        "health_summary": health.get("summary"),
        "active_alerts": len(active_pressure),
        "historical_alerts": len(health.get("historical_pressure", [])),
        "doctor_issues": len(doctor_issues),
        "roadmap_queued": len(queued),
        "roadmap_materialized": len([item for item in roadmap_items if item.status == "materialized"]),
    }
