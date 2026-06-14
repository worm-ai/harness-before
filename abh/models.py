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
DRIFT_TYPES = ("boundary_drift", "dependency_drift", "test_drift", "terminology_drift", "import_boundary_drift")
SCHEMA_VERSION = "2"
CURRENT_VERSION = 2
RECORD_SCHEMAS: dict[str, dict[str, set[str]]] = {
    "plan": {
        "required": {"schema_version", "id", "title", "attractor", "baseline"},
        "optional": {
            "owner",
            "status",
            "goals",
            "non_goals",
            "exit_criteria",
            "validation_checklist",
            "closure_evidence",
            "commitment_phase_state",
            "verification_runs",
            "audit_ids",
            "created_at",
            "updated_at",
            "doc_path",
        },
        "deprecated": {"prepared_at"},
    },
    "audit": {
        "required": {"schema_version", "id", "plan_id", "auditor", "scope"},
        "optional": {
            "auditor_context",
            "independence",
            "verification_id",
            "status",
            "result",
            "rationale",
            "evidence",
            "findings",
            "follow_ups",
            "created_at",
            "updated_at",
            "doc_path",
        },
        "deprecated": set(),
    },
    "attractor": {
        "required": {"schema_version", "id", "title", "version", "path", "intent"},
        "optional": {
            "status",
            "owner",
            "supersedes",
            "reason",
            "impact",
            "migration_strategy",
            "invariants",
            "created_at",
            "updated_at",
            "doc_path",
        },
        "deprecated": set(),
    },
    "memory": {
        "required": {"schema_version", "id", "type", "summary", "context", "implication"},
        "optional": {
            "status",
            "related",
            "evidence",
            "tags",
            "related_plan_ids",
            "related_audit_ids",
            "related_drift_ids",
            "superseded_by",
            "deprecation_policy",
            "created_at",
            "updated_at",
            "doc_path",
        },
        "deprecated": set(),
    },
    "drift": {
        "required": {"schema_version", "id", "source"},
        "optional": {"findings", "evidence", "follow_ups", "created_at", "updated_at", "doc_path"},
        "deprecated": set(),
    },
}


def validate_record_schema(record_type: str, data: dict[str, Any]) -> list[dict[str, str]]:
    schema = RECORD_SCHEMAS.get(record_type)
    if schema is None:
        return []
    required = schema["required"]
    deprecated = schema["deprecated"]
    allowed = required | schema["optional"] | deprecated
    issues: list[dict[str, str]] = []
    if "schema_version" not in data:
        issues.append({"category": "missing_schema_version", "field": "schema_version", "value": ""})
    elif str(data["schema_version"]) != SCHEMA_VERSION:
        version = int(str(data["schema_version"]))
        if version < CURRENT_VERSION:
            issues.append({"category": "legacy_schema_version", "field": "schema_version", "value": str(data["schema_version"])})
        else:
            issues.append({"category": "unsupported_schema_version", "field": "schema_version", "value": str(data["schema_version"])})
    for field_name in sorted(required - set(data)):
        if field_name == "schema_version":
            continue
        issues.append({"category": "missing_required_field", "field": field_name, "value": ""})
    for field_name in sorted(set(data) & deprecated):
        issues.append({"category": "deprecated_field", "field": field_name, "value": ""})
    for field_name in sorted(set(data) - allowed):
        issues.append({"category": "unknown_field", "field": field_name, "value": ""})
    return issues


def schema_issue_messages(record_type: str, record_id: str, data: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    for issue in validate_record_schema(record_type, data):
        category = issue["category"]
        field = issue["field"]
        if category == "missing_schema_version":
            messages.append(f"missing schema_version for {record_type} {record_id}")
        elif category == "legacy_schema_version":
            messages.append(f"legacy schema_version for {record_type} {record_id}: {issue['value']} (use 'abh doctor --fix' to migrate)")
        elif category == "unsupported_schema_version":
            messages.append(f"unsupported schema_version for {record_type} {record_id}: {issue['value']}")
        elif category == "missing_required_field":
            messages.append(f"missing required field for {record_type} {record_id}: {field}")
        elif category == "deprecated_field":
            messages.append(f"deprecated field for {record_type} {record_id}: {field}")
        elif category == "unknown_field":
            messages.append(f"unknown field for {record_type} {record_id}: {field}")
    return messages


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
        data = migrate_record("attractor", data)
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
        data = migrate_record("verification", data)
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
        data = migrate_record("audit", data)
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
        data = migrate_record("memory", data)
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
        data = migrate_record("drift", data)
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
class CommitmentResidualPressure:
    pressure: str
    non_blocking_rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "pressure": self.pressure,
            "non_blocking_rationale": self.non_blocking_rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CommitmentResidualPressure":
        return cls(
            pressure=data.get("pressure", ""),
            non_blocking_rationale=data.get("non_blocking_rationale", ""),
        )


@dataclass(slots=True)
class CommitmentPhaseState:
    stable_state_now: list[str] = field(default_factory=list)
    active_change_pressure: list[str] = field(default_factory=list)
    target_stable_state: list[str] = field(default_factory=list)
    conversion_proof: list[str] = field(default_factory=list)
    residual_pressure: list[CommitmentResidualPressure] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stable_state_now": list(self.stable_state_now),
            "active_change_pressure": list(self.active_change_pressure),
            "target_stable_state": list(self.target_stable_state),
            "conversion_proof": list(self.conversion_proof),
            "residual_pressure": [item.to_dict() for item in self.residual_pressure],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "CommitmentPhaseState":
        if not isinstance(data, dict):
            return cls()
        return cls(
            stable_state_now=list(data.get("stable_state_now", [])),
            active_change_pressure=list(data.get("active_change_pressure", [])),
            target_stable_state=list(data.get("target_stable_state", [])),
            conversion_proof=list(data.get("conversion_proof", [])),
            residual_pressure=[
                CommitmentResidualPressure.from_dict(item)
                for item in data.get("residual_pressure", [])
                if isinstance(item, dict)
            ],
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
    commitment_phase_state: CommitmentPhaseState = field(default_factory=CommitmentPhaseState)
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
            "commitment_phase_state": self.commitment_phase_state.to_dict(),
            "verification_runs": list(self.verification_runs),
            "audit_ids": list(self.audit_ids),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "doc_path": self.doc_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlanRecord":
        data = migrate_record("plan", data)
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
            commitment_phase_state=CommitmentPhaseState.from_dict(data.get("commitment_phase_state")),
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


# ---------------------------------------------------------------------------
# Schema migration infrastructure
# ---------------------------------------------------------------------------

def migrate_v1_to_v2(record_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """Migrate a v1 record to v2.

    v1 to v2 changes:
    - Sets schema_version to "2"
    - Ensures all optional fields exist with their default values
    - Normalizes deprecated fields

    This function is idempotent: applying it to an already-v2 record
    is a no-op.
    """
    if str(data.get("schema_version", "1")) == "2":
        return data
    migrated = dict(data)
    migrated["schema_version"] = SCHEMA_VERSION

    # Apply record-type-specific defaults for fields introduced between v1 and v2.
    if record_type == "plan":
        migrated.setdefault("commitment_phase_state", {
            "stable_state_now": [],
            "active_change_pressure": [],
            "target_stable_state": [],
            "conversion_proof": [],
            "residual_pressure": [],
        })
    elif record_type == "verification":
        migrated.setdefault("failed_checks", [])
        migrated.setdefault("failure_classifications", [])
        migrated.setdefault("environment", {})
        if not migrated.get("trust_level"):
            migrated["trust_level"] = "unknown"

    return migrated


def migrate_record(record_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """Run all applicable migrations on a record dict.

    Checks the schema_version field and applies each migration step
    sequentially until the record reaches CURRENT_VERSION.
    Gracefully handles missing, null, or malformed schema_version.
    """
    raw = data.get("schema_version")
    if raw is None or raw is False or (isinstance(raw, str) and raw == ""):
        return migrate_v1_to_v2(record_type, data)
    try:
        version = int(raw)
    except (ValueError, TypeError):
        return migrate_v1_to_v2(record_type, data)
    if version < CURRENT_VERSION:
        if version < 2:
            data = migrate_v1_to_v2(record_type, data)
    return data
