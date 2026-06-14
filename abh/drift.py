from __future__ import annotations

from pathlib import Path

from .errors import AbhError, validate_identifier
from .memory import add_memory
from .models import DRIFT_TYPES, DriftFinding, DriftReport, utc_now
from .plans import load_plan
from .storage import drift_doc_path, drift_json_path, drift_dir, ensure_workspace, read_json, write_json, write_json_markdown_pair


DRIFT_RULES: dict[str, dict[str, object]] = {
    "boundary_drift": {
        "keywords": ("boundary", "module boundary", "moved", "mixed", "plan manager", "audit logic", "边界", "混入"),
        "severity": "medium",
        "recommendation": "Create a follow-up to restore ownership boundaries or update the attractor if the boundary changed intentionally.",
    },
    "dependency_drift": {
        "keywords": ("database", "external", "service", "package", "dependency", "remote", "依赖", "数据库", "外部"),
        "severity": "high",
        "recommendation": "Review plan non-goals and dependency rules before accepting the new dependency.",
    },
    "test_drift": {
        "keywords": ("skip test", "skipped tests", "without tests", "no test", "测试跳过", "未测试"),
        "severity": "high",
        "recommendation": "Add or restore verification coverage before closing the plan.",
    },
    "terminology_drift": {
        "keywords": ("renamed", "terminology", "term", "prepared", "ready", "术语", "重命名"),
        "severity": "medium",
        "recommendation": "Align terminology with canonical docs or record an explicit migration.",
    },
}


def matched_span(text: str, lowered: str, keyword: str) -> dict[str, object]:
    start = lowered.find(keyword.lower())
    if start < 0:
        return {}
    end = start + len(keyword)
    return {"start": start, "end": end, "text": text[start:end]}


def excerpt_for_span(text: str, start: int, end: int, radius: int = 80) -> str:
    excerpt_start = max(0, start - radius)
    excerpt_end = min(len(text), end + radius)
    return " ".join(text[excerpt_start:excerpt_end].split())


def analyze_drift_text(text: str, evidence_path: str = "") -> list[DriftFinding]:
    lowered = text.lower()
    findings: list[DriftFinding] = []
    for drift_type, rule in DRIFT_RULES.items():
        matched = [keyword for keyword in rule["keywords"] if keyword.lower() in lowered]
        if matched:
            span = matched_span(text, lowered, str(matched[0]))
            findings.append(
                DriftFinding(
                    drift_type=drift_type,
                    evidence=f"matched keywords: {', '.join(matched)}",
                    recommendation=str(rule["recommendation"]),
                    severity=str(rule.get("severity", "medium")),
                    confidence="high",
                    rule_id=drift_type,
                    matched_span=span,
                    source_excerpt=excerpt_for_span(text, int(span.get("start", 0)), int(span.get("end", 0))) if span else "",
                    evidence_path=evidence_path,
                )
            )
    return findings


def save_drift_report(report: DriftReport, cwd: Path | None = None, write_doc: bool = True) -> DriftReport:
    ensure_workspace(cwd)
    report.updated_at = utc_now()
    if write_doc:
        doc_path = report.doc_path or str(drift_doc_path(report.id, cwd))
        report.doc_path = doc_path
        write_json_markdown_pair(drift_json_path(report.id, cwd), report.to_dict(), Path(doc_path), render_drift_markdown(report))
    else:
        write_json(drift_json_path(report.id, cwd), report.to_dict())
    return report


def list_drift_reports(cwd: Path | None = None) -> list[DriftReport]:
    directory = drift_dir(cwd)
    if not directory.exists():
        return []
    reports: list[DriftReport] = []
    for path in sorted(directory.glob("*.json")):
        reports.append(DriftReport.from_dict(read_json(path)))
    return reports


def analyze_drift(
    *,
    drift_id: str,
    source: str,
    evidence: list[str] | None = None,
    memory_id: str | None = None,
    plan_id: str | None = None,
    cwd: Path | None = None,
) -> DriftReport:
    validate_identifier(drift_id, "drift id")
    source_path = Path(source)
    if not source_path.exists():
        raise AbhError(f"drift source not found: {source}")
    source_text = source_path.read_text(encoding="utf-8")
    evidence_values = list(evidence or [source])
    primary_evidence = evidence_values[0] if evidence_values else source
    findings = analyze_drift_text(source_text, evidence_path=primary_evidence)
    if plan_id:
        plan = load_plan(plan_id, cwd)
        negation_prefixes = ("不", "不要", "无需", "禁止", "避免", "no ", "not ")
        lowered = source_text.lower()
        for non_goal in plan.non_goals:
            clean = non_goal.lower()
            for prefix in negation_prefixes:
                if clean.startswith(prefix):
                    clean = clean[len(prefix):]
                    break
            keywords = [clean] if len(clean) > 2 else []
            keywords += [w for w in clean.split() if len(w) > 2 and w not in keywords]
            if not keywords:
                continue
            matched = [kw for kw in keywords if kw in lowered]
            if matched:
                existing_types = {f.drift_type for f in findings}
                for dt in DRIFT_TYPES:
                    if dt not in existing_types:
                        findings.append(
                            DriftFinding(
                                drift_type=dt,
                                evidence=f"plan non-goal violation: '{non_goal}' matched keywords {matched}",
                                recommendation=f"Review plan '{plan_id}' non-goal: {non_goal}. Consider updating plan or source.",
                                severity="high",
                                confidence="high",
                                rule_id=f"plan_non_goal:{plan_id}",
                                matched_span=matched_span(source_text, lowered, matched[0]),
                                source_excerpt=excerpt_for_span(
                                    source_text,
                                    int(matched_span(source_text, lowered, matched[0]).get("start", 0)),
                                    int(matched_span(source_text, lowered, matched[0]).get("end", 0)),
                                ),
                                evidence_path=primary_evidence,
                            )
                        )
                        break
    follow_ups = [finding.recommendation for finding in findings]
    report = DriftReport(
        id=drift_id,
        source=source,
        findings=findings,
        evidence=evidence_values,
        follow_ups=follow_ups,
        doc_path=str(drift_doc_path(drift_id, cwd)),
    )
    save_drift_report(report, cwd)
    if memory_id:
        if not findings:
            raise AbhError("cannot write drift memory without drift findings")
        add_memory(
            memory_id=memory_id,
            memory_type="divergent_pattern",
            summary=f"Drift report {drift_id}: {', '.join(finding.drift_type for finding in findings)}",
            context=f"Drift source: {source}",
            implication="Use these drift patterns to route follow-up plans before closure.",
            evidence=[str(drift_doc_path(drift_id, cwd))],
            related=[drift_id],
            cwd=cwd,
        )
    return report


def render_drift_markdown(report: DriftReport) -> str:
    def bullet_lines(values: list[str]) -> str:
        if not values:
            return "- "
        return "\n".join(f"- {value}" for value in values)

    if report.findings:
        finding_lines = "\n".join(
            f"| {finding.drift_type} | {finding.severity} | {finding.confidence} | {finding.evidence} | {finding.source_excerpt} | {finding.recommendation} |"
            for finding in report.findings
        )
    else:
        finding_lines = "|  |  |  |  |  |  |"
    return (
        f"# Drift: {report.id}\n\n"
        "## Metadata\n\n"
        f"- ID: {report.id}\n"
        f"- Source: {report.source}\n"
        f"- Created: {report.created_at}\n"
        f"- Updated: {report.updated_at}\n\n"
        "## Evidence\n\n"
        f"{bullet_lines(report.evidence)}\n\n"
        "## Findings\n\n"
        "| Type | Severity | Confidence | Evidence | Excerpt | Recommendation |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        f"{finding_lines}\n\n"
        "## Follow-Ups\n\n"
        f"{bullet_lines(report.follow_ups)}\n"
    )
