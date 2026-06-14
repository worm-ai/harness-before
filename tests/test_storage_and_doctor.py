from __future__ import annotations

import json
import threading
from pathlib import Path
from unittest.mock import patch

from abh import storage
from abh.storage import write_json
from tests.support import WorkspaceCliTestCase


class StorageAndDoctorTests(WorkspaceCliTestCase):
    def test_doctor_passes_when_json_and_docs_are_in_sync(self) -> None:
        self.run_cli(
            "plan", "create",
            "--id", "plan-doctor-ok",
            "--title", "Doctor OK",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
        )

        code, out, err = self.run_cli("doctor")

        self.assertEqual(code, 0, err)
        self.assertIn("doctor: ok", out)

    def test_doctor_reports_missing_markdown_for_json_record(self) -> None:
        self.run_cli(
            "plan", "create",
            "--id", "plan-doctor-missing-doc",
            "--title", "Doctor Missing Doc",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
        )
        (self.root / "docs" / "plans" / "plan-doctor-missing-doc.md").unlink()

        code, out, err = self.run_cli("doctor")

        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        self.assertIn("missing markdown for plan plan-doctor-missing-doc", out)

    def test_doctor_reports_orphan_markdown_without_json(self) -> None:
        (self.root / "docs" / "plans").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "plans" / "plan-doctor-orphan.md").write_text("# Plan: Orphan\n", encoding="utf-8")

        code, out, err = self.run_cli("doctor")

        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        self.assertIn("orphan markdown for plan plan-doctor-orphan", out)

    def test_doctor_reports_missing_schema_version(self) -> None:
        self.run_cli(
            "plan", "create",
            "--id", "plan-doctor-schema",
            "--title", "Doctor Schema",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
        )
        plan_path = self.root / ".abh" / "plans" / "plan-doctor-schema.json"
        data = plan_path.read_text(encoding="utf-8")
        plan_path.write_text(data.replace('  "schema_version": "2",\n', ""), encoding="utf-8")

        code, out, err = self.run_cli("doctor")

        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        self.assertIn("missing schema_version for plan plan-doctor-schema", out)

    def test_doctor_reports_missing_required_record_fields(self) -> None:
        self.run_cli(
            "plan", "create",
            "--id", "plan-doctor-required",
            "--title", "Required Field",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
        )
        plan_path = self.root / ".abh" / "plans" / "plan-doctor-required.json"
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        data.pop("title")
        plan_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        code, out, err = self.run_cli("doctor")

        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        self.assertIn("missing required field for plan plan-doctor-required: title", out)

    def test_doctor_reports_unknown_record_fields(self) -> None:
        self.run_cli(
            "plan", "create",
            "--id", "plan-doctor-unknown",
            "--title", "Unknown Field",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
        )
        plan_path = self.root / ".abh" / "plans" / "plan-doctor-unknown.json"
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        data["surprise"] = "not in schema"
        plan_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        code, out, err = self.run_cli("doctor")

        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        self.assertIn("unknown field for plan plan-doctor-unknown: surprise", out)

    def test_doctor_reports_deprecated_record_fields(self) -> None:
        self.run_cli(
            "plan", "create",
            "--id", "plan-doctor-deprecated",
            "--title", "Deprecated Field",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
        )
        plan_path = self.root / ".abh" / "plans" / "plan-doctor-deprecated.json"
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        data["prepared_at"] = "2026-06-05T00:00:00+00:00"
        plan_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        code, out, err = self.run_cli("doctor")

        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        self.assertIn("deprecated field for plan plan-doctor-deprecated: prepared_at", out)
        self.assertNotIn("unknown field for plan plan-doctor-deprecated: prepared_at", out)

    def test_doctor_reports_invalid_schema_version(self) -> None:
        self.run_cli(
            "plan", "create",
            "--id", "plan-doctor-version",
            "--title", "Version Field",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
        )
        plan_path = self.root / ".abh" / "plans" / "plan-doctor-version.json"
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        data["schema_version"] = "999"
        plan_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        code, out, err = self.run_cli("doctor")

        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        self.assertIn("unsupported schema_version for plan plan-doctor-version: 999", out)

    def test_doctor_json_reports_consistency_issues(self) -> None:
        self.run_cli(
            "plan", "create",
            "--id", "plan-doctor-json",
            "--title", "Doctor JSON",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
        )
        (self.root / "docs" / "plans" / "plan-doctor-json.md").unlink()

        code, out, err = self.run_cli("doctor", "--json")

        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["command"], "doctor")
        self.assertEqual(payload["data"]["issues"], ["missing markdown for plan plan-doctor-json"])
        self.assertEqual(payload["errors"][0]["category"], "consistency")
        self.assertEqual(payload["errors"][0]["code"], "doctor_issues")

    def test_doctor_reports_roadmap_queue_preassigned_plan_ids(self) -> None:
        queue = self.root / ".abh" / "roadmap.json"
        queue.parent.mkdir(parents=True, exist_ok=True)
        queue.write_text(
            json.dumps(
                {
                    "schema_version": "2",
                    "items": [
                        {
                            "key": "stage4.preassigned",
                            "title": "Preassigned",
                            "stage": "stage4",
                            "planned_plan_id": "plan-123-preassigned",
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )

        code, out, err = self.run_cli("doctor")

        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        self.assertIn("roadmap item stage4.preassigned must not preassign plan id plan-123-preassigned", out)

    def test_doctor_reports_queued_roadmap_item_with_plan_id(self) -> None:
        queue = self.root / ".abh" / "roadmap.json"
        queue.parent.mkdir(parents=True, exist_ok=True)
        queue.write_text(
            json.dumps(
                {
                    "schema_version": "2",
                    "items": [
                        {
                            "key": "stage4.queued-with-plan",
                            "title": "Queued With Plan",
                            "stage": "stage4",
                            "status": "queued",
                            "plan_id": "plan-existing",
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )

        code, out, err = self.run_cli("doctor")

        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        self.assertIn("queued roadmap item stage4.queued-with-plan must have null plan_id", out)

    def test_doctor_reports_duplicate_plan_number_except_legacy_allowlist(self) -> None:
        for plan_id in ("plan-010-alpha", "plan-010-beta"):
            self.run_cli(
                "plan",
                "create",
                "--id",
                plan_id,
                "--title",
                plan_id,
                "--attractor",
                "docs/architecture/attractors/abh-core-attractor.md",
                "--baseline",
                "baseline",
            )

        code, out, err = self.run_cli("doctor")

        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        self.assertIn("duplicate plan sequence 010", out)

    def test_write_json_keeps_existing_file_when_atomic_replace_fails(self) -> None:
        path = self.root / ".abh" / "plans" / "plan-atomic.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"old": true}\n', encoding="utf-8")

        with patch("abh.storage.os.replace", side_effect=OSError("replace failed")):
            with self.assertRaises(OSError):
                write_json(path, {"new": True})

        self.assertEqual(path.read_text(encoding="utf-8"), '{"old": true}\n')
        self.assertEqual(list(path.parent.glob("*.tmp")), [])
        self.assertFalse(path.with_suffix(path.suffix + ".lock").exists())

    def test_storage_write_json_markdown_pair_writes_both_targets(self) -> None:
        json_path = self.root / ".abh" / "plans" / "plan-pair.json"
        doc_path = self.root / "docs" / "plans" / "plan-pair.md"

        storage.write_json_markdown_pair(json_path, {"schema_version": "2", "id": "plan-pair"}, doc_path, "# Plan\n")

        self.assertEqual(json.loads(json_path.read_text(encoding="utf-8"))["id"], "plan-pair")
        self.assertEqual(doc_path.read_text(encoding="utf-8"), "# Plan\n")

    def test_storage_write_json_markdown_pair_rolls_back_first_replace_on_second_replace_failure(self) -> None:
        json_path = self.root / ".abh" / "plans" / "plan-pair.json"
        doc_path = self.root / "docs" / "plans" / "plan-pair.md"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text('{"schema_version": "2", "id": "old"}\n', encoding="utf-8")
        doc_path.write_text("# Old\n", encoding="utf-8")
        real_replace = storage.os.replace
        calls: list[Path] = []

        def replace_then_fail(src: Path, dst: Path) -> None:
            calls.append(Path(dst))
            if Path(dst) == json_path:
                raise OSError("injected json replace failure")
            real_replace(src, dst)

        with patch.object(storage.os, "replace", side_effect=replace_then_fail):
            with self.assertRaises(OSError):
                storage.write_json_markdown_pair(
                    json_path,
                    {"schema_version": "2", "id": "new"},
                    doc_path,
                    "# New\n",
                )

        self.assertEqual(json_path.read_text(encoding="utf-8"), '{"schema_version": "2", "id": "old"}\n')
        self.assertEqual(doc_path.read_text(encoding="utf-8"), "# Old\n")
        self.assertIn(doc_path, calls)
        self.assertIn(json_path, calls)
        self.assertEqual(list(json_path.parent.glob("*.tmp")), [])
        self.assertEqual(list(doc_path.parent.glob("*.tmp")), [])
        self.assertFalse(json_path.with_suffix(json_path.suffix + ".lock").exists())
        self.assertFalse(doc_path.with_suffix(doc_path.suffix + ".lock").exists())

    def test_save_plan_markdown_uses_json_markdown_pair_writer(self) -> None:
        with patch("abh.plans.write_json_markdown_pair", wraps=storage.write_json_markdown_pair) as pair_writer:
            self.run_cli(
                "plan",
                "create",
                "--id",
                "plan-atomic-doc",
                "--title",
                "Atomic Doc",
                "--attractor",
                "docs/architecture/attractors/abh-core-attractor.md",
                "--baseline",
                "baseline",
            )

        written_pairs = [(call.args[0].resolve(), call.args[2].resolve()) for call in pair_writer.call_args_list]
        self.assertIn(
            (
                (self.root / ".abh" / "plans" / "plan-atomic-doc.json").resolve(),
                (self.root / "docs" / "plans" / "plan-atomic-doc.md").resolve(),
            ),
            written_pairs,
        )

    def test_save_audit_markdown_uses_json_markdown_pair_writer(self) -> None:
        self.create_ready_plan("plan-pair-audit", closure_evidence="docs/audits/audit-pair-writer.md")

        with patch("abh.audits.write_json_markdown_pair", wraps=storage.write_json_markdown_pair) as pair_writer:
            code, out, err = self.run_cli(
                "audit",
                "request",
                "plan-pair-audit",
                "--id",
                "audit-pair-writer",
                "--auditor",
                "reviewer",
                "--scope",
                "pair writer coverage",
                "--evidence",
                "tests/test_storage_and_doctor.py",
            )

        self.assertEqual(code, 0, err)
        written_pairs = [(call.args[0].resolve(), call.args[2].resolve()) for call in pair_writer.call_args_list]
        self.assertIn(
            (
                (self.root / ".abh" / "audits" / "audit-pair-writer.json").resolve(),
                (self.root / "docs" / "audits" / "audit-pair-writer.md").resolve(),
            ),
            written_pairs,
        )

    def test_save_memory_markdown_uses_json_markdown_pair_writer(self) -> None:
        with patch("abh.memory.write_json_markdown_pair", wraps=storage.write_json_markdown_pair) as pair_writer:
            code, out, err = self.run_cli(
                "memory",
                "add",
                "--id",
                "mem-pair-writer",
                "--type",
                "false_assumption",
                "--summary",
                "Pair writer memory",
                "--context",
                "Memory save should use pair writer.",
                "--evidence",
                "tests/test_storage_and_doctor.py",
                "--implication",
                "Audit evidence covers memory save path.",
            )

        self.assertEqual(code, 0, err)
        written_pairs = [(call.args[0].resolve(), call.args[2].resolve()) for call in pair_writer.call_args_list]
        self.assertIn(
            (
                (self.root / ".abh" / "memory" / "mem-pair-writer.json").resolve(),
                (self.root / "docs" / "memory" / "mem-pair-writer.md").resolve(),
            ),
            written_pairs,
        )

    def test_save_drift_markdown_uses_json_markdown_pair_writer(self) -> None:
        drift_source = self.root / "drift-pair-source.txt"
        drift_source.write_text("Added a remote database even though the plan forbids external services.", encoding="utf-8")

        with patch("abh.drift.write_json_markdown_pair", wraps=storage.write_json_markdown_pair) as pair_writer:
            code, out, err = self.run_cli(
                "drift",
                "analyze",
                "--id",
                "drift-pair-writer",
                "--source",
                str(drift_source),
                "--evidence",
                "drift-pair-source.txt",
            )

        self.assertEqual(code, 0, err)
        written_pairs = [(call.args[0].resolve(), call.args[2].resolve()) for call in pair_writer.call_args_list]
        self.assertIn(
            (
                (self.root / ".abh" / "drift" / "drift-pair-writer.json").resolve(),
                (self.root / "docs" / "drift" / "drift-pair-writer.md").resolve(),
            ),
            written_pairs,
        )

    def test_save_attractor_markdown_uses_json_markdown_pair_writer(self) -> None:
        with patch("abh.attractors.write_json_markdown_pair", wraps=storage.write_json_markdown_pair) as pair_writer:
            code, out, err = self.run_cli(
                "attractor",
                "create",
                "--id",
                "attractor-pair-writer",
                "--title",
                "Pair Writer Attractor",
                "--version",
                "0.1.0",
                "--path",
                "docs/architecture/attractors/pair-writer.md",
                "--owner",
                "architecture",
                "--intent",
                "Attractor save should use pair writer.",
                "--invariant",
                "Pair writer evidence covers attractor save path.",
            )

        self.assertEqual(code, 0, err)
        written_pairs = []
        for call in pair_writer.call_args_list:
            json_path = call.args[0]
            doc_path = call.args[2]
            resolved_doc_path = doc_path if doc_path.is_absolute() else self.root / doc_path
            written_pairs.append((json_path.resolve(), resolved_doc_path.resolve()))
        self.assertIn(
            (
                (self.root / ".abh" / "attractors" / "attractor-pair-writer.json").resolve(),
                (self.root / "docs" / "architecture" / "attractors" / "pair-writer.md").resolve(),
            ),
            written_pairs,
        )

    def test_write_json_serializes_concurrent_same_file_writes_and_cleans_locks(self) -> None:
        path = self.root / ".abh" / "plans" / "plan-concurrent.json"
        errors: list[BaseException] = []

        def writer(index: int) -> None:
            try:
                write_json(path, {"schema_version": "2", "index": index})
            except BaseException as exc:
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(index,)) for index in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "2")
        self.assertIn(payload["index"], range(8))
        self.assertEqual(list(path.parent.glob("*.tmp")), [])
        self.assertFalse(path.with_suffix(path.suffix + ".lock").exists())
