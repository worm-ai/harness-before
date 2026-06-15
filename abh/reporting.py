from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import SCHEMA_VERSION
from .audits import list_audits
from .core import doctor
from .drift import list_drift_reports
from .memory import list_memories
from .plans import list_plans, verification_freshness_summary
from .roadmap import list_roadmap_items
from .verifications import load_verification

SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def empty_metrics() -> dict[str, Any]:
    return {
        "plans": {
            "total": 0,
            "open": 0,
            "closed": 0,
            "close_rate": 0.0,
            "stale_latest_verifications": 0,
        },
        "verification": {
            "latest_pass": 0,
            "latest_fail_or_partial": 0,
            "stale_latest": 0,
            "failure_classifications": {},
        },
        "audit": {
            "total": 0,
            "pass": 0,
            "fail": 0,
            "partial": 0,
            "need_info": 0,
            "independent_pass": 0,
        },
        "drift": {
            "reports": 0,
            "findings": 0,
            "by_type": {},
            "high_or_critical": 0,
        },
        "memory": {
            "total": 0,
            "active": 0,
            "orphaned_active": 0,
            "superseded": 0,
        },
        "doctor": {
            "issues": 0,
        },
        "roadmap": {
            "queued": 0,
            "materialized": 0,
        },
    }


def project_health_report(cwd: Path | None = None) -> dict[str, Any]:
    metrics = empty_metrics()
    pressure: list[dict[str, Any]] = []

    plans = list_plans(cwd)
    metrics["plans"]["total"] = len(plans)
    metrics["plans"]["closed"] = len([plan for plan in plans if plan.status == "closed"])
    metrics["plans"]["open"] = metrics["plans"]["total"] - metrics["plans"]["closed"]
    if metrics["plans"]["total"]:
        metrics["plans"]["close_rate"] = metrics["plans"]["closed"] / metrics["plans"]["total"]

    for plan in plans:
        summary = verification_freshness_summary(plan, cwd)
        latest_id = summary.get("latest_id")
        if latest_id:
            if summary.get("result") == "pass":
                metrics["verification"]["latest_pass"] += 1
            else:
                metrics["verification"]["latest_fail_or_partial"] += 1
        if summary.get("stale"):
            metrics["plans"]["stale_latest_verifications"] += 1
            metrics["verification"]["stale_latest"] += 1
            evidence_refs = [plan.id]
            if latest_id:
                evidence_refs.append(str(latest_id))
            if summary.get("freshness_class") == "governance_metadata_churn":
                pressure.append(
                    pressure_signal(
                        signal_id=f"pressure-post-close-metadata-{plan.id}",
                        signal_type="post_close_metadata_churn",
                        severity="low",
                        confidence="high",
                        summary=f"{plan.id} latest verification is stale only because closed-plan governance metadata changed.",
                        evidence_refs=evidence_refs,
                        related_plan_ids=[plan.id],
                        recommendation="Review post-close documentation sync and record a follow-up if product proof changed.",
                    )
                )
            else:
                # Closed plans with stale verification are expected (git moves forward);
                # only open plans with stale proofs represent real risk.
                severity = "info" if plan.status == "closed" else "high"
                pressure.append(
                    pressure_signal(
                        signal_id=f"pressure-stale-proof-{plan.id}",
                        signal_type="stale_proof",
                        severity=severity,
                        confidence="high",
                        summary=f"{plan.id} latest verification is stale.",
                        evidence_refs=evidence_refs,
                        related_plan_ids=[plan.id],
                        recommendation="Run fresh verification before audit or close.",
                    )
                )
        if latest_id:
            run = load_verification(str(latest_id), cwd)
            for item in run.failure_classifications:
                category = str(item.get("category", "unknown"))
                counts = metrics["verification"]["failure_classifications"]
                counts[category] = counts.get(category, 0) + 1

    audits = list_audits(cwd)
    metrics["audit"]["total"] = len(audits)
    for audit in audits:
        if audit.result in metrics["audit"]:
            metrics["audit"][audit.result] += 1
        if audit.result == "pass" and audit.independence == "independent":
            metrics["audit"]["independent_pass"] += 1

    drift_reports = list_drift_reports(cwd)
    metrics["drift"]["reports"] = len(drift_reports)
    drift_type_counts: dict[str, int] = {}
    for report in drift_reports:
        for finding in report.findings:
            metrics["drift"]["findings"] += 1
            drift_type_counts[finding.drift_type] = drift_type_counts.get(finding.drift_type, 0) + 1
            if finding.severity in {"high", "critical"}:
                metrics["drift"]["high_or_critical"] += 1
    metrics["drift"]["by_type"] = drift_type_counts
    drift_ids_with_memory = related_drift_ids_from_memory(cwd)
    for drift_type, count in sorted(drift_type_counts.items()):
        if count >= 2:
            related = [report.id for report in drift_reports if any(finding.drift_type == drift_type for finding in report.findings)]
            pressure.append(
                pressure_signal(
                    signal_id=f"pressure-repeated-leakage-{drift_type}",
                    signal_type="repeated_leakage",
                    severity="medium",
                    confidence="medium",
                    summary=f"Drift family {drift_type} appears {count} time(s).",
                    evidence_refs=related,
                    related_drift_ids=related,
                    recommendation="Review repeated drift family before starting related roadmap work.",
                )
            )
    for report in drift_reports:
        if report.findings and report.id not in drift_ids_with_memory:
            pressure.append(
                pressure_signal(
                    signal_id=f"pressure-j-flow-only-{report.id}",
                    signal_type="j_flow_only_evidence",
                    severity="medium",
                    confidence="medium",
                    summary=f"{report.id} routes drift evidence but has no typed reusable memory link.",
                    evidence_refs=[report.id],
                    related_drift_ids=[report.id],
                    recommendation="Attach the drift report to active memory or a follow-up plan when the finding should influence future work.",
                )
            )

    memories = list_memories(cwd)
    metrics["memory"]["total"] = len(memories)
    for memory in memories:
        if memory.status == "active":
            metrics["memory"]["active"] += 1
            if is_orphaned_active_memory(memory):
                metrics["memory"]["orphaned_active"] += 1
                pressure.append(
                    pressure_signal(
                        signal_id=f"pressure-orphaned-memory-{memory.id}",
                        signal_type="orphaned_memory",
                        severity="medium",
                        confidence="high",
                        summary=f"{memory.id} is active but has no tags or typed relationships.",
                        evidence_refs=[memory.id],
                        related_memory_ids=[memory.id],
                        recommendation="Add tags or related plan/audit/drift ids so future agents can reuse this memory.",
                    )
                )
        if memory.status == "superseded" or memory.superseded_by:
            metrics["memory"]["superseded"] += 1

    metrics["doctor"]["issues"] = len(doctor(cwd))
    roadmap_items = list_roadmap_items(cwd)
    metrics["roadmap"]["queued"] = len([item for item in roadmap_items if item.status == "queued"])
    metrics["roadmap"]["materialized"] = len([item for item in roadmap_items if item.status == "materialized"])

    top_risks = sorted_risks(pressure)[:5]
    posture = posture_for(pressure)
    summary = "No unresolved quality risks found." if not pressure else f"{len(pressure)} unresolved semantic pressure signal(s)."
    return {
        "schema_version": SCHEMA_VERSION,
        "posture": posture,
        "summary": summary,
        "metrics": metrics,
        "semantic_pressure": pressure,
        "top_risks": top_risks,
        "recommended_inspections": recommended_inspections(top_risks),
    }


def pressure_signal(
    *,
    signal_id: str,
    signal_type: str,
    severity: str,
    confidence: str,
    summary: str,
    evidence_refs: list[str],
    recommendation: str,
    related_plan_ids: list[str] | None = None,
    related_audit_ids: list[str] | None = None,
    related_memory_ids: list[str] | None = None,
    related_drift_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": signal_id,
        "kind": "health",
        "type": signal_type,
        "severity": severity,
        "confidence": confidence,
        "status": "active",
        "summary": summary,
        "evidence_refs": list(evidence_refs),
        "related_plan_ids": list(related_plan_ids or []),
        "related_audit_ids": list(related_audit_ids or []),
        "related_memory_ids": list(related_memory_ids or []),
        "related_drift_ids": list(related_drift_ids or []),
        "recommendation": recommendation,
    }


def sorted_risks(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(signals, key=lambda item: (-SEVERITY_RANK.get(str(item["severity"]), 0), str(item["id"])))


def posture_for(signals: list[dict[str, Any]]) -> str:
    actionable = [s for s in signals if s.get("severity") not in ("info",)]
    if any(item["severity"] == "critical" for item in actionable):
        return "blocked"
    if any(item["severity"] == "high" for item in actionable):
        return "at_risk"
    if actionable:
        return "watch"
    return "healthy"


def recommended_inspections(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    inspections: list[dict[str, Any]] = []
    for risk in risks:
        command = "abh plan status <plan-id> --json"
        if risk["type"] == "orphaned_memory":
            command = "abh memory search --status active --json"
        elif risk["type"] in {"repeated_leakage", "j_flow_only_evidence"}:
            command = "abh drift list --json"
        inspections.append({"risk_id": risk["id"], "reason": risk["summary"], "command": command})
    return inspections


def related_drift_ids_from_memory(cwd: Path | None = None) -> set[str]:
    related: set[str] = set()
    for memory in list_memories(cwd):
        related.update(memory.related_drift_ids)
        related.update(item for item in memory.related if item.startswith("drift-"))
    return related


def is_orphaned_active_memory(memory) -> bool:
    return not any((memory.tags, memory.related_plan_ids, memory.related_audit_ids, memory.related_drift_ids))
