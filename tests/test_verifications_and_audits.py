from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from abh.core import is_recursive_verify_command
from abh.verifications import normalized_git_status
from tests.support import WorkspaceCliTestCase


class VerificationAndAuditTests(WorkspaceCliTestCase):
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

    def test_verify_record_persists_manual_trust_level(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-111-manual-trust",
            "--title",
            "Manual Trust",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "record manual verification trust",
            "--non-goal",
            "execute validation",
            "--exit-criterion",
            "manual trust is persisted",
            "--validation",
            "python3 -m abh doctor",
            "--closure-evidence",
            "docs/plans/plan-111-manual-trust.md",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli(
            "verify",
            "record",
            "plan-111-manual-trust",
            "--command",
            "python3 -m abh doctor",
            "--result",
            "pass",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("plan", "status", "plan-111-manual-trust", "--json")
        self.assertEqual(code, 0, err)
        plan = json.loads(out)["data"]["plan"]
        run_path = self.root / ".abh" / "verifications" / f"{plan['verification_runs'][0]}.json"
        run = json.loads(run_path.read_text(encoding="utf-8"))
        self.assertEqual(run["trust_level"], "manual_record")
        summary = json.loads(out)["data"]["verification_summary"]
        self.assertEqual(summary["trust_level"], "manual_record")
        self.assertFalse(summary["stale"])
        self.assertEqual(summary["reasons"], [])

    def test_verify_run_executes_validation_checklist_and_records_pass(self) -> None:
        command = f'"{sys.executable}" -c "print(\'abh-runner-pass\')"'
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
            command,
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
        self.assertEqual(run["command"], command)
        self.assertTrue(any("exit_code=0" in artifact for artifact in run["artifacts"]))
        self.assertEqual(run["trust_level"], "local_shell")

    def test_verify_run_records_failed_check_and_blocks_running_plan(self) -> None:
        command = f'"{sys.executable}" -c "import sys; sys.exit(7)"'
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
            command,
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
        self.assertEqual(run["failed_checks"], [command])
        self.assertTrue(any("exit_code=7" in artifact for artifact in run["artifacts"]))
        self.assertEqual(run["environment"]["runner"]["check_count"], 1)
        self.assertEqual(run["environment"]["commands"][0]["argv"], [sys.executable, "-c", "import sys; sys.exit(7)"])
        self.assertEqual(
            run["failure_classifications"],
            [
                {
                    "command": command,
                    "category": "validation_failure",
                    "message": "validation command exited with non-zero status",
                    "details": {"exit_code": 7},
                }
            ],
        )

    def test_verify_run_json_returns_machine_readable_result(self) -> None:
        command = f'"{sys.executable}" -c "print(\'abh-json\')"'
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
            command,
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

    def test_verify_run_records_timeout_failure_classification(self) -> None:
        command = f'"{sys.executable}" -c "import time; time.sleep(2)"'
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-114-timeout-classification",
            "--title",
            "Timeout Classification",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "classify timeout",
            "--non-goal",
            "retry command",
            "--exit-criterion",
            "timeout is classified",
            "--validation",
            command,
            "--closure-evidence",
            "docs/plans/plan-114-timeout-classification.md",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("verify", "run", "plan-114-timeout-classification", "--json", "--timeout", "1")
        self.assertEqual(code, 1, err)
        verification = json.loads(out)["data"]["verification"]
        self.assertEqual(verification["result"], "fail")
        self.assertEqual(verification["failure_classifications"][0]["category"], "timeout")
        self.assertEqual(verification["failure_classifications"][0]["command"], command)
        self.assertEqual(verification["failure_classifications"][0]["details"]["timeout_seconds"], 1)

    def test_verify_run_records_environment_metadata(self) -> None:
        command = f'"{sys.executable}" -c "print(\'env-ok\')"'
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-109-runner-environment",
            "--title",
            "Runner Environment",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "record runner environment",
            "--non-goal",
            "isolated execution",
            "--exit-criterion",
            "environment metadata is persisted",
            "--validation",
            command,
            "--closure-evidence",
            "docs/plans/plan-109-runner-environment.md",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("verify", "run", "plan-109-runner-environment", "--json", "--timeout", "17")
        self.assertEqual(code, 0, err)
        verification = json.loads(out)["data"]["verification"]
        environment = verification["environment"]
        self.assertEqual(environment["cwd"], str(self.root.resolve()))
        self.assertEqual(environment["runner"]["timeout_seconds"], 17)
        self.assertTrue(environment["runner"]["shell"])
        self.assertEqual(environment["runner"]["check_count"], 1)
        self.assertEqual(environment["runner"]["execution_policy"], "guarded_local_shell")
        self.assertEqual(environment["runner"]["trust_level"], "local_shell")
        self.assertEqual(environment["runner"]["command_source"], "plan_validation_checklist")
        self.assertEqual(environment["runner"]["isolation"], "none")
        self.assertTrue(environment["python"]["executable"])
        self.assertIn("version", environment["python"])
        self.assertIn("version", environment["abh"])
        self.assertIn("commit", environment["git"])
        self.assertIn("dirty", environment["git"])
        self.assertEqual(environment["commands"][0]["command"], command)
        self.assertEqual(environment["commands"][0]["argv"], [sys.executable, "-c", "print('env-ok')"])
        self.assertIn("environment_variables", environment)

    def test_readme_documents_verify_runner_trust_policy_semantics(self) -> None:
        readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

        self.assertIn("execution_policy=guarded_local_shell", readme)
        self.assertIn("trust_level=local_shell", readme)
        self.assertIn("command_source=plan_validation_checklist", readme)
        self.assertIn("isolation=none", readme)
        self.assertIn("不是隔离环境", readme)
        self.assertIn("不是 CI attestation", readme)
        self.assertIn("不是防篡改证明", readme)
        self.assertIn("未审阅的外部命令", readme)

    def test_plan_status_json_reports_latest_verification_trust_and_stale_state(self) -> None:
        command = f'"{sys.executable}" -c "print(\'fresh\')"'
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-112-stale-summary",
            "--title",
            "Stale Summary",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "report stale summary",
            "--non-goal",
            "block stale close",
            "--exit-criterion",
            "summary is current after run",
            "--validation",
            command,
            "--closure-evidence",
            "docs/plans/plan-112-stale-summary.md",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("verify", "run", "plan-112-stale-summary", "--json")
        self.assertEqual(code, 0, err)
        run = json.loads(out)["data"]["verification"]

        code, out, err = self.run_cli("plan", "status", "plan-112-stale-summary", "--json")
        self.assertEqual(code, 0, err)
        summary = json.loads(out)["data"]["verification_summary"]
        self.assertEqual(summary["latest_id"], run["id"])
        self.assertEqual(summary["trust_level"], "local_shell")
        self.assertFalse(summary["stale"])
        self.assertEqual(summary["reasons"], [])

        code, out, err = self.run_cli(
            "plan",
            "update",
            "plan-112-stale-summary",
            "--validation",
            f'"{sys.executable}" -c "print(\'new-check\')"',
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("plan", "status", "plan-112-stale-summary", "--json")
        self.assertEqual(code, 0, err)
        summary = json.loads(out)["data"]["verification_summary"]
        self.assertEqual(summary["latest_id"], run["id"])
        self.assertTrue(summary["stale"])
        self.assertIn("plan_updated_after_verification", summary["reasons"])
        self.assertIn("validation_checklist_changed", summary["reasons"])
        reason_details = {item["reason"]: item for item in summary["reason_details"]}
        self.assertEqual(reason_details["plan_updated_after_verification"]["category"], "product_proof_drift")
        self.assertTrue(reason_details["plan_updated_after_verification"]["requires_fresh_verification"])
        self.assertEqual(summary["freshness_class"], "product_proof_drift")

    def test_closed_plan_status_distinguishes_governance_metadata_churn(self) -> None:
        self.create_ready_plan("plan-119-closed-freshness")
        self.run_cli(
            "verify",
            "record",
            "plan-119-closed-freshness",
            "--command",
            "unit tests pass",
            "--result",
            "pass",
        )
        plan = json.loads(self.run_cli("plan", "status", "plan-119-closed-freshness", "--json")[1])["data"]["plan"]
        verification_id = plan["verification_runs"][-1]
        self.run_cli(
            "audit",
            "request",
            "plan-119-closed-freshness",
            "--id",
            "audit-119-closed-freshness",
            "--auditor",
            "independent-reviewer",
            "--scope",
            "Independent close audit",
            "--evidence",
            "tests/test_verifications_and_audits.py",
        )
        self.run_cli(
            "audit",
            "record",
            "audit-119-closed-freshness",
            "--result",
            "pass",
            "--rationale",
            "fresh independent evidence verified",
            "--auditor-context",
            "separate session",
            "--independence",
            "independent",
            "--verification-id",
            verification_id,
        )
        self.run_cli("close", "plan-119-closed-freshness")

        code, out, err = self.run_cli("plan", "status", "plan-119-closed-freshness", "--json")

        self.assertEqual(code, 0, err)
        summary = json.loads(out)["data"]["verification_summary"]
        self.assertTrue(summary["stale"])
        self.assertEqual(summary["freshness_class"], "governance_metadata_churn")
        self.assertFalse(summary["requires_fresh_verification"])
        reason_details = {item["reason"]: item for item in summary["reason_details"]}
        self.assertEqual(reason_details["plan_updated_after_verification"]["category"], "governance_metadata_churn")
        self.assertEqual(reason_details["plan_updated_after_verification"]["trigger"], "closed_plan_metadata")
        self.assertEqual(reason_details["plan_updated_after_verification"]["changed_fields"], ["closure_evidence"])

    def test_closed_plan_status_keeps_closure_evidence_changes_as_product_drift(self) -> None:
        self.create_ready_plan("plan-120-closed-proof-drift")
        self.run_cli(
            "verify",
            "record",
            "plan-120-closed-proof-drift",
            "--command",
            "unit tests pass",
            "--result",
            "pass",
        )
        plan = json.loads(self.run_cli("plan", "status", "plan-120-closed-proof-drift", "--json")[1])["data"]["plan"]
        verification_id = plan["verification_runs"][-1]
        self.run_cli(
            "audit",
            "request",
            "plan-120-closed-proof-drift",
            "--id",
            "audit-120-closed-proof-drift",
            "--auditor",
            "independent-reviewer",
            "--scope",
            "Independent close audit",
            "--evidence",
            "tests/test_verifications_and_audits.py",
        )
        self.run_cli(
            "audit",
            "record",
            "audit-120-closed-proof-drift",
            "--result",
            "pass",
            "--rationale",
            "fresh independent evidence verified",
            "--auditor-context",
            "separate session",
            "--independence",
            "independent",
            "--verification-id",
            verification_id,
        )
        self.run_cli("close", "plan-120-closed-proof-drift")
        self.run_cli(
            "plan",
            "update",
            "plan-120-closed-proof-drift",
            "--closure-evidence",
            "docs/plans/post-close-proof-change.md",
        )

        code, out, err = self.run_cli("plan", "status", "plan-120-closed-proof-drift", "--json")

        self.assertEqual(code, 0, err)
        summary = json.loads(out)["data"]["verification_summary"]
        self.assertTrue(summary["stale"])
        self.assertEqual(summary["freshness_class"], "product_proof_drift")
        self.assertTrue(summary["requires_fresh_verification"])
        reason_details = {item["reason"]: item for item in summary["reason_details"]}
        self.assertEqual(reason_details["plan_updated_after_verification"]["category"], "product_proof_drift")
        self.assertEqual(reason_details["plan_updated_after_verification"]["trigger"], "proof_bearing_plan_fields")
        self.assertEqual(reason_details["plan_updated_after_verification"]["changed_fields"], ["closure_evidence"])

    def test_plan_status_json_marks_latest_verification_stale_when_git_status_changes(self) -> None:
        command = f'"{sys.executable}" -c "print(\'git-stale\')"'
        subprocess.run(["git", "init"], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "config", "user.email", "abh@example.test"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "ABH Test"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        tracked = self.root / "tracked.txt"
        tracked.write_text("before\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "seed"], cwd=self.root, check=True, capture_output=True, text=True)

        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-113-git-stale",
            "--title",
            "Git Stale",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "detect git status changes",
            "--non-goal",
            "tamper proof evidence",
            "--exit-criterion",
            "git status change is stale",
            "--validation",
            command,
            "--closure-evidence",
            "docs/plans/plan-113-git-stale.md",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("verify", "run", "plan-113-git-stale", "--json")
        self.assertEqual(code, 0, err)
        verification = json.loads(out)["data"]["verification"]
        self.assertIn("status_hash", verification["environment"]["git"])

        code, out, err = self.run_cli("plan", "status", "plan-113-git-stale", "--json")
        self.assertEqual(code, 0, err)
        summary = json.loads(out)["data"]["verification_summary"]
        self.assertFalse(summary["stale"])

        tracked.write_text("after\n", encoding="utf-8")
        code, out, err = self.run_cli("plan", "status", "plan-113-git-stale", "--json")
        self.assertEqual(code, 0, err)
        summary = json.loads(out)["data"]["verification_summary"]
        self.assertTrue(summary["stale"])
        self.assertIn("git_status_changed", summary["reasons"])

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
        self.assertTrue(
            is_recursive_verify_command(
                "abh verify run plan-recursive-guard",
                "plan-recursive-guard",
            )
        )
        self.assertTrue(
            is_recursive_verify_command(
                ".venv/Scripts/python.exe -m abh verify run plan-recursive-guard",
                "plan-recursive-guard",
            )
        )
        self.assertTrue(
            is_recursive_verify_command(
                "py -m abh verify run plan-recursive-guard",
                "plan-recursive-guard",
            )
        )
        self.assertFalse(
            is_recursive_verify_command(
                "python3 -m abh verify run another-plan",
                "plan-recursive-guard",
            )
        )
        self.assertFalse(
            is_recursive_verify_command(
                "abh verify run another-plan",
                "plan-recursive-guard",
            )
        )
        self.assertFalse(is_recursive_verify_command("python3 -m abh doctor", "plan-recursive-guard"))

    def test_verify_run_recursive_guard_records_environment_metadata(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-110-recursive-environment",
            "--title",
            "Recursive Environment",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "guard recursive verification",
            "--non-goal",
            "execute recursion",
            "--exit-criterion",
            "recursive guard leaves evidence",
            "--validation",
            "python3 -m abh verify run plan-110-recursive-environment",
            "--closure-evidence",
            "docs/plans/plan-110-recursive-environment.md",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("verify", "run", "plan-110-recursive-environment", "--json")
        self.assertEqual(code, 1, err)
        verification = json.loads(out)["data"]["verification"]
        environment = verification["environment"]
        self.assertEqual(environment["runner"]["check_count"], 1)
        self.assertEqual(environment["commands"][0]["command"], "python3 -m abh verify run plan-110-recursive-environment")
        self.assertEqual(
            environment["commands"][0]["argv"],
            ["python3", "-m", "abh", "verify", "run", "plan-110-recursive-environment"],
        )
        self.assertTrue(any("recursive_verify_guard" in artifact for artifact in verification["artifacts"]))
        self.assertEqual(verification["failure_classifications"][0]["category"], "recursive_guard")
        self.assertEqual(
            verification["failure_classifications"][0]["command"],
            "python3 -m abh verify run plan-110-recursive-environment",
        )

    def test_verify_run_records_environment_failure_classification_for_runner_exception(self) -> None:
        command = f'"{sys.executable}" -c "print(\'unused\')"'
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-115-environment-classification",
            "--title",
            "Environment Classification",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "classify runner exception",
            "--non-goal",
            "repair environment",
            "--exit-criterion",
            "runner exception is classified",
            "--validation",
            command,
            "--closure-evidence",
            "docs/plans/plan-115-environment-classification.md",
        )
        self.assertEqual(code, 0, err)

        def raise_os_error(*args, **kwargs):
            raise OSError("spawn failed")

        with patch("abh.verifications.subprocess.run", side_effect=raise_os_error):
            code, out, err = self.run_cli("verify", "run", "plan-115-environment-classification", "--json")

        self.assertEqual(code, 1, err)
        verification = json.loads(out)["data"]["verification"]
        self.assertEqual(verification["result"], "fail")
        self.assertEqual(verification["failed_checks"], [command])
        self.assertEqual(verification["failure_classifications"][0]["category"], "environment_failure")
        self.assertEqual(verification["failure_classifications"][0]["details"]["exception_type"], "OSError")

    def test_git_status_hash_ignores_abh_runtime_evidence_paths(self) -> None:
        status = "\n".join(
            [
                " M .abh/plans/plan-021-verification-trust-and-stale-detection.json",
                " M .abh/audits/audit-021-verification-trust-and-stale-detection.json",
                "?? .abh/memory/mem-opencode-deepseek-audit-models.json",
                "?? .abh/verifications/ver-runtime.json",
                "?? docs/plans/plan-021-verification-trust-and-stale-detection.md",
                "?? docs/audits/audit-021-verification-trust-and-stale-detection.md",
                "?? docs/memory/mem-opencode-deepseek-audit-models.md",
            ]
        )

        self.assertEqual(normalized_git_status(status), "")

    def test_git_status_hash_keeps_product_file_changes(self) -> None:
        status = "\n".join(
            [
                " M abh/verifications.py",
                "?? .abh/verifications/ver-runtime.json",
            ]
        )

        self.assertEqual(normalized_git_status(status), " M abh/verifications.py")

    def test_audit_record_allows_close_only_after_pass(self) -> None:
        self.create_ready_plan()
        code, out, err = self.run_cli(
            "verify",
            "record",
            "plan-200-audit",
            "--command",
            "unit tests pass",
            "--result",
            "pass",
        )
        self.assertEqual(code, 0, err)
        plan = json.loads(self.run_cli("plan", "status", "plan-200-audit", "--json")[1])["data"]["plan"]
        verification_id = plan["verification_runs"][-1]
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
            "tests/test_verifications_and_audits.py",
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
        self.assertEqual(code, 2)
        self.assertIn("independent", err)

        code, out, err = self.run_cli(
            "audit",
            "record",
            "audit-200-audit",
            "--result",
            "pass",
            "--rationale",
            "all exit criteria verified independently",
            "--auditor-context",
            "separate review session",
            "--independence",
            "independent",
            "--verification-id",
            verification_id,
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("close", "plan-200-audit")
        self.assertEqual(code, 0, err)
        self.assertIn("closed plan plan-200-audit", out)

        code, out, err = self.run_cli("plan", "status", "plan-200-audit")
        self.assertEqual(code, 0, err)
        self.assertIn("plan-200-audit [closed]", out)

    def test_audit_record_persists_independent_context_and_verification_basis(self) -> None:
        self.create_ready_plan("plan-211-audit-context")
        code, out, err = self.run_cli(
            "verify",
            "record",
            "plan-211-audit-context",
            "--command",
            "unit tests pass",
            "--result",
            "pass",
        )
        self.assertEqual(code, 0, err)
        plan = json.loads(self.run_cli("plan", "status", "plan-211-audit-context", "--json")[1])["data"]["plan"]
        verification_id = plan["verification_runs"][-1]

        code, out, err = self.run_cli(
            "audit",
            "request",
            "plan-211-audit-context",
            "--id",
            "audit-211-audit-context",
            "--auditor",
            "opencode-deepseek-v4-pro",
            "--scope",
            "Independent close gate audit",
            "--evidence",
            f".abh/verifications/{verification_id}.json",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli(
            "audit",
            "record",
            "audit-211-audit-context",
            "--result",
            "pass",
            "--rationale",
            "independent reviewer checked fresh evidence",
            "--auditor-context",
            "opencode isolated session using DeepSeek V4 Pro",
            "--independence",
            "independent",
            "--verification-id",
            verification_id,
        )
        self.assertEqual(code, 0, err)

        audit_path = self.root / ".abh" / "audits" / "audit-211-audit-context.json"
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        self.assertEqual(audit["auditor_context"], "opencode isolated session using DeepSeek V4 Pro")
        self.assertEqual(audit["independence"], "independent")
        self.assertEqual(audit["verification_id"], verification_id)
        audit_doc = (self.root / "docs" / "audits" / "audit-211-audit-context.md").read_text(encoding="utf-8")
        self.assertIn("- Auditor Context: opencode isolated session using DeepSeek V4 Pro", audit_doc)
        self.assertIn("- Independence: independent", audit_doc)
        self.assertIn(f"- Verification ID: {verification_id}", audit_doc)

    def test_close_requires_independent_audit_tied_to_fresh_latest_verification(self) -> None:
        self.create_ready_plan("plan-212-independent-close")
        self.run_cli(
            "verify",
            "record",
            "plan-212-independent-close",
            "--command",
            "unit tests pass",
            "--result",
            "pass",
        )
        plan = json.loads(self.run_cli("plan", "status", "plan-212-independent-close", "--json")[1])["data"]["plan"]
        first_verification_id = plan["verification_runs"][-1]
        self.run_cli(
            "audit",
            "request",
            "plan-212-independent-close",
            "--id",
            "audit-212-non-independent",
            "--auditor",
            "same-session",
            "--scope",
            "Non-independent audit",
            "--evidence",
            "tests/test_verifications_and_audits.py",
        )
        self.run_cli(
            "audit",
            "record",
            "audit-212-non-independent",
            "--result",
            "pass",
            "--rationale",
            "same session reviewed it",
            "--auditor-context",
            "same implementation session",
            "--independence",
            "self_review",
            "--verification-id",
            first_verification_id,
        )

        code, out, err = self.run_cli("close", "plan-212-independent-close")
        self.assertEqual(code, 2)
        self.assertIn("independent", err)

        self.run_cli(
            "audit",
            "request",
            "plan-212-independent-close",
            "--id",
            "audit-212-stale-independent",
            "--auditor",
            "independent-reviewer",
            "--scope",
            "Independent audit tied to old verification",
            "--evidence",
            "tests/test_verifications_and_audits.py",
        )
        self.run_cli(
            "audit",
            "record",
            "audit-212-stale-independent",
            "--result",
            "pass",
            "--rationale",
            "old verification looked good before the plan changed",
            "--auditor-context",
            "separate session",
            "--independence",
            "independent",
            "--verification-id",
            first_verification_id,
        )
        self.run_cli(
            "verify",
            "record",
            "plan-212-independent-close",
            "--command",
            "unit tests pass",
            "--result",
            "pass",
        )

        code, out, err = self.run_cli("close", "plan-212-independent-close")
        self.assertEqual(code, 2)
        self.assertIn("latest verification", err)

        current_plan = json.loads(self.run_cli("plan", "status", "plan-212-independent-close", "--json")[1])["data"]["plan"]
        latest_verification_id = current_plan["verification_runs"][-1]
        self.run_cli(
            "audit",
            "request",
            "plan-212-independent-close",
            "--id",
            "audit-212-independent-current",
            "--auditor",
            "independent-reviewer",
            "--scope",
            "Independent audit tied to current verification",
            "--evidence",
            "tests/test_verifications_and_audits.py",
        )
        self.run_cli(
            "audit",
            "record",
            "audit-212-independent-current",
            "--result",
            "pass",
            "--rationale",
            "fresh independent evidence verified",
            "--auditor-context",
            "separate session",
            "--independence",
            "independent",
            "--verification-id",
            latest_verification_id,
        )

        code, out, err = self.run_cli("close", "plan-212-independent-close")
        self.assertEqual(code, 0, err)
        self.assertIn("closed plan plan-212-independent-close", out)

    def test_audit_bundle_json_returns_prompt_and_structured_evidence(self) -> None:
        self.create_ready_plan("plan-210-bundle")
        self.run_cli(
            "audit",
            "request",
            "plan-210-bundle",
            "--id",
            "audit-210-bundle",
            "--auditor",
            "opencode-deepseek-v4-pro",
            "--scope",
            "Independent audit of plan-210-bundle",
            "--evidence",
            "docs/plans/plan-210-bundle.md",
        )
        self.run_cli(
            "verify",
            "record",
            "plan-210-bundle",
            "--command",
            "unit tests pass",
            "--result",
            "pass",
            "--artifact",
            "tests/test_verifications_and_audits.py",
        )

        code, out, err = self.run_cli("audit", "bundle", "plan-210-bundle", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "audit bundle")
        bundle = payload["data"]["audit_bundle"]
        self.assertEqual(bundle["plan"]["id"], "plan-210-bundle")
        self.assertEqual(bundle["latest_verification"]["result"], "pass")
        self.assertFalse(bundle["latest_verification"]["stale"])
        self.assertIn(".abh/verifications/", bundle["evidence"]["latest_verification"])
        self.assertTrue(any(path.endswith("docs/plans/plan-210-bundle.md") for path in bundle["evidence"]["plan"]))
        self.assertIn("audit-210-bundle", bundle["requested_audits"][0]["id"])
        self.assertIn("Independent audit only", bundle["prompt"])
        self.assertIn("Do not modify files", bundle["prompt"])
        self.assertIn("Result: pass|fail|partial|need_info", bundle["prompt"])
        self.assertIn("Semantic conservation", bundle["prompt"])
        self.assertIn("in-scope commitments disappeared, weakened, or moved", bundle["prompt"])
        self.assertIn("J-flow-only", bundle["prompt"])
        self.assertIn("R-flow uncertainty reduction", bundle["prompt"])

    def test_audit_docs_document_semantic_conservation_review(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        audit_template = (repo / "docs" / "audits" / "templates" / "audit-template.md").read_text(encoding="utf-8")
        audits_readme = (repo / "docs" / "audits" / "README.md").read_text(encoding="utf-8")
        quality_signals = (repo / "docs" / "architecture" / "quality-signals.md").read_text(encoding="utf-8")

        for text in (audit_template, audits_readme, quality_signals):
            self.assertIn("Semantic Conservation", text)
            self.assertIn("J-flow-only", text)
            self.assertIn("R-flow", text)

    def test_audit_request_markdown_includes_semantic_conservation_review(self) -> None:
        self.create_ready_plan("plan-213-semantic-audit")

        code, out, err = self.run_cli(
            "audit",
            "request",
            "plan-213-semantic-audit",
            "--id",
            "audit-213-semantic-audit",
            "--auditor",
            "independent-reviewer",
            "--scope",
            "Semantic conservation audit",
            "--evidence",
            "docs/plans/plan-213-semantic-audit.md",
        )
        self.assertEqual(code, 0, err)

        audit_doc = (self.root / "docs" / "audits" / "audit-213-semantic-audit.md").read_text(encoding="utf-8")
        self.assertIn("## Semantic Conservation", audit_doc)
        self.assertIn("in-scope commitments disappeared, weakened, or moved", audit_doc)
        self.assertIn("J-flow-only", audit_doc)
        self.assertIn("R-flow", audit_doc)

    def test_audit_list_returns_all_audits(self) -> None:
        self.create_ready_plan("plan-audit-list")
        self.run_cli(
            "audit", "request",
            "plan-audit-list",
            "--id", "audit-list-a",
            "--auditor", "reviewer",
            "--scope", "test audit list",
            "--evidence", "tests/test_verifications_and_audits.py",
        )
        self.run_cli(
            "audit", "request",
            "plan-audit-list",
            "--id", "audit-list-b",
            "--auditor", "reviewer",
            "--scope", "test audit list again",
            "--evidence", "tests/test_verifications_and_audits.py",
        )
        code, out, err = self.run_cli("audit", "list")
        self.assertEqual(code, 0, err)
        self.assertIn("audit-list-a  -> plan-audit-list", out)
        self.assertIn("audit-list-b  -> plan-audit-list", out)
        self.assertIn("total: 2 audit(s)", out)
