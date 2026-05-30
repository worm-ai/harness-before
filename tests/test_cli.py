from __future__ import annotations

import io
import json
import shutil
import subprocess
import tempfile
import threading
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import os

from abh import storage
from abh.cli import main
from abh import audits, plans, verifications
from abh.core import (
    close_plan,
    create_plan,
    is_recursive_verify_command,
    record_audit,
    request_audit,
    run_verification,
    transition_plan,
    update_plan_record,
)
from abh.models import AttractorRecord, AuditRecord, DriftReport, MemoryRecord, PlanRecord, VerificationRun
from abh.models import RoadmapItem, RoadmapQueue
from abh.storage import drift_json_path, write_json
from abh.verifications import normalized_git_status


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

    def test_core_reexports_plan_audit_and_verification_module_functions(self) -> None:
        self.assertIs(create_plan, plans.create_plan)
        self.assertIs(update_plan_record, plans.update_plan_record)
        self.assertIs(transition_plan, plans.transition_plan)
        self.assertIs(close_plan, plans.close_plan)
        self.assertIs(run_verification, verifications.run_verification)
        self.assertIs(request_audit, audits.request_audit)
        self.assertIs(record_audit, audits.record_audit)

    def test_core_reexports_memory_drift_and_routing_module_functions(self) -> None:
        from abh import core, drift, memory, routing

        self.assertIs(core.add_memory, memory.add_memory)
        self.assertIs(core.search_memory, memory.search_memory)
        self.assertIs(core.list_memories, memory.list_memories)
        self.assertIs(core.analyze_drift, drift.analyze_drift)
        self.assertIs(core.route_question, routing.route_question)

    def test_agent_first_command_contract_describes_existing_agent_commands(self) -> None:
        from abh.commands import command_contract, make_envelope

        next_contract = command_contract("next")
        self.assertEqual(next_contract.cli_command, "next")
        self.assertTrue(next_contract.read_only)
        self.assertEqual(next_contract.confirmation, "none")
        self.assertEqual(next_contract.side_effects, [])
        self.assertEqual(next_contract.output_keys, ["next"])

        onboarding_contract = command_contract("onboarding.check")
        self.assertEqual(onboarding_contract.cli_command, "onboarding check")
        self.assertTrue(onboarding_contract.read_only)
        self.assertEqual(onboarding_contract.confirmation, "none")
        self.assertEqual(onboarding_contract.side_effects, [])
        self.assertEqual(onboarding_contract.output_keys, ["onboarding"])

        hooks_profile = command_contract("hooks.profile")
        self.assertEqual(hooks_profile.cli_command, "hooks profile")
        self.assertTrue(hooks_profile.read_only)
        self.assertEqual(hooks_profile.confirmation, "none")
        self.assertEqual(hooks_profile.side_effects, [])
        self.assertEqual(hooks_profile.output_keys, ["profile"])

        hooks_install = command_contract("hooks.install")
        self.assertEqual(hooks_install.cli_command, "hooks install")
        self.assertFalse(hooks_install.read_only)
        self.assertEqual(hooks_install.confirmation, "--write --confirm")
        self.assertIn("write", hooks_install.input_schema["properties"])
        self.assertIn("confirm", hooks_install.input_schema["properties"])
        self.assertTrue(any(".git/hooks/pre-commit" in effect for effect in hooks_install.side_effects))

        plan_status = command_contract("plan.status")
        self.assertEqual(plan_status.cli_command, "plan status")
        self.assertEqual(plan_status.mcp_tool, "abh_plan_status")
        self.assertTrue(plan_status.read_only)
        self.assertEqual(plan_status.confirmation, "none")
        self.assertEqual(plan_status.side_effects, [])
        self.assertIn("plan_id", plan_status.input_schema["properties"])

        audit_bundle = command_contract("audit.bundle")
        self.assertEqual(audit_bundle.cli_command, "audit bundle")
        self.assertTrue(audit_bundle.read_only)
        self.assertEqual(audit_bundle.confirmation, "none")
        self.assertEqual(audit_bundle.side_effects, [])
        self.assertEqual(audit_bundle.output_keys, ["audit_bundle"])
        self.assertIn("plan_id", audit_bundle.input_schema["properties"])

        audit_record = command_contract("audit.record")
        self.assertEqual(audit_record.cli_command, "audit record")
        self.assertEqual(audit_record.mcp_tool, "abh_audit_record")
        self.assertFalse(audit_record.read_only)
        self.assertIn("auditor_context", audit_record.input_schema["properties"])
        self.assertIn("independence", audit_record.input_schema["properties"])
        self.assertIn("verification_id", audit_record.input_schema["properties"])

        memory_add = command_contract("memory.add")
        self.assertEqual(memory_add.cli_command, "memory add")
        self.assertEqual(memory_add.mcp_tool, "abh_memory_add")
        self.assertFalse(memory_add.read_only)
        self.assertIn("tags", memory_add.input_schema["properties"])
        self.assertIn("status", memory_add.input_schema["properties"])
        self.assertIn("related_plan_ids", memory_add.input_schema["properties"])
        self.assertIn("related_audit_ids", memory_add.input_schema["properties"])
        self.assertIn("related_drift_ids", memory_add.input_schema["properties"])
        self.assertIn("superseded_by", memory_add.input_schema["properties"])

        plan_create = command_contract("plan.create")
        self.assertEqual(plan_create.cli_command, "plan create")
        self.assertEqual(plan_create.mcp_tool, "abh_plan_create")
        self.assertFalse(plan_create.read_only)
        self.assertEqual(plan_create.confirmation, "confirm=true")
        self.assertIn("confirm", plan_create.input_schema["required"])
        self.assertTrue(any(".abh/plans/" in effect for effect in plan_create.side_effects))

        init_workspace = command_contract("init.workspace")
        self.assertEqual(init_workspace.cli_command, "init")
        self.assertFalse(init_workspace.read_only)
        self.assertEqual(init_workspace.confirmation, "--write --confirm")
        self.assertIn("write", init_workspace.input_schema["properties"])
        self.assertIn("confirm", init_workspace.input_schema["properties"])
        self.assertTrue(any("docs/index.md" in effect for effect in init_workspace.side_effects))

        for command_id, cli_command in (
            ("agent.setup.codex", "agent setup codex"),
            ("agent.setup.claude_code", "agent setup claude-code"),
            ("agent.setup.mcp", "agent setup mcp"),
        ):
            with self.subTest(command_id=command_id):
                contract = command_contract(command_id)
                self.assertEqual(contract.cli_command, cli_command)
                self.assertTrue(contract.read_only)
                self.assertEqual(contract.confirmation, "none")
                self.assertEqual(contract.side_effects, [])
                self.assertEqual(contract.output_keys, ["setup"])

        envelope = make_envelope(ok=True, command="plan.status", data={"plan": {"id": "plan-contract"}})
        self.assertEqual(envelope["schema_version"], "1")
        self.assertTrue(envelope["ok"])
        self.assertEqual(envelope["command"], "plan.status")
        self.assertEqual(envelope["errors"], [])

    def test_init_preview_is_machine_readable_and_does_not_write(self) -> None:
        shutil.rmtree(self.root / "docs")

        code, out, err = self.run_cli("init", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "init")
        result = payload["data"]["init"]
        self.assertEqual(result["mode"], "preview")
        self.assertFalse(result["write"])
        self.assertFalse(result["confirmed"])
        self.assertEqual(result["active_attractor"]["id"], "attractor-abh-core")
        write_paths = {item["path"] for item in result["writes"]}
        self.assertIn(".abh/plans", write_paths)
        self.assertIn(".abh/attractors/attractor-abh-core.json", write_paths)
        self.assertIn("docs/index.md", write_paths)
        self.assertIn("docs/context/source-of-truth.md", write_paths)
        self.assertIn("docs/architecture/attractors/abh-core-attractor.md", write_paths)
        self.assertFalse((self.root / ".abh").exists())
        self.assertFalse((self.root / "docs").exists())

    def test_init_write_requires_confirm(self) -> None:
        shutil.rmtree(self.root / "docs")

        code, out, err = self.run_cli("init", "--write", "--json")

        self.assertEqual(code, 2)
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertIn("--confirm", payload["errors"][0]["message"])
        self.assertFalse((self.root / ".abh").exists())
        self.assertFalse((self.root / "docs").exists())

    def test_init_write_confirm_creates_workspace_and_active_attractor(self) -> None:
        shutil.rmtree(self.root / "docs")

        code, out, err = self.run_cli("init", "--write", "--confirm", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        result = payload["data"]["init"]
        self.assertEqual(result["mode"], "write")
        self.assertTrue(result["write"])
        self.assertTrue(result["confirmed"])
        write_paths = {item["path"] for item in result["writes"]}
        self.assertIn("docs/index.md", write_paths)
        self.assertIn(".abh/attractors/attractor-abh-core.json", write_paths)
        self.assertEqual(result["active_attractor"]["path"], "docs/architecture/attractors/abh-core-attractor.md")
        self.assertTrue((self.root / ".abh" / "plans").is_dir())
        self.assertTrue((self.root / ".abh" / "audits").is_dir())
        self.assertTrue((self.root / ".abh" / "verifications").is_dir())
        self.assertTrue((self.root / ".abh" / "attractors" / "attractor-abh-core.json").exists())
        self.assertTrue((self.root / "docs" / "index.md").exists())
        self.assertTrue((self.root / "docs" / "context" / "source-of-truth.md").exists())
        self.assertTrue((self.root / "docs" / "requirements").is_dir())
        self.assertTrue((self.root / "docs" / "requirements" / "README.md").exists())
        self.assertTrue((self.root / "docs" / "design").is_dir())
        self.assertTrue((self.root / "docs" / "design" / "README.md").exists())

        code, out, err = self.run_cli("attractor", "active", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["data"]["attractor"]["id"], "attractor-abh-core")

    def test_init_write_confirm_does_not_overwrite_existing_files(self) -> None:
        (self.root / "README.md").write_text("# Existing README\n", encoding="utf-8")
        (self.root / "AGENTS.md").write_text("# Existing Agents\n", encoding="utf-8")
        existing_index = self.root / "docs" / "index.md"
        existing_index.write_text("# Existing Index\n", encoding="utf-8")
        existing_attractor = self.root / "docs" / "architecture" / "attractors" / "abh-core-attractor.md"
        existing_attractor.write_text("# Existing Attractor\n", encoding="utf-8")

        code, out, err = self.run_cli("init", "--write", "--confirm", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        skipped_paths = {item["path"] for item in payload["data"]["init"]["skips"]}
        self.assertIn("README.md", skipped_paths)
        self.assertIn("AGENTS.md", skipped_paths)
        self.assertIn("docs/index.md", skipped_paths)
        self.assertIn("docs/architecture/attractors/abh-core-attractor.md", skipped_paths)
        self.assertEqual((self.root / "README.md").read_text(encoding="utf-8"), "# Existing README\n")
        self.assertEqual((self.root / "AGENTS.md").read_text(encoding="utf-8"), "# Existing Agents\n")
        self.assertEqual(existing_index.read_text(encoding="utf-8"), "# Existing Index\n")
        self.assertEqual(existing_attractor.read_text(encoding="utf-8"), "# Existing Attractor\n")
        self.assertTrue((self.root / ".abh" / "attractors" / "attractor-abh-core.json").exists())

    def test_agent_setup_codex_json_returns_readonly_bundle(self) -> None:
        self.run_cli("init", "--write", "--confirm", "--json")

        code, out, err = self.run_cli("agent", "setup", "codex", "--json")

        self.assertEqual(code, 0, err)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "agent setup codex")
        setup = payload["data"]["setup"]
        self.assertEqual(setup["agent"], "codex")
        self.assertEqual(setup["active_attractor"]["id"], "attractor-abh-core")
        self.assertEqual(setup["active_attractor"]["path"], "docs/architecture/attractors/abh-core-attractor.md")
        self.assertIn("docs/index.md", setup["required_reading"])
        self.assertIn("docs/context/source-of-truth.md", setup["required_reading"])
        self.assertIn("docs/architecture/agent-protocol.md", setup["required_reading"])
        self.assertIn("verification is evidence, not completion", setup["workflow_rules"])
        self.assertIn("abh attractor active --json", setup["commands"])
        self.assertEqual(setup["write_policy"]["mode"], "read_only")
        self.assertEqual(setup["write_policy"]["writes"], [])
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertFalse((self.root / "CLAUDE.md").exists())

    def test_agent_setup_targets_share_shape_and_mcp_includes_server_command(self) -> None:
        self.run_cli("init", "--write", "--confirm", "--json")

        for target in ("claude-code", "mcp"):
            with self.subTest(target=target):
                code, out, err = self.run_cli("agent", "setup", target, "--json")
                self.assertEqual(code, 0, err)
                payload = json.loads(out)
                self.assertTrue(payload["ok"])
                self.assertEqual(payload["command"], f"agent setup {target}")
                setup = payload["data"]["setup"]
                self.assertEqual(setup["agent"], target)
                self.assertIn("active_attractor", setup)
                self.assertIn("required_reading", setup)
                self.assertIn("workflow_rules", setup)
                self.assertIn("commands", setup)
                self.assertEqual(setup["write_policy"]["mode"], "read_only")

        mcp_setup = json.loads(self.run_cli("agent", "setup", "mcp", "--json")[1])["data"]["setup"]
        self.assertEqual(mcp_setup["server"]["command"], "python3 -m abh.mcp_server")
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertFalse((self.root / "CLAUDE.md").exists())
        self.assertFalse((self.root / ".mcp.json").exists())

    def test_hooks_profile_json_returns_default_guardrail_profile(self) -> None:
        code, out, err = self.run_cli("hooks", "profile", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "hooks profile")
        profile = payload["data"]["profile"]
        self.assertEqual(profile["name"], "default")
        self.assertEqual(profile["hook"], "pre-commit")
        self.assertEqual(profile["path"], ".git/hooks/pre-commit")
        self.assertIn("ABH MANAGED PRE-COMMIT", profile["managed_marker"])
        self.assertEqual(
            profile["commands"],
            ["python3 -m abh doctor", "python3 -m abh roadmap check --json", "git diff --check"],
        )
        self.assertIn("plan_doc_sync", profile["invariants"])
        self.assertEqual(profile["write_policy"]["mode"], "preview_by_default")
        self.assertFalse((self.root / ".git" / "hooks" / "pre-commit").exists())

    def test_hooks_install_preview_does_not_write_hook(self) -> None:
        code, out, err = self.run_cli("hooks", "install", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "hooks install")
        install = payload["data"]["install"]
        self.assertEqual(install["mode"], "preview")
        self.assertFalse(install["write"])
        self.assertFalse(install["confirmed"])
        self.assertEqual(install["path"], ".git/hooks/pre-commit")
        self.assertEqual(install["writes"][0]["path"], ".git/hooks/pre-commit")
        self.assertEqual(install["blockers"], [])
        self.assertFalse((self.root / ".git" / "hooks" / "pre-commit").exists())

    def test_hooks_install_write_requires_confirm(self) -> None:
        code, out, err = self.run_cli("hooks", "install", "--write", "--json")

        self.assertEqual(code, 2)
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertIn("--confirm", payload["errors"][0]["message"])
        self.assertFalse((self.root / ".git" / "hooks" / "pre-commit").exists())

    def test_hooks_install_write_confirm_creates_executable_managed_hook(self) -> None:
        code, out, err = self.run_cli("hooks", "install", "--write", "--confirm", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        install = payload["data"]["install"]
        self.assertEqual(install["mode"], "write")
        self.assertTrue(install["write"])
        self.assertTrue(install["confirmed"])
        hook_path = self.root / ".git" / "hooks" / "pre-commit"
        self.assertTrue(hook_path.exists())
        content = hook_path.read_text(encoding="utf-8")
        self.assertIn("ABH MANAGED PRE-COMMIT", content)
        self.assertIn("python3 -m abh doctor", content)
        self.assertIn("python3 -m abh roadmap check --json", content)
        self.assertIn("git diff --check", content)
        self.assertTrue(os.access(hook_path, os.X_OK))

    def test_hooks_install_does_not_overwrite_unmanaged_hook(self) -> None:
        hook_path = self.root / ".git" / "hooks" / "pre-commit"
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")

        code, out, err = self.run_cli("hooks", "install", "--write", "--confirm", "--json")

        self.assertEqual(code, 2)
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertIn("existing unmanaged hook", payload["errors"][0]["message"])
        self.assertEqual(hook_path.read_text(encoding="utf-8"), "#!/bin/sh\necho custom\n")

    def test_next_json_recommends_materializing_next_queued_item_when_no_open_plans(self) -> None:
        self.run_cli("init", "--write", "--confirm", "--json")
        queue = self.root / ".abh" / "roadmap.json"
        queue.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "items": [
                        {
                            "key": "stage4.abh-next-and-onboarding-check",
                            "title": "ABH Next and Onboarding Check",
                            "stage": "stage4",
                            "summary": "Expose next action.",
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        code, out, err = self.run_cli("next", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "next")
        result = payload["data"]["next"]
        self.assertEqual(result["next_action"], "materialize_roadmap_item")
        self.assertEqual(result["recommended_command"], "abh roadmap materialize stage4.abh-next-and-onboarding-check --json")
        self.assertFalse(result["requires_confirmation"])
        self.assertIn("no open plans", result["rationale"])
        self.assertEqual(result["source"]["roadmap_key"], "stage4.abh-next-and-onboarding-check")
        self.assertIn("abh roadmap list --json", result["alternatives"])

    def test_next_json_prioritizes_existing_draft_plan(self) -> None:
        self.run_cli("init", "--write", "--confirm", "--json")
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-200-draft",
            "--title",
            "Draft Plan",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("next", "--json")

        self.assertEqual(code, 0, err)
        result = json.loads(out)["data"]["next"]
        self.assertEqual(result["next_action"], "complete_plan_definition")
        self.assertEqual(result["recommended_command"], "abh plan status plan-200-draft --json")
        self.assertFalse(result["requires_confirmation"])
        self.assertEqual(result["source"]["plan_id"], "plan-200-draft")

    def test_next_json_recommends_audit_after_fresh_passing_verification(self) -> None:
        self.run_cli("init", "--write", "--confirm", "--json")
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-202-verified",
            "--title",
            "Verified Plan",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "recommend audit",
            "--non-goal",
            "close automatically",
            "--exit-criterion",
            "audit recommended",
            "--validation",
            "python3 -c 'print(\"verified\")'",
            "--closure-evidence",
            "docs/plans/plan-202-verified.md",
        )
        self.assertEqual(code, 0, err)
        code, out, err = self.run_cli("verify", "run", "plan-202-verified", "--json")
        self.assertEqual(code, 0, err)
        verification_id = json.loads(out)["data"]["verification"]["id"]

        code, out, err = self.run_cli("next", "--json")

        self.assertEqual(code, 0, err)
        result = json.loads(out)["data"]["next"]
        self.assertEqual(result["next_action"], "request_audit")
        self.assertEqual(
            result["recommended_command"],
            f'abh audit request plan-202-verified --id audit-202-verified --auditor human-independent-review --scope "Independent audit of plan-202-verified" --evidence docs/plans/plan-202-verified.md --evidence .abh/verifications/{verification_id}.json',
        )
        self.assertFalse(result["requires_confirmation"])
        self.assertEqual(result["source"]["plan_id"], "plan-202-verified")
        self.assertEqual(result["source"]["latest_verification"], verification_id)

    def test_onboarding_check_json_reports_readiness(self) -> None:
        self.run_cli("init", "--write", "--confirm", "--json")
        self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-201-loop",
            "--title",
            "Loop",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "close a loop",
            "--non-goal",
            "ship ui",
            "--exit-criterion",
            "closed",
            "--validation",
            "python3 -m abh doctor",
            "--closure-evidence",
            "docs/plans/plan-201-loop.md",
        )
        self.run_cli("verify", "record", "plan-201-loop", "--command", "python3 -m abh doctor", "--result", "pass")
        plan = json.loads(self.run_cli("plan", "status", "plan-201-loop", "--json")[1])["data"]["plan"]
        verification_id = plan["verification_runs"][-1]
        self.run_cli(
            "audit",
            "request",
            "plan-201-loop",
            "--id",
            "audit-201-loop",
            "--auditor",
            "reviewer",
            "--scope",
            "loop",
            "--evidence",
            "docs/plans/plan-201-loop.md",
        )
        self.run_cli(
            "audit",
            "record",
            "audit-201-loop",
            "--result",
            "pass",
            "--rationale",
            "ok",
            "--auditor-context",
            "independent onboarding smoke reviewer",
            "--independence",
            "independent",
            "--verification-id",
            verification_id,
        )
        self.run_cli("close", "plan-201-loop")

        code, out, err = self.run_cli("onboarding", "check", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "onboarding check")
        onboarding = payload["data"]["onboarding"]
        self.assertTrue(onboarding["ready"])
        check_statuses = {check["id"]: check["status"] for check in onboarding["checks"]}
        self.assertEqual(check_statuses["active_attractor"], "pass")
        self.assertEqual(check_statuses["owner_docs"], "pass")
        self.assertEqual(check_statuses["agent_setup_export"], "pass")
        self.assertEqual(check_statuses["hook_guardrails"], "pass")
        self.assertEqual(check_statuses["doctor"], "pass")
        self.assertEqual(check_statuses["closed_loop_evidence"], "pass")
        self.assertEqual(onboarding["recommended_actions"], [])

    def test_attractor_create_active_show_list_and_supersede_json_flow(self) -> None:
        code, out, err = self.run_cli(
            "attractor",
            "create",
            "--id",
            "attractor-product",
            "--title",
            "Product Attractor",
            "--version",
            "0.1.0",
            "--path",
            "docs/architecture/attractors/product.md",
            "--owner",
            "architecture",
            "--intent",
            "Keep product work evidence-first.",
            "--invariant",
            "Plans must cite product evidence.",
            "--json",
        )
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "attractor create")
        attractor = payload["data"]["attractor"]
        self.assertEqual(attractor["id"], "attractor-product")
        self.assertEqual(attractor["status"], "active")
        self.assertTrue((self.root / ".abh" / "attractors" / "attractor-product.json").exists())
        self.assertTrue((self.root / "docs" / "architecture" / "attractors" / "product.md").exists())

        code, out, err = self.run_cli("attractor", "active", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["data"]["attractor"]["id"], "attractor-product")

        code, out, err = self.run_cli("attractor", "show", "attractor-product", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["data"]["attractor"]["path"], "docs/architecture/attractors/product.md")

        code, out, err = self.run_cli("attractor", "list", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["data"]["total"], 1)

        code, out, err = self.run_cli(
            "attractor",
            "supersede",
            "attractor-product",
            "--id",
            "attractor-product-v2",
            "--title",
            "Product Attractor V2",
            "--version",
            "0.2.0",
            "--path",
            "docs/architecture/attractors/product-v2.md",
            "--reason",
            "Audit found missing release boundary.",
            "--impact",
            "New plans must cite release evidence.",
            "--migration-strategy",
            "Existing plans keep old attractor; new plans use v2.",
            "--json",
        )
        self.assertEqual(code, 0, err)
        supersede_payload = json.loads(out)
        self.assertEqual(supersede_payload["data"]["old_attractor"]["status"], "inactive")
        self.assertEqual(supersede_payload["data"]["attractor"]["supersedes"], "attractor-product")

        code, out, err = self.run_cli("attractor", "active", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["data"]["attractor"]["id"], "attractor-product-v2")

    def test_attractor_create_does_not_overwrite_existing_markdown(self) -> None:
        existing = self.root / "docs" / "architecture" / "attractors" / "existing.md"
        existing.write_text("# Existing Attractor\n\n## Custom Section\n\nDo not overwrite.\n", encoding="utf-8")

        code, out, err = self.run_cli(
            "attractor",
            "create",
            "--id",
            "attractor-existing",
            "--title",
            "Existing",
            "--version",
            "1.0.0",
            "--path",
            "docs/architecture/attractors/existing.md",
            "--intent",
            "Register existing document.",
            "--json",
        )

        self.assertEqual(code, 0, err)
        self.assertEqual(existing.read_text(encoding="utf-8"), "# Existing Attractor\n\n## Custom Section\n\nDo not overwrite.\n")
        self.assertEqual(json.loads(out)["data"]["attractor"]["doc_path"], "docs/architecture/attractors/existing.md")

    def test_ready_plan_must_reference_active_attractor_by_id_or_path(self) -> None:
        code, out, err = self.run_cli(
            "attractor",
            "create",
            "--id",
            "attractor-active",
            "--title",
            "Active",
            "--version",
            "1.0.0",
            "--path",
            "docs/architecture/attractors/active.md",
            "--intent",
            "Active attractor",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-active-by-id",
            "--title",
            "Active By ID",
            "--attractor",
            "attractor-active",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "use active id",
            "--non-goal",
            "inactive attractor",
            "--exit-criterion",
            "plan ready",
            "--validation",
            "python3 -m abh doctor",
            "--closure-evidence",
            "tests/test_cli.py",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-active-by-path",
            "--title",
            "Active By Path",
            "--attractor",
            "docs/architecture/attractors/active.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "use active path",
            "--non-goal",
            "inactive attractor",
            "--exit-criterion",
            "plan ready",
            "--validation",
            "python3 -m abh doctor",
            "--closure-evidence",
            "tests/test_cli.py",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-inactive-attractor",
            "--title",
            "Inactive",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "reject inactive",
            "--non-goal",
            "accept inactive",
            "--exit-criterion",
            "rejected",
            "--validation",
            "python3 -m abh doctor",
            "--closure-evidence",
            "tests/test_cli.py",
        )
        self.assertEqual(code, 2)
        self.assertIn("active attractor", err)

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

    def test_roadmap_next_id_list_and_materialize_queue_item(self) -> None:
        queue = self.root / ".abh" / "roadmap.json"
        queue.parent.mkdir(parents=True, exist_ok=True)
        queue.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "items": [
                        {
                            "key": "stage4.abh-init-active-attractor",
                            "title": "ABH Init Active Attractor",
                            "stage": "stage4",
                            "summary": "Initialize a repository around the active attractor.",
                            "attractor": "docs/architecture/attractors/abh-core-attractor.md",
                            "baseline": "queue baseline",
                            "goals": ["materialize the next plan id"],
                            "non_goals": ["preassign plan numbers in docs"],
                            "exit_criteria": ["plan exists"],
                            "validation_checklist": ["python3 -m abh doctor"],
                            "closure_evidence": ["docs/development-roadmap.md"],
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        code, out, err = self.run_cli("roadmap", "next-id", "--json")
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["command"], "roadmap next-id")
        self.assertEqual(payload["data"]["next_plan_id"], "plan-001")
        self.assertEqual(payload["data"]["next_sequence"], 1)

        code, out, err = self.run_cli("roadmap", "list", "--json")
        self.assertEqual(code, 0, err)
        list_payload = json.loads(out)
        self.assertEqual(list_payload["data"]["items"][0]["key"], "stage4.abh-init-active-attractor")
        self.assertIsNone(list_payload["data"]["items"][0]["plan_id"])

        code, out, err = self.run_cli("roadmap", "materialize", "stage4.abh-init-active-attractor", "--json")
        self.assertEqual(code, 0, err)
        materialize_payload = json.loads(out)
        self.assertEqual(materialize_payload["data"]["plan"]["id"], "plan-001-abh-init-active-attractor")
        self.assertEqual(materialize_payload["data"]["item"]["plan_id"], "plan-001-abh-init-active-attractor")
        self.assertTrue((self.root / ".abh" / "plans" / "plan-001-abh-init-active-attractor.json").exists())

        code, out, err = self.run_cli("roadmap", "next-id", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["data"]["next_plan_id"], "plan-002")

    def test_roadmap_materialize_rejects_preassigned_plan_id(self) -> None:
        queue = self.root / ".abh" / "roadmap.json"
        queue.parent.mkdir(parents=True, exist_ok=True)
        queue.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "items": [
                        {
                            "key": "stage4.bad-preassigned",
                            "title": "Bad Preassigned",
                            "stage": "stage4",
                            "summary": "Bad item",
                            "planned_plan_id": "plan-999-bad",
                            "attractor": "docs/architecture/attractors/abh-core-attractor.md",
                            "baseline": "baseline",
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )

        code, out, err = self.run_cli("roadmap", "materialize", "stage4.bad-preassigned", "--json")

        self.assertEqual(code, 2)
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertIn("must not preassign plan id", payload["errors"][0]["message"])

    def test_roadmap_materialize_uses_allocation_lock(self) -> None:
        queue = self.root / ".abh" / "roadmap.json"
        queue.parent.mkdir(parents=True, exist_ok=True)
        queue.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "items": [
                        {
                            "key": "stage4.concurrent-alpha",
                            "title": "Concurrent Alpha",
                            "stage": "stage4",
                            "summary": "alpha",
                            "attractor": "docs/architecture/attractors/abh-core-attractor.md",
                            "baseline": "baseline",
                        },
                        {
                            "key": "stage4.concurrent-beta",
                            "title": "Concurrent Beta",
                            "stage": "stage4",
                            "summary": "beta",
                            "attractor": "docs/architecture/attractors/abh-core-attractor.md",
                            "baseline": "baseline",
                        },
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        from abh import roadmap

        locked_paths: list[Path] = []

        class SpyLock:
            def __init__(self, path: Path) -> None:
                self.path = path

            def __enter__(self):
                locked_paths.append(self.path)

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("abh.roadmap.file_lock", side_effect=lambda path: SpyLock(path), create=True):
            roadmap.materialize_roadmap_item("stage4.concurrent-alpha", cwd=self.root)

        self.assertEqual(locked_paths, [self.root / ".abh" / "roadmap.materialize"])

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
        self.assertEqual(run["trust_level"], "local_shell")

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
        self.assertEqual(run["environment"]["runner"]["check_count"], 1)
        self.assertEqual(run["environment"]["commands"][0]["argv"], ["python3", "-c", "import sys; sys.exit(7)"])
        self.assertEqual(
            run["failure_classifications"],
            [
                {
                    "command": "python3 -c 'import sys; sys.exit(7)'",
                    "category": "validation_failure",
                    "message": "validation command exited with non-zero status",
                    "details": {"exit_code": 7},
                }
            ],
        )

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

    def test_verify_run_records_timeout_failure_classification(self) -> None:
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
            "python3 -c 'import time; time.sleep(1)'",
            "--closure-evidence",
            "docs/plans/plan-114-timeout-classification.md",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("verify", "run", "plan-114-timeout-classification", "--json", "--timeout", "1")
        self.assertEqual(code, 1, err)
        verification = json.loads(out)["data"]["verification"]
        self.assertEqual(verification["result"], "fail")
        self.assertEqual(verification["failure_classifications"][0]["category"], "timeout")
        self.assertEqual(verification["failure_classifications"][0]["command"], "python3 -c 'import time; time.sleep(1)'")
        self.assertEqual(verification["failure_classifications"][0]["details"]["timeout_seconds"], 1)

    def test_verify_run_records_environment_metadata(self) -> None:
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
            "python3 -c 'print(\"env-ok\")'",
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
        self.assertTrue(environment["python"]["executable"])
        self.assertIn("version", environment["python"])
        self.assertIn("version", environment["abh"])
        self.assertIn("commit", environment["git"])
        self.assertIn("dirty", environment["git"])
        self.assertEqual(environment["commands"][0]["command"], "python3 -c 'print(\"env-ok\")'")
        self.assertEqual(environment["commands"][0]["argv"], ["python3", "-c", "print(\"env-ok\")"])
        self.assertIn("environment_variables", environment)

    def test_plan_status_json_reports_latest_verification_trust_and_stale_state(self) -> None:
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
            "python3 -c 'print(\"fresh\")'",
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
            "python3 -c 'print(\"new-check\")'",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("plan", "status", "plan-112-stale-summary", "--json")
        self.assertEqual(code, 0, err)
        summary = json.loads(out)["data"]["verification_summary"]
        self.assertEqual(summary["latest_id"], run["id"])
        self.assertTrue(summary["stale"])
        self.assertIn("plan_updated_after_verification", summary["reasons"])
        self.assertIn("validation_checklist_changed", summary["reasons"])

    def test_plan_status_json_marks_latest_verification_stale_when_git_status_changes(self) -> None:
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
            "python3 -c 'print(\"git-stale\")'",
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
        self.assertFalse(
            is_recursive_verify_command(
                "python3 -m abh verify run another-plan",
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
            "python3 -c 'print(\"unused\")'",
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
        self.assertEqual(verification["failed_checks"], ["python3 -c 'print(\"unused\")'"])
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
            "tests/test_cli.py",
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
            "tests/test_cli.py",
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
            "tests/test_cli.py",
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
            "tests/test_cli.py",
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

    def test_memory_metadata_is_recorded_searchable_and_rendered(self) -> None:
        code, out, err = self.run_cli(
            "memory",
            "add",
            "--id",
            "mem-quality-001",
            "--type",
            "false_assumption",
            "--summary",
            "Quality metadata makes memory reusable",
            "--context",
            "A plan repeated a previously rejected shortcut.",
            "--evidence",
            "docs/audits/audit-040-drift-quality.md",
            "--tag",
            "quality-signal",
            "--tag",
            "audit",
            "--status",
            "active",
            "--related-plan",
            "plan-040-drift-quality",
            "--related-audit",
            "audit-040-drift-quality",
            "--related-drift",
            "drift-quality-001",
            "--superseded-by",
            "mem-quality-002",
            "--related",
            "plan-040-drift-quality",
            "--implication",
            "Route and audit flows should surface reusable memory.",
        )

        self.assertEqual(code, 0, err)
        payload = json.loads((self.root / ".abh" / "memory" / "mem-quality-001.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["tags"], ["quality-signal", "audit"])
        self.assertEqual(payload["status"], "active")
        self.assertEqual(payload["related_plan_ids"], ["plan-040-drift-quality"])
        self.assertEqual(payload["related_audit_ids"], ["audit-040-drift-quality"])
        self.assertEqual(payload["related_drift_ids"], ["drift-quality-001"])
        self.assertEqual(payload["superseded_by"], "mem-quality-002")

        markdown = (self.root / "docs" / "memory" / "mem-quality-001.md").read_text(encoding="utf-8")
        self.assertIn("- Tags: quality-signal, audit", markdown)
        self.assertIn("- Related Plans: plan-040-drift-quality", markdown)
        self.assertIn("- Related Audits: audit-040-drift-quality", markdown)
        self.assertIn("- Related Drift Reports: drift-quality-001", markdown)
        self.assertIn("- Superseded By: mem-quality-002", markdown)

        code, out, err = self.run_cli(
            "memory",
            "search",
            "--status",
            "active",
            "--related-plan",
            "plan-040-drift-quality",
            "--tag",
            "quality-signal",
            "--json",
        )
        self.assertEqual(code, 0, err)
        result = json.loads(out)["data"]["memories"]
        self.assertEqual([memory["id"] for memory in result], ["mem-quality-001"])
        self.assertEqual(result[0]["related_plan_ids"], ["plan-040-drift-quality"])

    def test_memory_legacy_records_get_metadata_defaults(self) -> None:
        (self.root / ".abh" / "memory").mkdir(parents=True, exist_ok=True)
        write_json(
            self.root / ".abh" / "memory" / "mem-legacy.json",
            {
                "schema_version": "1",
                "id": "mem-legacy",
                "type": "rejected_path",
                "summary": "legacy memory",
                "context": "created before memory index",
                "implication": "legacy reads still work",
                "related": ["plan-old"],
                "evidence": ["docs/memory/mem-legacy.md"],
            },
        )

        code, out, err = self.run_cli("memory", "list", "--json")

        self.assertEqual(code, 0, err)
        memory = json.loads(out)["data"]["memories"][0]
        self.assertEqual(memory["id"], "mem-legacy")
        self.assertEqual(memory["status"], "active")
        self.assertEqual(memory["tags"], [])
        self.assertEqual(memory["related_plan_ids"], [])
        self.assertEqual(memory["related_audit_ids"], [])
        self.assertEqual(memory["related_drift_ids"], [])
        self.assertEqual(memory["superseded_by"], "")

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

    def test_drift_analyze_json_returns_quality_signal_metadata(self) -> None:
        drift_source = self.root / "drift-quality.txt"
        drift_source.write_text(
            "Imported a remote database dependency even though the plan said no external database.\n",
            encoding="utf-8",
        )

        code, out, err = self.run_cli(
            "drift",
            "analyze",
            "--id",
            "drift-quality-001",
            "--source",
            str(drift_source),
            "--evidence",
            "drift-quality.txt",
            "--json",
        )

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        finding = payload["data"]["drift_report"]["findings"][0]
        self.assertEqual(finding["type"], "dependency_drift")
        self.assertEqual(finding["severity"], "high")
        self.assertEqual(finding["confidence"], "high")
        self.assertEqual(finding["rule_id"], "dependency_drift")
        self.assertEqual(finding["evidence_path"], "drift-quality.txt")
        self.assertEqual(finding["matched_span"]["text"], "database")
        self.assertIn("remote database dependency", finding["source_excerpt"])
        self.assertIn("Review plan non-goals", finding["recommendation"])

    def test_drift_report_legacy_findings_remain_readable(self) -> None:
        with Chdir(self.root):
            write_json(
                drift_json_path("drift-legacy"),
                {
                    "schema_version": "1",
                    "id": "drift-legacy",
                    "source": "legacy.txt",
                    "findings": [
                        {
                            "type": "dependency_drift",
                            "evidence": "matched keywords: database",
                            "recommendation": "Review dependency drift.",
                        }
                    ],
                    "evidence": [],
                    "follow_ups": [],
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                    "doc_path": "",
                },
            )

        code, out, err = self.run_cli("drift", "analyze", "--id", "drift-new", "--source", __file__, "--json")
        self.assertEqual(code, 0, err)

        legacy_data = json.loads((self.root / ".abh" / "drift" / "drift-legacy.json").read_text(encoding="utf-8"))
        legacy_report = DriftReport.from_dict(legacy_data)
        finding = legacy_report.to_dict()["findings"][0]
        self.assertEqual(finding["type"], "dependency_drift")
        self.assertEqual(finding["severity"], "unknown")
        self.assertEqual(finding["confidence"], "unknown")

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

    def test_doctor_reports_roadmap_queue_preassigned_plan_ids(self) -> None:
        queue = self.root / ".abh" / "roadmap.json"
        queue.parent.mkdir(parents=True, exist_ok=True)
        queue.write_text(
            json.dumps(
                {
                    "schema_version": "1",
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
                    "schema_version": "1",
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

    def test_save_plan_markdown_uses_shared_atomic_text_writer(self) -> None:
        with patch("abh.plans.write_text", wraps=storage.write_text) as text_writer:
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

        written_paths = [call.args[0].resolve() for call in text_writer.call_args_list]
        self.assertIn((self.root / "docs" / "plans" / "plan-atomic-doc.md").resolve(), written_paths)

    def test_write_json_serializes_concurrent_same_file_writes_and_cleans_locks(self) -> None:
        path = self.root / ".abh" / "plans" / "plan-concurrent.json"
        errors: list[BaseException] = []

        def writer(index: int) -> None:
            try:
                write_json(path, {"schema_version": "1", "index": index})
            except BaseException as exc:
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(index,)) for index in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "1")
        self.assertIn(payload["index"], range(8))
        self.assertEqual(list(path.parent.glob("*.tmp")), [])
        self.assertFalse(path.with_suffix(path.suffix + ".lock").exists())

    def test_core_read_commands_support_json_output(self) -> None:
        self.run_cli("init", "--write", "--confirm", "--json")
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
            (("agent", "setup", "codex", "--json"), "setup"),
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
            self.assertEqual(record.to_dict()["schema_version"], "1")

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

        report = json.loads((self.root / ".abh" / "drift" / "drift-plan-001.json").read_text(encoding="utf-8"))
        finding = next(item for item in report["findings"] if item["rule_id"] == "plan_non_goal:plan-drift-baseline")
        self.assertEqual(finding["severity"], "high")
        self.assertEqual(finding["confidence"], "high")
        self.assertEqual(finding["evidence_path"], str(drift_source))


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
        self.assertIn("abh_attractor_list", tool_names)
        self.assertIn("abh_attractor_show", tool_names)
        self.assertIn("abh_attractor_active", tool_names)
        self.assertIn("abh_roadmap_list", tool_names)
        self.assertIn("abh_roadmap_next_id", tool_names)
        self.assertIn("abh_roadmap_check", tool_names)
        self.assertIn("abh_close_plan", tool_names)
        for tool in tools:
            self.assertEqual(tool["inputSchema"]["type"], "object")
        readonly = {tool["name"]: tool["annotations"]["readOnlyHint"] for tool in tools}
        self.assertTrue(readonly["abh_plan_list"])
        self.assertTrue(readonly["abh_attractor_active"])
        self.assertTrue(readonly["abh_roadmap_list"])
        self.assertTrue(readonly["abh_roadmap_next_id"])
        self.assertTrue(readonly["abh_roadmap_check"])
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
        self.assertIn("verification_summary", envelope["data"])
        self.assertEqual(envelope["data"]["verification_summary"]["latest_id"], None)
        self.assertEqual(envelope["data"]["verification_summary"]["reasons"], ["no_verification_runs"])

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

    def test_mcp_attractor_read_tools_return_registry_data(self) -> None:
        code, out, err = self.run_cli(
            "attractor",
            "create",
            "--id",
            "attractor-mcp",
            "--title",
            "MCP Attractor",
            "--version",
            "1.0.0",
            "--path",
            "docs/architecture/attractors/mcp.md",
            "--intent",
            "MCP can read active attractor.",
        )
        self.assertEqual(code, 0, err)

        active_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 18,
                "method": "tools/call",
                "params": {"name": "abh_attractor_active", "arguments": {}},
            }
        )
        active = active_response["result"]["structuredContent"]["data"]["attractor"]
        self.assertEqual(active["id"], "attractor-mcp")

        show_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 19,
                "method": "tools/call",
                "params": {"name": "abh_attractor_show", "arguments": {"attractor_id": "attractor-mcp"}},
            }
        )
        self.assertEqual(show_response["result"]["structuredContent"]["data"]["attractor"]["path"], "docs/architecture/attractors/mcp.md")

        list_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 20,
                "method": "tools/call",
                "params": {"name": "abh_attractor_list", "arguments": {}},
            }
        )
        self.assertEqual(list_response["result"]["structuredContent"]["data"]["total"], 1)

    def test_mcp_roadmap_read_tools_return_queue_data(self) -> None:
        with Chdir(self.root):
            write_json(
                self.root / ".abh" / "roadmap.json",
                RoadmapQueue(
                    items=[
                        RoadmapItem(
                            key="stage4.mcp-roadmap",
                            title="MCP Roadmap",
                            stage="stage4",
                            summary="MCP reads roadmap queue.",
                        )
                    ]
                ).to_dict(),
            )

        list_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 21,
                "method": "tools/call",
                "params": {"name": "abh_roadmap_list", "arguments": {}},
            }
        )
        list_envelope = list_response["result"]["structuredContent"]
        self.assertTrue(list_envelope["ok"])
        self.assertEqual(list_envelope["data"]["items"][0]["key"], "stage4.mcp-roadmap")

        next_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 22,
                "method": "tools/call",
                "params": {"name": "abh_roadmap_next_id", "arguments": {}},
            }
        )
        next_envelope = next_response["result"]["structuredContent"]
        self.assertEqual(next_envelope["data"]["next_plan_id"], "plan-001")

        check_response = self.call_mcp(
            {
                "jsonrpc": "2.0",
                "id": 23,
                "method": "tools/call",
                "params": {"name": "abh_roadmap_check", "arguments": {}},
            }
        )
        self.assertEqual(check_response["result"]["structuredContent"]["data"]["issues"], [])

    def test_mcp_drift_list_reads_existing_reports_without_writing(self) -> None:
        with Chdir(self.root):
            write_json(
                drift_json_path("drift-mcp-existing"),
                {
                    "schema_version": "1",
                    "id": "drift-mcp-existing",
                    "source": "source.txt",
                    "findings": [
                        {
                            "type": "dependency_drift",
                            "evidence": "matched keywords: database",
                            "recommendation": "Review dependency drift.",
                        }
                    ],
                    "evidence": [],
                    "follow_ups": [],
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                    "doc_path": "",
                },
            )

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
        finding = envelope["data"]["drift_reports"][0]["findings"][0]
        self.assertEqual(finding["severity"], "unknown")
        self.assertEqual(finding["confidence"], "unknown")

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
                        "command": "unit tests pass",
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
                        "auditor_context": "independent MCP write-flow reviewer",
                        "independence": "independent",
                        "verification_id": verification["id"],
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
                        "tags": ["mcp", "quality-signal"],
                        "status": "active",
                        "related_plan_ids": ["plan-mcp-write"],
                        "related_audit_ids": ["audit-mcp-write"],
                        "related_drift_ids": ["drift-mcp-write"],
                        "superseded_by": "mem-mcp-write-v2",
                    },
                },
            }
        )
        memory = memory_response["result"]["structuredContent"]["data"]["memory"]
        self.assertEqual(memory["id"], "mem-mcp-write")
        self.assertEqual(memory["tags"], ["mcp", "quality-signal"])
        self.assertEqual(memory["related_plan_ids"], ["plan-mcp-write"])
        self.assertEqual(memory["related_audit_ids"], ["audit-mcp-write"])
        self.assertEqual(memory["related_drift_ids"], ["drift-mcp-write"])
        self.assertEqual(memory["superseded_by"], "mem-mcp-write-v2")
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
        finding = envelope["data"]["drift_report"]["findings"][0]
        self.assertEqual(finding["severity"], "high")
        self.assertEqual(finding["confidence"], "high")
        self.assertIn("source_excerpt", finding)
        self.assertTrue((self.root / ".abh" / "drift" / "drift-mcp-write.json").exists())
