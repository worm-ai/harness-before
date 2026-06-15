from __future__ import annotations

from pathlib import Path

from .errors import AbhError, validate_identifier
from .models import AUDIT_RESULTS, AuditFinding, AuditRecord, utc_now
from .plans import load_plan, save_plan
from .storage import audit_doc_path, audit_json_path, audits_dir, ensure_workspace, read_json, write_json, write_json_markdown_pair


AUDIT_INDEPENDENCE_VALUES = {"unknown", "independent", "self_review"}


def parse_finding(value: str) -> AuditFinding:
    parts = value.split("|", 3)
    if len(parts) != 4 or not all(part.strip() for part in parts):
        raise AbhError("finding must use Severity|Finding|Evidence|Recommendation")
    return AuditFinding(
        severity=parts[0].strip(),
        finding=parts[1].strip(),
        evidence=parts[2].strip(),
        recommendation=parts[3].strip(),
    )


def load_audit(audit_id: str, cwd: Path | None = None) -> AuditRecord:
    validate_identifier(audit_id, "audit id")
    path = audit_json_path(audit_id, cwd)
    if not path.exists():
        raise AbhError(f"audit not found: {audit_id}")
    return AuditRecord.from_dict(read_json(path))


def list_audits(cwd: Path | None = None, *, limit: int | None = None, offset: int = 0, plan_id: str | None = None, status: str | None = None) -> list[AuditRecord]:
    directory = audits_dir(cwd)
    if not directory.exists():
        return []
    audits: list[AuditRecord] = []
    for path in sorted(directory.glob("*.json")):
        audits.append(AuditRecord.from_dict(read_json(path)))
    if plan_id:
        audits = [a for a in audits if a.plan_id == plan_id]
    if status:
        audits = [a for a in audits if a.status == status]
    if offset:
        audits = audits[offset:]
    if limit is not None:
        audits = audits[:limit]
    return audits


def save_audit(audit: AuditRecord, cwd: Path | None = None, write_doc: bool = True) -> AuditRecord:
    ensure_workspace(cwd)
    audit.updated_at = utc_now()
    if write_doc:
        doc_path = audit.doc_path or str(audit_doc_path(audit.id, cwd))
        audit.doc_path = doc_path
        doc_file = Path(doc_path)
        write_json_markdown_pair(audit_json_path(audit.id, cwd), audit.to_dict(), doc_file, render_audit_markdown(audit))
    else:
        write_json(audit_json_path(audit.id, cwd), audit.to_dict())
    return audit


def request_audit(
    *,
    audit_id: str,
    plan_id: str,
    auditor: str,
    scope: str,
    evidence: list[str] | None = None,
    cwd: Path | None = None,
) -> AuditRecord:
    ensure_workspace(cwd)
    validate_identifier(audit_id, "audit id")
    plan = load_plan(plan_id, cwd)
    if audit_json_path(audit_id, cwd).exists():
        raise AbhError(f"audit already exists: {audit_id}")
    reviewed = list(evidence or [])
    if not reviewed:
        raise AbhError("audit request requires at least one evidence item")
    audit = AuditRecord(
        id=audit_id,
        plan_id=plan_id,
        auditor=auditor,
        scope=scope,
        evidence=reviewed,
        doc_path=str(audit_doc_path(audit_id, cwd)),
    )
    save_audit(audit, cwd)
    if audit_id not in plan.audit_ids:
        plan.audit_ids.append(audit_id)
        save_plan(plan, cwd)
    return audit


def record_audit(
    *,
    audit_id: str,
    result: str,
    rationale: str,
    auditor_context: str | None = None,
    independence: str | None = None,
    verification_id: str | None = None,
    findings: list[str] | None = None,
    follow_ups: list[str] | None = None,
    cwd: Path | None = None,
) -> AuditRecord:
    if result not in AUDIT_RESULTS:
        raise AbhError(f"invalid audit result: {result}")
    if independence is not None and independence not in AUDIT_INDEPENDENCE_VALUES:
        raise AbhError(f"invalid audit independence: {independence}")
    audit = load_audit(audit_id, cwd)
    audit.result = result
    audit.rationale = rationale
    if auditor_context is not None:
        audit.auditor_context = auditor_context
    if independence is not None:
        audit.independence = independence
    if verification_id is not None:
        audit.verification_id = verification_id
    audit.status = "complete"
    audit.findings = [parse_finding(value) for value in (findings or [])]
    audit.follow_ups = list(follow_ups or [])
    saved = save_audit(audit, cwd)
    if result in ("fail", "partial", "need_info"):
        _auto_memory_from_audit_rejection(saved, cwd)
    return saved


def _auto_memory_from_audit_rejection(audit: AuditRecord, cwd: Path | None = None) -> None:
    """Auto-create a divergent_pattern memory when an audit rejects a plan."""
    from .memory import add_memory
    import uuid

    memory_id = f"mem-audit-{audit.id}-{uuid.uuid4().hex[:8]}"
    try:
        plan = load_plan(audit.plan_id, cwd)
        summary = f"Audit {audit.id} rejected plan {audit.plan_id}: {audit.result}"
        context = (
            f"Plan: {plan.title} (attractor: {plan.attractor}). "
            f"Auditor: {audit.auditor}. "
            f"Independence: {audit.independence or 'unknown'}. "
            f"Rationale: {audit.rationale[:500]}"
        )
        implication = (
            f"Plan {audit.plan_id} was rejected by independent audit. "
            f"Review the audit findings and rationale before re-opening the plan. "
            f"Update the plan's goals, exit criteria, or scope to address the audit concerns."
        )
        add_memory(
            memory_id=memory_id,
            memory_type="divergent_pattern",
            summary=summary,
            context=context,
            implication=implication,
            evidence=[str(audit.doc_path or audit_json_path(audit.id, cwd))],
            related=[audit.id],
            tags=["auto-generated", "audit-rejection", audit.result],
            related_plan_ids=[audit.plan_id],
            related_audit_ids=[audit.id],
            cwd=cwd,
        )
    except Exception:
        pass  # best-effort; don't block audit recording on memory creation failure


def render_audit_markdown(audit: AuditRecord) -> str:
    def bullet_lines(values: list[str]) -> str:
        if not values:
            return "-"
        return "\n".join(f"- {value}" for value in values)

    if audit.findings:
        finding_lines = "\n".join(
            f"| {finding.severity} | {finding.finding} | {finding.evidence} | {finding.recommendation} |"
            for finding in audit.findings
        )
    else:
        finding_lines = "|  |  |  |  |"
    return (
        f"# Audit: {audit.plan_id}\n\n"
        "## Metadata\n\n"
        f"- Audit ID: {audit.id}\n"
        f"- Plan: {audit.plan_id}\n"
        f"- Auditor: {audit.auditor}\n"
        f"- Auditor Context: {audit.auditor_context or 'unknown'}\n"
        f"- Independence: {audit.independence}\n"
        f"- Verification ID: {audit.verification_id or 'none'}\n"
        f"- Status: {audit.status}\n"
        f"- Created: {audit.created_at}\n"
        f"- Updated: {audit.updated_at}\n\n"
        "## Scope\n\n"
        f"{audit.scope}\n\n"
        "## Evidence Reviewed\n\n"
        f"{bullet_lines(audit.evidence)}\n\n"
        "## Semantic Conservation\n\n"
        "- Check whether any in-scope commitments disappeared, weakened, or moved to non-authoritative artifacts.\n"
        "- Distinguish J-flow-only evidence from R-flow evidence that reduces uncertainty through proof, decision, or owner-doc alignment.\n"
        "- Cite repository evidence for any semantic conservation gap.\n\n"
        "## Findings\n\n"
        "| Severity | Finding | Evidence | Recommendation |\n"
        "| --- | --- | --- | --- |\n"
        f"{finding_lines}\n\n"
        "## Verdict\n\n"
        f"- Result: {audit.result}\n"
        f"- Rationale: {audit.rationale}\n\n"
        "## Follow-Ups\n\n"
        f"{bullet_lines(audit.follow_ups)}\n"
    )
