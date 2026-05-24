from __future__ import annotations

import io
import json
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import TestCase
import os

from abh.cli import main
from abh.core import is_recursive_verify_command
from abh.models import AuditRecord, DriftReport, MemoryRecord, PlanRecord, VerificationRun
from abh.storage import drift_json_path, write_json


class Chdir:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.previous: Path | None = None

    def __enter__(self):
        self.previous = Path.cwd()
        os.chdir(self.path)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.previous is not None:
            os.chdir(self.previous)


class CliTests(TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs" / "architecture" / "attractors").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "architecture" / "attractors" / "abh-core-attractor.md").write_text("# Attractor\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with Chdir(self.root), redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_plan_create_status_transition_and_verify(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-100-demo",
            "--title",
            "Demo",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "initial baseline",
            "--status",
            "ready",
            "--goal",
            "ship skeleton",
            "--non-goal",
            "web ui",
            "--exit-criterion",
            "cli commands exist",
            "--validation",
            "unit tests pass",
            "--closure-evidence",
            "docs/plans/plan-100-demo.md",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("created plan plan-100-demo", out)
        self.assertTrue((self.root / ".abh" / "plans" / "plan-100-demo.json").exists())
        self.assertTrue((self.root / "docs" / "plans" / "plan-100-demo.md").exists())

        code, out, err = self.run_cli(
            "plan",
            "status",
            "plan-100-demo",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("plan-100-demo [ready]", out)

        code, out, err = self.run_cli(
            "verify",
            "record",
            "plan-100-demo",
            "--command",
            "python -m pytest",
            "--result",
            "pass",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("recorded verification", out)

        code, out, err = self.run_cli(
            "plan",
            "transition",
            "plan-100-demo",
            "--to",
            "running",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("transitioned plan-100-demo -> running", out)

    def test_plan_update_appends_fields_deduplicates_and_syncs_markdown(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-106-update",
            "--title",
            "Update Plan",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--goal",
            "initial goal",
            "--non-goal",
            "initial non-goal",
            "--exit-criterion",
            "initial exit",
            "--validation",
            "initial validation",
            "--closure-evidence",
            "initial evidence",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli(
            "plan",
            "update",
            "plan-106-update",
            "--goal",
            "new goal",
            "--goal",
            "new goal",
            "--non-goal",
            "new non-goal",
            "--exit-criterion",
            "new exit",
            "--validation",
            "python3 -m abh doctor",
            "--closure-evidence",
            "tests/test_cli.py",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("updated plan plan-106-update", out)

        code, out, err = self.run_cli("plan", "status", "plan-106-update", "--json")
        self.assertEqual(code, 0, err)
        plan = json.loads(out)["data"]["plan"]
        self.assertEqual(plan["goals"], ["initial goal", "new goal"])
        self.assertEqual(plan["non_goals"], ["initial non-goal", "new non-goal"])
        self.assertEqual(plan["exit_criteria"], ["initial exit", "new exit"])
        self.assertEqual(plan["validation_checklist"], ["initial validation", "python3 -m abh doctor"])
        self.assertEqual(plan["closure_evidence"], ["initial evidence", "tests/test_cli.py"])

        doc = (self.root / "docs" / "plans" / "plan-106-update.md").read_text(encoding="utf-8")
        self.assertIn("- new goal", doc)
        self.assertIn("- new non-goal", doc)
        self.assertIn("- new exit", doc)
        self.assertIn("- python3 -m abh doctor", doc)
        self.assertIn("- tests/test_cli.py", doc)

    def test_plan_update_json_returns_machine_readable_plan(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-107-update-json",
            "--title",
            "Update JSON",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--goal",
            "initial goal",
            "--non-goal",
            "initial non-goal",
            "--exit-criterion",
            "initial exit",
            "--validation",
            "initial validation",
            "--closure-evidence",
            "initial evidence",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli(
            "plan",
            "update",
            "plan-107-update-json",
            "--validation",
            "python3 -m unittest tests/test_cli.py -v",
            "--json",
        )
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "plan update")
        self.assertEqual(payload["data"]["plan"]["validation_checklist"][-1], "python3 -m unittest tests/test_cli.py -v")

    def test_plan_update_removes_validation_checklist_entry(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-108-remove-validation",
            "--title",
            "Remove Validation",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--goal",
            "repair validation checklist",
            "--non-goal",
            "general delete",
            "--exit-criterion",
            "unsafe validation removed",
            "--validation",
            "python3 -m abh doctor",
            "--validation",
            "python3 -m abh verify run plan-108-remove-validation",
            "--closure-evidence",
            "docs/plans/plan-108-remove-validation.md",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli(
            "plan",
            "update",
            "plan-108-remove-validation",
            "--remove-validation",
            "python3 -m abh verify run plan-108-remove-validation",
            "--json",
        )
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["data"]["plan"]["validation_checklist"], ["python3 -m abh doctor"])
        doc = (self.root / "docs" / "plans" / "plan-108-remove-validation.md").read_text(encoding="utf-8")
        self.assertIn("- python3 -m abh doctor", doc)
        self.assertNotIn("- python3 -m abh verify run plan-108-remove-validation", doc)

    def test_failed_verification_blocks_ready_plan(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-102-ready",
            "--title",
            "Ready Plan",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "ship loop",
            "--non-goal",
            "audit",
            "--exit-criterion",
            "validation recorded",
            "--validation",
            "unit tests pass",
            "--closure-evidence",
            "docs/plans/plan-102-ready.md",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli(
            "verify",
            "record",
            "plan-102-ready",
            "--command",
            "python -m pytest",
            "--result",
            "fail",
            "--failed-check",
            "unit tests",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("plan", "status", "plan-102-ready")
        self.assertEqual(code, 0, err)
        self.assertIn("plan-102-ready [blocked]", out)

    def test_verify_run_executes_validation_checklist_and_records_pass(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-103-runner-pass",
            "--title",
            "Runner Pass",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "execute validation commands",
            "--non-goal",
            "remote runner",
            "--exit-criterion",
            "verification run is recorded",
            "--validation",
            "python3 -c 'print(\"abh-runner-pass\")'",
            "--closure-evidence",
            "docs/plans/plan-103-runner-pass.md",
        )
        self.assertEqual(code, 0, err)
        code, out, err = self.run_cli("verify", "run", "plan-103-runner-pass")
        self.assertEqual(code, 0, err)
        self.assertIn("ran verification", out)
        self.assertIn("pass", out)

        code, out, err = self.run_cli("plan", "status", "plan-103-runner-pass", "--json")
        self.assertEqual(code, 0, err)
        plan = json.loads(out)["data"]["plan"]
        self.assertEqual(plan["status"], "ready")
        self.assertEqual(len(plan["verification_runs"]), 1)
        run_path = self.root / ".abh" / "verifications" / f"{plan['verification_runs'][0]}.json"
        run = json.loads(run_path.read_text(encoding="utf-8"))
        self.assertEqual(run["result"], "pass")
        self.assertEqual(run["failed_checks"], [])
        self.assertIn("python3 -c", run["command"])
        self.assertTrue(any("exit_code=0" in artifact for artifact in run["artifacts"]))

    def test_verify_run_records_failed_check_and_blocks_running_plan(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-104-runner-fail",
            "--title",
            "Runner Fail",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "block on failed validation",
            "--non-goal",
            "remote runner",
            "--exit-criterion",
            "failure is recorded",
            "--validation",
            "python3 -c 'import sys; sys.exit(7)'",
            "--closure-evidence",
            "docs/plans/plan-104-runner-fail.md",
        )
        self.assertEqual(code, 0, err)
        code, out, err = self.run_cli("plan", "transition", "plan-104-runner-fail", "--to", "running")
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("verify", "run", "plan-104-runner-fail")
        self.assertEqual(code, 1, err)
        self.assertIn("ran verification", out)
        self.assertIn("fail", out)

        code, out, err = self.run_cli("plan", "status", "plan-104-runner-fail", "--json")
        self.assertEqual(code, 0, err)
        plan = json.loads(out)["data"]["plan"]
        self.assertEqual(plan["status"], "blocked")
        self.assertEqual(len(plan["verification_runs"]), 1)
        run_path = self.root / ".abh" / "verifications" / f"{plan['verification_runs'][0]}.json"
        run = json.loads(run_path.read_text(encoding="utf-8"))
        self.assertEqual(run["result"], "fail")
        self.assertEqual(run["failed_checks"], ["python3 -c 'import sys; sys.exit(7)'"])
        self.assertTrue(any("exit_code=7" in artifact for artifact in run["artifacts"]))

    def test_verify_run_json_returns_machine_readable_result(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-105-runner-json",
            "--title",
            "Runner JSON",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "emit json verification result",
            "--non-goal",
            "mcp wrapper",
            "--exit-criterion",
            "json output is parseable",
            "--validation",
            "python3 -c 'print(\"abh-json\")'",
            "--closure-evidence",
            "docs/plans/plan-105-runner-json.md",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("verify", "run", "plan-105-runner-json", "--json")
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "verify run")
        self.assertEqual(payload["data"]["verification"]["result"], "pass")
        self.assertEqual(payload["data"]["verification"]["failed_checks"], [])

    def test_verify_run_detects_recursive_self_invocation_command(self) -> None:
        self.assertTrue(
            is_recursive_verify_command(
                "python3 -m abh verify run plan-recursive-guard --timeout 1",
                "plan-recursive-guard",
            )
        )
        self.assertTrue(
            is_recursive_verify_command(
                "python3 -m abh verify run --json plan-recursive-guard",
                "plan-recursive-guard",
            )
        )
        self.assertFalse(
            is_recursive_verify_command(
                "python3 -m abh verify run another-plan",
                "plan-recursive-guard",
            )
        )
        self.assertFalse(is_recursive_verify_command("python3 -m abh doctor", "plan-recursive-guard"))

    def test_invalid_ready_transition_is_rejected(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-101-draft",
            "--title",
            "Draft",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
        )
        self.assertEqual(code, 0, err)
        stderr = io.StringIO()
        stdout = io.StringIO()
        with Chdir(self.root), redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["plan", "transition", "plan-101-draft", "--to", "ready"])
        self.assertNotEqual(code, 0)
        self.assertIn("plan is not ready", stderr.getvalue())

    def create_ready_plan(self, plan_id: str = "plan-200-audit") -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            plan_id,
            "--title",
            "Audited Plan",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "ship audited close",
            "--non-goal",
            "remote service",
            "--exit-criterion",
            "audit passes",
            "--validation",
            "unit tests pass",
            "--closure-evidence",
            "docs/audits/audit-200-audit.md",
        )
        self.assertEqual(code, 0, err)

    def test_audit_record_allows_close_only_after_pass(self) -> None:
        self.create_ready_plan()
        code, out, err = self.run_cli("close", "plan-200-audit")
        self.assertEqual(code, 2)
        self.assertIn("passing audit", err)

        code, out, err = self.run_cli(
            "audit",
            "request",
            "plan-200-audit",
            "--id",
            "audit-200-audit",
            "--auditor",
            "independent reviewer",
            "--scope",
            "Sprint 3 close gate",
            "--evidence",
            "tests/test_cli.py",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("requested audit audit-200-audit", out)
        self.assertTrue((self.root / ".abh" / "audits" / "audit-200-audit.json").exists())
        self.assertTrue((self.root / "docs" / "audits" / "audit-200-audit.md").exists())

        code, out, err = self.run_cli(
            "audit",
            "record",
            "audit-200-audit",
            "--result",
            "partial",
            "--finding",
            "Medium|Missing evidence|docs/plans/plan-200-audit.md|Add evidence",
            "--rationale",
            "not enough evidence",
        )
        self.assertEqual(code, 0, err)
        code, out, err = self.run_cli("close", "plan-200-audit")
        self.assertEqual(code, 2)
        self.assertIn("passing audit", err)

        code, out, err = self.run_cli(
            "audit",
            "record",
            "audit-200-audit",
            "--result",
            "pass",
            "--rationale",
            "all exit criteria verified",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("close", "plan-200-audit")
        self.assertEqual(code, 0, err)
        self.assertIn("closed plan plan-200-audit", out)

        code, out, err = self.run_cli("plan", "status", "plan-200-audit")
        self.assertEqual(code, 0, err)
        self.assertIn("plan-200-audit [closed]", out)

    def test_memory_add_and_search_by_type_and_keyword(self) -> None:
        code, out, err = self.run_cli(
            "memory",
            "add",
            "--id",
            "mem-001",
            "--type",
            "overturned_completion",
            "--summary",
            "Audit overturned a premature close",
            "--context",
            "Close was attempted without evidence.",
            "--evidence",
            "docs/audits/audit-200-audit.md",
            "--related",
            "plan-200-audit",
            "--implication",
            "Require pass audit before close.",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("recorded memory mem-001", out)
        self.assertTrue((self.root / ".abh" / "memory" / "mem-001.json").exists())
        self.assertTrue((self.root / "docs" / "memory" / "mem-001.md").exists())

        code, out, err = self.run_cli(
            "memory",
            "search",
            "--type",
            "overturned_completion",
            "--query",
            "premature",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("mem-001 [overturned_completion]", out)
        self.assertIn("Audit overturned a premature close", out)

    def test_route_recommends_reading_order_for_close_question(self) -> None:
        code, out, err = self.run_cli(
            "route",
            "--question",
            "Can we close this plan after the implementation claims completion?",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("Route: completion_audit", out)
        self.assertIn("docs/plans/", out)
        self.assertIn("docs/audits/", out)
        self.assertIn("docs/memory/", out)

    def test_drift_analyze_detects_patterns_and_can_write_memory(self) -> None:
        drift_source = self.root / "drift-source.txt"
        drift_source.write_text(
            "\n".join(
                [
                    "Imported a remote database dependency even though the plan said no external database.",
                    "Moved audit logic into the plan manager boundary.",
                    "Skipped tests and renamed ready to prepared in documentation.",
                ]
            ),
            encoding="utf-8",
        )

        code, out, err = self.run_cli(
            "drift",
            "analyze",
            "--id",
            "drift-001",
            "--source",
            str(drift_source),
            "--evidence",
            "drift-source.txt",
            "--memory-id",
            "mem-drift-001",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("drift-001", out)
        self.assertIn("boundary_drift", out)
        self.assertIn("dependency_drift", out)
        self.assertIn("test_drift", out)
        self.assertIn("terminology_drift", out)
        self.assertTrue((self.root / ".abh" / "drift" / "drift-001.json").exists())
        self.assertTrue((self.root / "docs" / "drift" / "drift-001.md").exists())
        self.assertTrue((self.root / ".abh" / "memory" / "mem-drift-001.json").exists())

        code, out, err = self.run_cli(
            "memory",
            "search",
            "--type",
            "divergent_pattern",
            "--query",
            "dependency_drift",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("mem-drift-001 [divergent_pattern]", out)

    def test_plan_list_returns_all_plans(self) -> None:
        self.run_cli(
            "plan", "create",
            "--id", "plan-list-a",
            "--title", "Plan A for list test",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
        )
        self.run_cli(
            "plan", "create",
            "--id", "plan-list-b",
            "--title", "Plan B for list test",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
        )
        code, out, err = self.run_cli("plan", "list")
        self.assertEqual(code, 0, err)
        self.assertIn("plan-list-a  [draft]  Plan A for list test", out)
        self.assertIn("plan-list-b  [draft]  Plan B for list test", out)
        self.assertIn("total: 2 plan(s)", out)

    def test_plan_list_json_returns_machine_readable_envelope(self) -> None:
        self.run_cli(
            "plan", "create",
            "--id", "plan-json-a",
            "--title", "Plan JSON A",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
        )

        code, out, err = self.run_cli("plan", "list", "--json")

        self.assertEqual(code, 0, err)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertEqual(payload["schema_version"], "1")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "plan list")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["warnings"], [])
        self.assertEqual(payload["data"]["total"], 1)
        self.assertEqual(payload["data"]["plans"][0]["id"], "plan-json-a")
        self.assertEqual(payload["data"]["plans"][0]["status"], "draft")

    def test_abh_error_json_returns_structured_error(self) -> None:
        code, out, err = self.run_cli("plan", "status", "missing-plan", "--json")

        self.assertEqual(code, 2)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertEqual(payload["schema_version"], "1")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["command"], "plan status")
        self.assertEqual(payload["data"], {})
        self.assertEqual(payload["errors"][0]["code"], "abh_error")
        self.assertEqual(payload["errors"][0]["category"], "not_found")
        self.assertEqual(payload["errors"][0]["message"], "plan not found: missing-plan")

    def test_memory_list_returns_all_memories(self) -> None:
        self.run_cli(
            "memory", "add",
            "--id", "mem-list-a",
            "--type", "false_assumption",
            "--summary", "list test assumption",
            "--context", "testing memory list",
            "--implication", "list works",
            "--evidence", "tests/test_cli.py",
        )
        self.run_cli(
            "memory", "add",
            "--id", "mem-list-b",
            "--type", "rejected_path",
            "--summary", "another list test",
            "--context", "testing memory list again",
            "--implication", "list works twice",
            "--evidence", "tests/test_cli.py",
        )
        code, out, err = self.run_cli("memory", "list")
        self.assertEqual(code, 0, err)
        self.assertIn("mem-list-a  [false_assumption]  list test assumption", out)
        self.assertIn("mem-list-b  [rejected_path]  another list test", out)
        self.assertIn("total: 2 memory record(s)", out)

    def test_audit_list_returns_all_audits(self) -> None:
        self.create_ready_plan("plan-audit-list")
        self.run_cli(
            "audit", "request",
            "plan-audit-list",
            "--id", "audit-list-a",
            "--auditor", "reviewer",
            "--scope", "test audit list",
            "--evidence", "tests/test_cli.py",
        )
        self.run_cli(
            "audit", "request",
            "plan-audit-list",
            "--id", "audit-list-b",
            "--auditor", "reviewer",
            "--scope", "test audit list again",
            "--evidence", "tests/test_cli.py",
        )
        code, out, err = self.run_cli("audit", "list")
        self.assertEqual(code, 0, err)
        self.assertIn("audit-list-a  -> plan-audit-list", out)
        self.assertIn("audit-list-b  -> plan-audit-list", out)
        self.assertIn("total: 2 audit(s)", out)

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
        plan_path.write_text(data.replace('  "schema_version": "1",\n', ""), encoding="utf-8")

        code, out, err = self.run_cli("doctor")

        self.assertEqual(code, 1)
        self.assertEqual(err, "")
        self.assertIn("missing schema_version for plan plan-doctor-schema", out)

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

    def test_core_read_commands_support_json_output(self) -> None:
        self.create_ready_plan("plan-json-contract")
        self.run_cli(
            "audit", "request",
            "plan-json-contract",
            "--id", "audit-json-contract",
            "--auditor", "reviewer",
            "--scope", "json contract",
            "--evidence", "tests/test_cli.py",
        )
        self.run_cli(
            "memory", "add",
            "--id", "mem-json-contract",
            "--type", "false_assumption",
            "--summary", "json contract memory",
            "--context", "testing json",
            "--implication", "agents can parse memory",
            "--evidence", "tests/test_cli.py",
        )
        drift_source = self.root / "json-drift.txt"
        drift_source.write_text("Skipped tests and added external dependency.\n", encoding="utf-8")

        checks = [
            (("plan", "status", "plan-json-contract", "--json"), "plan"),
            (("audit", "list", "--json"), "audits"),
            (("memory", "list", "--json"), "memories"),
            (("memory", "search", "--query", "json", "--json"), "memories"),
            (("route", "--question", "Can we close this plan?", "--json"), "route"),
            (("drift", "analyze", "--id", "drift-json-contract", "--source", str(drift_source), "--json"), "drift_report"),
        ]

        for args, data_key in checks:
            with self.subTest(args=args):
                code, out, err = self.run_cli(*args)
                self.assertEqual(code, 0, err)
                self.assertEqual(err, "")
                payload = json.loads(out)
                self.assertTrue(payload["ok"])
                self.assertEqual(payload["errors"], [])
                self.assertIn(data_key, payload["data"])

    def test_model_serialization_includes_schema_version(self) -> None:
        records = [
            VerificationRun(id="ver-schema", plan_id="plan-schema", command="cmd", result="pass"),
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
            self.assertEqual(record.to_dict()["schema_version"], "1")

    def test_model_deserialization_allows_missing_schema_version(self) -> None:
        plan = PlanRecord.from_dict(
            {
                "id": "plan-legacy",
                "title": "Legacy",
                "attractor": "attr",
                "baseline": "base",
            }
        )

        self.assertEqual(plan.id, "plan-legacy")
        self.assertEqual(plan.to_dict()["schema_version"], "1")

    def test_route_injects_active_plans(self) -> None:
        self.run_cli(
            "plan", "create",
            "--id", "plan-route-active",
            "--title", "Active Plan",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
            "--status", "ready",
            "--goal", "test route injection",
            "--non-goal", "web ui",
            "--exit-criterion", "route test passes",
            "--validation", "unit tests pass",
            "--closure-evidence", "tests/test_cli.py",
        )
        self.run_cli(
            "verify", "record",
            "plan-route-active",
            "--command", "python -m pytest",
            "--result", "pass",
        )
        self.run_cli(
            "plan", "transition", "plan-route-active", "--to", "running",
        )
        code, out, err = self.run_cli("route", "--question", "Can we close this plan?")
        self.assertEqual(code, 0, err)
        self.assertIn("Route: completion_audit", out)
        self.assertIn("active plans", out.lower())
        self.assertIn("plan-route-active", out)

    def test_drift_with_plan_detects_non_goal_violation(self) -> None:
        drift_source = self.root / "drift-plan.txt"
        drift_source.write_text("重构存储层并引入外部服务\n", encoding="utf-8")
        self.run_cli(
            "plan", "create",
            "--id", "plan-drift-baseline",
            "--title", "Drift Baseline Plan",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
            "--status", "ready",
            "--goal", "cli commands",
            "--non-goal", "不重构存储层",
            "--exit-criterion", "drift test passes",
            "--validation", "unit tests pass",
            "--closure-evidence", "tests/test_cli.py",
        )
        code, out, err = self.run_cli(
            "drift", "analyze",
            "--id", "drift-plan-001",
            "--source", str(drift_source),
            "--plan", "plan-drift-baseline",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("boundary_drift", out)
        self.assertIn("plan non-goal violation", out)


class McpServerTests(TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs" / "architecture" / "attractors").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "architecture" / "attractors" / "abh-core-attractor.md").write_text("# Attractor\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with Chdir(self.root), redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def create_ready_plan(self, plan_id: str = "plan-mcp-contract") -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            plan_id,
            "--title",
            "MCP Contract Plan",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "expose readonly mcp",
            "--non-goal",
            "write tools",
            "--exit-criterion",
            "mcp tests pass",
            "--validation",
            "unit tests pass",
            "--closure-evidence",
            "tests/test_cli.py",
        )
        self.assertEqual(code, 0, err)

    def call_mcp(self, message: dict[str, object]) -> dict[str, object]:
        from abh.mcp_server import handle_message

        with Chdir(self.root):
            response = handle_message(message)
        self.assertIsNotNone(response)
        assert response is not None
        return response

    def test_mcp_initialize_and_tools_list_exposes_readonly_tools(self) -> None:
        init_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "0.0.1"},
                },
            }
        )

        self.assertEqual(init_response["jsonrpc"], "2.0")
        self.assertEqual(init_response["id"], 1)
        init_result = init_response["result"]
        self.assertEqual(init_result["protocolVersion"], "2025-11-25")
        self.assertEqual(init_result["capabilities"]["tools"]["listChanged"], False)
        self.assertEqual(init_result["serverInfo"]["name"], "abh")

        list_response = self.call_mcp({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = list_response["result"]["tools"]
        tool_names = {tool["name"] for tool in tools}
        self.assertIn("abh_plan_list", tool_names)
        self.assertIn("abh_plan_status", tool_names)
        self.assertIn("abh_close_plan", tool_names)
        for tool in tools:
            self.assertEqual(tool["inputSchema"]["type"], "object")
        readonly = {tool["name"]: tool["annotations"]["readOnlyHint"] for tool in tools}
        self.assertTrue(readonly["abh_plan_list"])
        self.assertTrue(readonly["abh_doctor"])
        self.assertFalse(readonly["abh_plan_create"])
        self.assertFalse(readonly["abh_verify_record"])
        self.assertFalse(readonly["abh_close_plan"])
        write_tool_names = {
            "abh_plan_create",
            "abh_plan_transition",
            "abh_verify_record",
            "abh_audit_request",
            "abh_audit_record",
            "abh_close_plan",
            "abh_memory_add",
            "abh_drift_analyze",
        }
        self.assertTrue(write_tool_names.issubset(tool_names))
        for tool in tools:
            if tool["name"] in write_tool_names:
                self.assertIn("confirm", tool["inputSchema"]["required"])

    def test_mcp_tools_call_returns_structured_content_for_core_reads(self) -> None:
        self.create_ready_plan()

        response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "abh_plan_status",
                    "arguments": {"plan_id": "plan-mcp-contract"},
                },
            }
        )

        result = response["result"]
        self.assertFalse(result["isError"])
        self.assertEqual(result["content"][0]["type"], "text")
        envelope = result["structuredContent"]
        self.assertTrue(envelope["ok"])
        self.assertEqual(envelope["command"], "abh_plan_status")
        self.assertEqual(envelope["data"]["plan"]["id"], "plan-mcp-contract")

        doctor_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "abh_doctor", "arguments": {}},
            }
        )
        doctor_envelope = doctor_response["result"]["structuredContent"]
        self.assertTrue(doctor_envelope["ok"])
        self.assertEqual(doctor_envelope["data"]["issues"], [])

        route_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "abh_route",
                    "arguments": {"question": "Can we close this plan?"},
                },
            }
        )
        route_envelope = route_response["result"]["structuredContent"]
        self.assertEqual(route_envelope["data"]["route"]["route"], "completion_audit")

    def test_mcp_drift_list_reads_existing_reports_without_writing(self) -> None:
        with Chdir(self.root):
            report = DriftReport(id="drift-mcp-existing", source="source.txt")
            write_json(drift_json_path(report.id), report.to_dict())

        response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {"name": "abh_drift_list", "arguments": {}},
            }
        )

        envelope = response["result"]["structuredContent"]
        self.assertTrue(envelope["ok"])
        self.assertEqual(envelope["data"]["total"], 1)
        self.assertEqual(envelope["data"]["drift_reports"][0]["id"], "drift-mcp-existing")

    def test_mcp_errors_are_structured(self) -> None:
        unknown_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {"name": "abh_missing_tool", "arguments": {}},
            }
        )
        self.assertEqual(unknown_response["error"]["code"], -32601)
        self.assertEqual(unknown_response["error"]["data"]["category"], "not_found")

        tool_error_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "abh_plan_status",
                    "arguments": {"plan_id": "missing-plan"},
                },
            }
        )
        result = tool_error_response["result"]
        self.assertTrue(result["isError"])
        envelope = result["structuredContent"]
        self.assertFalse(envelope["ok"])
        self.assertEqual(envelope["errors"][0]["category"], "not_found")

    def test_mcp_doctor_consistency_errors_include_issues(self) -> None:
        self.create_ready_plan("plan-mcp-doctor")
        (self.root / "docs" / "plans" / "plan-mcp-doctor.md").unlink()

        response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {"name": "abh_doctor", "arguments": {}},
            }
        )

        result = response["result"]
        self.assertTrue(result["isError"])
        envelope = result["structuredContent"]
        self.assertFalse(envelope["ok"])
        self.assertEqual(envelope["data"]["issues"], ["missing markdown for plan plan-mcp-doctor"])
        self.assertEqual(envelope["errors"][0]["code"], "doctor_issues")
        self.assertEqual(envelope["errors"][0]["category"], "consistency")

    def test_mcp_stdio_processes_newline_delimited_messages(self) -> None:
        from abh.mcp_server import serve_stdio

        input_stream = io.StringIO(
            "\n".join(
                [
                    json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}),
                    "not-json",
                    json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                ]
            )
        )
        output_stream = io.StringIO()

        with Chdir(self.root):
            exit_code = serve_stdio(input_stream=input_stream, output_stream=output_stream)

        self.assertEqual(exit_code, 0)
        lines = [json.loads(line) for line in output_stream.getvalue().splitlines()]
        self.assertEqual(lines[0]["id"], 1)
        self.assertIn("tools", lines[0]["result"])
        self.assertEqual(lines[1]["error"]["code"], -32700)

    def test_mcp_write_tools_require_confirm_and_do_not_write_without_it(self) -> None:
        response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "abh_plan_create",
                    "arguments": {
                        "plan_id": "plan-mcp-no-confirm",
                        "title": "No Confirm",
                        "attractor": "docs/architecture/attractors/abh-core-attractor.md",
                        "baseline": "baseline",
                    },
                },
            }
        )

        result = response["result"]
        self.assertTrue(result["isError"])
        envelope = result["structuredContent"]
        self.assertFalse(envelope["ok"])
        self.assertEqual(envelope["errors"][0]["category"], "business_rule")
        self.assertFalse((self.root / ".abh" / "plans" / "plan-mcp-no-confirm.json").exists())

    def test_mcp_controlled_write_flow_can_create_verify_audit_close_and_write_memory(self) -> None:
        create_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "abh_plan_create",
                    "arguments": {
                        "confirm": True,
                        "plan_id": "plan-mcp-write",
                        "title": "MCP Write Plan",
                        "attractor": "docs/architecture/attractors/abh-core-attractor.md",
                        "baseline": "baseline",
                        "status": "ready",
                        "goals": ["ship controlled writes"],
                        "non_goals": ["skip audit"],
                        "exit_criteria": ["closed through mcp"],
                        "validation_checklist": ["unit tests pass"],
                        "closure_evidence": ["tests/test_cli.py"],
                    },
                },
            }
        )
        plan = create_response["result"]["structuredContent"]["data"]["plan"]
        self.assertEqual(plan["id"], "plan-mcp-write")
        self.assertEqual(plan["status"], "ready")

        verify_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {
                    "name": "abh_verify_record",
                    "arguments": {
                        "confirm": True,
                        "plan_id": "plan-mcp-write",
                        "command": "python3 -m unittest tests/test_cli.py -v",
                        "result": "pass",
                        "artifacts": ["tests/test_cli.py"],
                    },
                },
            }
        )
        verification = verify_response["result"]["structuredContent"]["data"]["verification"]
        self.assertEqual(verification["plan_id"], "plan-mcp-write")

        transition_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {
                    "name": "abh_plan_transition",
                    "arguments": {"confirm": True, "plan_id": "plan-mcp-write", "to": "running"},
                },
            }
        )
        self.assertEqual(transition_response["result"]["structuredContent"]["data"]["plan"]["status"], "running")

        audit_request_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 14,
                "method": "tools/call",
                "params": {
                    "name": "abh_audit_request",
                    "arguments": {
                        "confirm": True,
                        "plan_id": "plan-mcp-write",
                        "audit_id": "audit-mcp-write",
                        "auditor": "independent-auditor",
                        "scope": "mcp write close gate",
                        "evidence": ["tests/test_cli.py"],
                    },
                },
            }
        )
        self.assertEqual(audit_request_response["result"]["structuredContent"]["data"]["audit"]["id"], "audit-mcp-write")

        audit_record_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 15,
                "method": "tools/call",
                "params": {
                    "name": "abh_audit_record",
                    "arguments": {
                        "confirm": True,
                        "audit_id": "audit-mcp-write",
                        "result": "pass",
                        "rationale": "mcp write flow verified",
                    },
                },
            }
        )
        self.assertEqual(audit_record_response["result"]["structuredContent"]["data"]["audit"]["result"], "pass")

        closing_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 16,
                "method": "tools/call",
                "params": {
                    "name": "abh_plan_transition",
                    "arguments": {"confirm": True, "plan_id": "plan-mcp-write", "to": "closing"},
                },
            }
        )
        self.assertEqual(closing_response["result"]["structuredContent"]["data"]["plan"]["status"], "closing")

        close_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 17,
                "method": "tools/call",
                "params": {
                    "name": "abh_close_plan",
                    "arguments": {"confirm": True, "plan_id": "plan-mcp-write"},
                },
            }
        )
        self.assertEqual(close_response["result"]["structuredContent"]["data"]["plan"]["status"], "closed")

        memory_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 18,
                "method": "tools/call",
                "params": {
                    "name": "abh_memory_add",
                    "arguments": {
                        "confirm": True,
                        "memory_id": "mem-mcp-write",
                        "type": "divergent_pattern",
                        "summary": "controlled mcp write flow",
                        "context": "mcp write tools created ABH records",
                        "implication": "write tools preserve ABH gates",
                        "evidence": ["tests/test_cli.py"],
                        "related": ["plan-mcp-write"],
                    },
                },
            }
        )
        self.assertEqual(memory_response["result"]["structuredContent"]["data"]["memory"]["id"], "mem-mcp-write")
        self.assertTrue((self.root / ".abh" / "plans" / "plan-mcp-write.json").exists())
        self.assertTrue((self.root / "docs" / "plans" / "plan-mcp-write.md").exists())
        self.assertTrue((self.root / ".abh" / "audits" / "audit-mcp-write.json").exists())
        self.assertTrue((self.root / ".abh" / "memory" / "mem-mcp-write.json").exists())

    def test_mcp_drift_analyze_write_tool_requires_confirm_and_can_write_report(self) -> None:
        drift_source = self.root / "mcp-drift-source.txt"
        drift_source.write_text("Skipped tests and added external dependency.\n", encoding="utf-8")

        response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 19,
                "method": "tools/call",
                "params": {
                    "name": "abh_drift_analyze",
                    "arguments": {
                        "confirm": True,
                        "drift_id": "drift-mcp-write",
                        "source": str(drift_source),
                        "evidence": ["mcp-drift-source.txt"],
                    },
                },
            }
        )

        envelope = response["result"]["structuredContent"]
        self.assertTrue(envelope["ok"])
        self.assertEqual(envelope["data"]["drift_report"]["id"], "drift-mcp-write")
        self.assertTrue((self.root / ".abh" / "drift" / "drift-mcp-write.json").exists())
