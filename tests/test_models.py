from __future__ import annotations

from abh.models import AttractorRecord, AuditRecord, DriftReport, MemoryRecord, PlanRecord, VerificationRun
from abh.models import validate_record_schema
from tests.support import WorkspaceCliTestCase


class ModelTests(WorkspaceCliTestCase):
    def test_model_serialization_includes_schema_version(self) -> None:
        records = [
            VerificationRun(id="ver-schema", plan_id="plan-schema", command="cmd", result="pass"),
            AttractorRecord(
                id="attractor-schema",
                title="Attractor Schema",
                version="1.0.0",
                path="docs/architecture/attractors/schema.md",
                intent="schema",
            ),
            AuditRecord(id="audit-schema", plan_id="plan-schema", auditor="auditor", scope="scope"),
            MemoryRecord(
                id="mem-schema",
                memory_type="false_assumption",
                summary="summary",
                context="context",
                implication="implication",
            ),
            DriftReport(id="drift-schema", source="source.txt"),
            PlanRecord(id="plan-schema", title="Schema", attractor="attr", baseline="base"),
        ]

        for record in records:
            self.assertEqual(record.to_dict()["schema_version"], "2")

    def test_model_schema_validation_covers_core_record_families(self) -> None:
        records = {
            "plan": PlanRecord(id="plan-schema", title="Schema", attractor="attr", baseline="base").to_dict(),
            "audit": AuditRecord(id="audit-schema", plan_id="plan-schema", auditor="auditor", scope="scope").to_dict(),
            "attractor": AttractorRecord(
                id="attractor-schema",
                title="Attractor Schema",
                version="1.0.0",
                path="docs/architecture/attractors/schema.md",
                intent="schema",
            ).to_dict(),
            "memory": MemoryRecord(
                id="mem-schema",
                memory_type="false_assumption",
                summary="summary",
                context="context",
                implication="implication",
            ).to_dict(),
            "drift": DriftReport(id="drift-schema", source="source.txt").to_dict(),
        }

        for record_type, data in records.items():
            self.assertEqual(validate_record_schema(record_type, data), [])
            data["unexpected"] = "unknown"
            self.assertEqual(
                validate_record_schema(record_type, data),
                [{"category": "unknown_field", "field": "unexpected", "value": ""}],
            )

    def test_model_schema_validation_distinguishes_deprecated_fields(self) -> None:
        data = PlanRecord(id="plan-schema", title="Schema", attractor="attr", baseline="base").to_dict()
        data["prepared_at"] = "2026-06-05T00:00:00+00:00"

        self.assertEqual(
            validate_record_schema("plan", data),
            [{"category": "deprecated_field", "field": "prepared_at", "value": ""}],
        )

    def test_model_deserialization_allows_missing_schema_version(self) -> None:
        verification = VerificationRun.from_dict(
            {
                "id": "ver-legacy",
                "plan_id": "plan-legacy",
                "command": "cmd",
                "result": "pass",
            }
        )
        self.assertEqual(verification.environment, {})
        self.assertEqual(verification.trust_level, "unknown")
        self.assertEqual(verification.failure_classifications, [])

        attractor = AttractorRecord.from_dict(
            {
                "id": "attractor-legacy",
                "title": "Legacy Attractor",
                "version": "1.0.0",
                "path": "docs/architecture/attractors/legacy.md",
                "intent": "legacy",
            }
        )
        self.assertEqual(attractor.status, "active")
        self.assertEqual(attractor.supersedes, "none")
        self.assertEqual(attractor.invariants, [])

        plan = PlanRecord.from_dict(
            {
                "id": "plan-legacy",
                "title": "Legacy",
                "attractor": "attr",
                "baseline": "base",
            }
        )

        self.assertEqual(plan.id, "plan-legacy")
        self.assertEqual(plan.to_dict()["schema_version"], "2")
