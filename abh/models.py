from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

PLAN_STATUSES = ("draft", "ready", "running", "blocked", "closing", "closed")
VERIFICATION_RESULTS = ("pass", "fail", "partial")
VERIFICATION_TRUST_LEVELS = ("unknown", "manual_record", "local_shell", "isolated_shell", "ci")
AUDIT_RESULTS = ("pass", "fail", "partial", "need_info")
MEMORY_TYPES = ("false_assumption", "rejected_path", "divergent_pattern", "overturned_completion")
MEMORY_STATUSES = ("active", "resolved", "superseded", "dismissed")
DRIFT_TYPES = ("boundary_drift", "dependency_drift", "test_drift", "terminology_drift")
SCHEMA_VERSION = "1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class AttractorRecord:
    id: str
    title: str
    version: str
    path: str
    intent: str
    status: str = "active"
    owner: str = "architecture"
    supersedes: str = "none"
    reason: str = ""
    impact: str = ""
    migration_strategy: str = ""
    invariants: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    doc_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "id": self.id,
            "title": self.title,
            "version": self.version,
            "status": self.status,
            "path": self.path,
            "owner": self.owner,
            "supersedes": self.supersedes,
            "reason": self.reason,
            "impact": self.impact,
            "migration_strategy": self.migration_strategy,
            "intent": self.intent,
            "invariants": list(self.invariants),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "doc_path": self.doc_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttractorRecord":
        return cls(
            id=data["id"],
            title=data["title"],
            version=data["version"],
            path=data["path"],
            intent=data["intent"],
            status=data.get("status", "active"),
            owner=data.get("owner", "architecture"),
            supersedes=data.get("supersedes", "none"),
            reason=data.get("reason", ""),
            impact=data.get("impact", ""),
            migration_strategy=data.get("migration_strategy", ""),
            invariants=list(data.get("invariants", [])),
            created_at=data.get("created_at", utc_now()),
            updated_at=data.get("updated_at", utc_now()),
            doc_path=data.get("doc_path", ""),
        )


@dataclass(slots=True)
class VerificationRun:
    id: str
    plan_id: str
    command: str
    result: str
    artifacts: list[str] = field(default_factory=list)
    failed_checks: list[str] = field(default_factory=list)
    failure_classifications: list[dict[str, Any]] = field(default_factory=list)
    environment: dict[str, Any] = field(default_factory=dict)
    trust_level: str = "unknown"
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "id": self.id,
            "plan_id": self.plan_id,
            "command": self.command,
            "result": self.result,
            "artifacts": list(self.artifacts),
            "failed_checks": list(self.failed_checks),
            "failure_classifications": [dict(item) for item in self.failure_classifications],
            "environment": dict(self.environment),
            "trust_level": self.trust_level,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerificationRun":
        return cls(
            id=data["id"],
            plan_id=data["plan_id"],
            command=data["command"],
            result=data["result"],
            artifacts=list(data.get("artifacts", [])),
            failed_checks=list(data.get("failed_checks", [])),
            failure_classifications=[dict(item) for item in data.get("failure_classifications", [])],
            environment=dict(data.get("environment", {})),
            trust_level=data.get("trust_level", "unknown"),
            created_at=data.get("created_at", utc_now()),
        )


@dataclass(slots=True)
class AuditFinding:
    severity: str
    finding: str
    evidence: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "finding": self.finding,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditFinding":
        return cls(
            severity=data["severity"],
            finding=data["finding"],
            evidence=data["evidence"],
            recommendation=data["recommendation"],
        )


@dataclass(slots=True)
class AuditRecord:
    id: str
    plan_id: str
    auditor: str
    scope: str
    auditor_context: str = ""
    independence: str = "unknown"
    verification_id: str = ""
    status: str = "requested"
    result: str = "need_info"
    rationale: str = ""
    evidence: list[str] = field(default_factory=list)
    findings: list[AuditFinding] = field(default_factory=list)
    follow_ups: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    doc_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "id": self.id,
            "plan_id": self.plan_id,
            "auditor": self.auditor,
            "scope": self.scope,
            "auditor_context": self.auditor_context,
            "independence": self.independence,
            "verification_id": self.verification_id,
            "status": self.status,
            "result": self.result,
            "rationale": self.rationale,
            "evidence": list(self.evidence),
            "findings": [finding.to_dict() for finding in self.findings],
            "follow_ups": list(self.follow_ups),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "doc_path": self.doc_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditRecord":
        return cls(
            id=data["id"],
            plan_id=data["plan_id"],
            auditor=data["auditor"],
            scope=data["scope"],
            auditor_context=data.get("auditor_context", ""),
            independence=data.get("independence", "unknown"),
            verification_id=data.get("verification_id", ""),
            status=data.get("status", "requested"),
            result=data.get("result", "need_info"),
            rationale=data.get("rationale", ""),
            evidence=list(data.get("evidence", [])),
            findings=[AuditFinding.from_dict(item) for item in data.get("findings", [])],
            follow_ups=list(data.get("follow_ups", [])),
            created_at=data.get("created_at", utc_now()),
            updated_at=data.get("updated_at", utc_now()),
            doc_path=data.get("doc_path", ""),
        )


@dataclass(slots=True)
class MemoryRecord:
    id: str
    memory_type: str
    summary: str
    context: str
    implication: str
    status: str = "active"
    related: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    related_plan_ids: list[str] = field(default_factory=list)
    related_audit_ids: list[str] = field(default_factory=list)
    related_drift_ids: list[str] = field(default_factory=list)
    superseded_by: str = ""
    deprecation_policy: str = "Mark deprecated when evidence no longer applies."
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    doc_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "id": self.id,
            "type": self.memory_type,
            "summary": self.summary,
            "context": self.context,
            "implication": self.implication,
            "status": self.status,
            "related": list(self.related),
            "evidence": list(self.evidence),
            "tags": list(self.tags),
            "related_plan_ids": list(self.related_plan_ids),
            "related_audit_ids": list(self.related_audit_ids),
            "related_drift_ids": list(self.related_drift_ids),
            "superseded_by": self.superseded_by,
            "deprecation_policy": self.deprecation_policy,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "doc_path": self.doc_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryRecord":
        return cls(
            id=data["id"],
            memory_type=data["type"],
            summary=data["summary"],
            context=data["context"],
            implication=data["implication"],
            status=data.get("status", "active"),
            related=list(data.get("related", [])),
            evidence=list(data.get("evidence", [])),
            tags=list(data.get("tags", [])),
            related_plan_ids=list(data.get("related_plan_ids", [])),
            related_audit_ids=list(data.get("related_audit_ids", [])),
            related_drift_ids=list(data.get("related_drift_ids", [])),
            superseded_by=data.get("superseded_by", ""),
            deprecation_policy=data.get("deprecation_policy", "Mark deprecated when evidence no longer applies."),
            created_at=data.get("created_at", utc_now()),
            updated_at=data.get("updated_at", utc_now()),
            doc_path=data.get("doc_path", ""),
        )


@dataclass(slots=True)
class DriftFinding:
    drift_type: str
    evidence: str
    recommendation: str
    severity: str = "unknown"
    confidence: str = "unknown"
    rule_id: str = ""
    matched_span: dict[str, Any] = field(default_factory=dict)
    source_excerpt: str = ""
    evidence_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.drift_type,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "severity": self.severity,
            "confidence": self.confidence,
            "rule_id": self.rule_id,
            "matched_span": dict(self.matched_span),
            "source_excerpt": self.source_excerpt,
            "evidence_path": self.evidence_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DriftFinding":
        return cls(
            drift_type=data["type"],
            evidence=data["evidence"],
            recommendation=data["recommendation"],
            severity=data.get("severity", "unknown"),
            confidence=data.get("confidence", "unknown"),
            rule_id=data.get("rule_id", ""),
            matched_span=dict(data.get("matched_span", {})),
            source_excerpt=data.get("source_excerpt", ""),
            evidence_path=data.get("evidence_path", ""),
        )


@dataclass(slots=True)
class DriftReport:
    id: str
    source: str
    findings: list[DriftFinding] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    follow_ups: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    doc_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "id": self.id,
            "source": self.source,
            "findings": [finding.to_dict() for finding in self.findings],
            "evidence": list(self.evidence),
            "follow_ups": list(self.follow_ups),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "doc_path": self.doc_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DriftReport":
        return cls(
            id=data["id"],
            source=data["source"],
            findings=[DriftFinding.from_dict(item) for item in data.get("findings", [])],
            evidence=list(data.get("evidence", [])),
            follow_ups=list(data.get("follow_ups", [])),
            created_at=data.get("created_at", utc_now()),
            updated_at=data.get("updated_at", utc_now()),
            doc_path=data.get("doc_path", ""),
        )


@dataclass(slots=True)
class PlanRecord:
    id: str
    title: str
    attractor: str
    baseline: str
    owner: str = "platform"
    status: str = "draft"
    goals: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    exit_criteria: list[str] = field(default_factory=list)
    validation_checklist: list[str] = field(default_factory=list)
    closure_evidence: list[str] = field(default_factory=list)
    verification_runs: list[str] = field(default_factory=list)
    audit_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    doc_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "id": self.id,
            "title": self.title,
            "attractor": self.attractor,
            "baseline": self.baseline,
            "owner": self.owner,
            "status": self.status,
            "goals": list(self.goals),
            "non_goals": list(self.non_goals),
            "exit_criteria": list(self.exit_criteria),
            "validation_checklist": list(self.validation_checklist),
            "closure_evidence": list(self.closure_evidence),
            "verification_runs": list(self.verification_runs),
            "audit_ids": list(self.audit_ids),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "doc_path": self.doc_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlanRecord":
        return cls(
            id=data["id"],
            title=data["title"],
            attractor=data["attractor"],
            baseline=data["baseline"],
            owner=data.get("owner", "platform"),
            status=data.get("status", "draft"),
            goals=list(data.get("goals", [])),
            non_goals=list(data.get("non_goals", [])),
            exit_criteria=list(data.get("exit_criteria", [])),
            validation_checklist=list(data.get("validation_checklist", [])),
            closure_evidence=list(data.get("closure_evidence", [])),
            verification_runs=list(data.get("verification_runs", [])),
            audit_ids=list(data.get("audit_ids", [])),
            created_at=data.get("created_at", utc_now()),
            updated_at=data.get("updated_at", utc_now()),
            doc_path=data.get("doc_path", ""),
        )


@dataclass(slots=True)
class RoadmapItem:
    key: str
    title: str
    stage: str
    summary: str = ""
    attractor: str = ""
    baseline: str = ""
    goals: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    exit_criteria: list[str] = field(default_factory=list)
    validation_checklist: list[str] = field(default_factory=list)
    closure_evidence: list[str] = field(default_factory=list)
    status: str = "queued"
    plan_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "key": self.key,
            "title": self.title,
            "stage": self.stage,
            "summary": self.summary,
            "attractor": self.attractor,
            "baseline": self.baseline,
            "goals": list(self.goals),
            "non_goals": list(self.non_goals),
            "exit_criteria": list(self.exit_criteria),
            "validation_checklist": list(self.validation_checklist),
            "closure_evidence": list(self.closure_evidence),
            "status": self.status,
            "plan_id": self.plan_id,
        }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RoadmapItem":
        return cls(
            key=data["key"],
            title=data["title"],
            stage=data.get("stage", ""),
            summary=data.get("summary", ""),
            attractor=data.get("attractor", ""),
            baseline=data.get("baseline", ""),
            goals=list(data.get("goals", [])),
            non_goals=list(data.get("non_goals", [])),
            exit_criteria=list(data.get("exit_criteria", [])),
            validation_checklist=list(data.get("validation_checklist", [])),
            closure_evidence=list(data.get("closure_evidence", [])),
            status=data.get("status", "queued"),
            plan_id=data.get("plan_id"),
        )


@dataclass(slots=True)
class RoadmapQueue:
    items: list[RoadmapItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, "items": [item.to_dict() for item in self.items]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RoadmapQueue":
        return cls(items=[RoadmapItem.from_dict(item) for item in data.get("items", [])])
