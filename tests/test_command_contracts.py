from __future__ import annotations

import json
from pathlib import Path

from abh import audits, plans, verifications
from abh.core import (
    close_plan,
    create_plan,
    record_audit,
    request_audit,
    run_verification,
    transition_plan,
    update_plan_record,
)
from tests.support import WorkspaceCliTestCase


class CommandContractTests(WorkspaceCliTestCase):
    def test_owner_docs_expose_stable_commitment_sections(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        required_sections = (
            "## Stable Commitments",
            "## Allowed Variation",
            "## Drift / Leakage Signals",
            "## Correction Path",
        )
        owner_docs = (
            repo / "docs" / "index.md",
            repo / "docs" / "context" / "source-of-truth.md",
            repo / "docs" / "context" / "project-context.md",
            repo / "docs" / "context" / "codebase-map.md",
            repo / "docs" / "architecture" / "templates" / "attractor-template.md",
        )

        for path in owner_docs:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                for section in required_sections:
                    self.assertIn(section, text)

        index = (repo / "docs" / "index.md").read_text(encoding="utf-8")
        source_of_truth = (repo / "docs" / "context" / "source-of-truth.md").read_text(encoding="utf-8")
        for phrase in (
            "plan scoping",
            "semantic conservation audit",
            "health or drift review",
            "owner-doc conflict resolution",
        ):
            self.assertIn(phrase, index)
            self.assertIn(phrase, source_of_truth)

        quality_signals = (repo / "docs" / "architecture" / "quality-signals.md").read_text(encoding="utf-8")
        self.assertIn("Owner Doc Stable Commitments", quality_signals)
        self.assertIn("future health and drift checks", quality_signals)
        for section in required_sections:
            self.assertIn(section.removeprefix("## "), quality_signals)

    def test_init_seed_owner_docs_expose_stable_commitment_sections(self) -> None:
        from abh.init import planned_init_actions

        required_sections = (
            "## Stable Commitments",
            "## Allowed Variation",
            "## Drift / Leakage Signals",
            "## Correction Path",
        )
        action_content = {action.path: action.content for action in planned_init_actions(self.root)}
        seed_docs = (
            "docs/index.md",
            "docs/context/source-of-truth.md",
            "docs/context/project-context.md",
            "docs/context/codebase-map.md",
            "docs/architecture/attractors/abh-core-attractor.md",
        )

        for path in seed_docs:
            with self.subTest(path=path):
                text = action_content[path]
                for section in required_sections:
                    self.assertIn(section, text)

    def test_codebase_map_describes_split_test_surface(self) -> None:
        codebase_map = (Path(__file__).resolve().parents[1] / "docs" / "context" / "codebase-map.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("`tests/test_cli.py` is now the thin end-to-end CLI regression layer", codebase_map)
        self.assertIn("init/setup/hooks/attractor/plan smoke coverage", codebase_map)
        self.assertIn("`tests/test_verifications_and_audits.py` covers verification runner behavior", codebase_map)
        self.assertIn("`tests/test_memory_drift_reporting.py` covers memory indexing, route/drift behavior, and health-report aggregation", codebase_map)
        self.assertIn("`tests/test_command_contracts.py` covers shared command-contract metadata", codebase_map)

    def test_cli_module_is_limited_to_e2e_cli_smoke_scope(self) -> None:
        cli_tests = (Path(__file__).resolve().parents[1] / "tests" / "test_cli.py").read_text(encoding="utf-8")

        self.assertIn("def test_init_preview_is_machine_readable_and_does_not_write", cli_tests)
        self.assertIn("def test_hooks_install_write_confirm_creates_executable_managed_hook", cli_tests)
        self.assertIn("def test_attractor_create_active_show_list_and_supersede_json_flow", cli_tests)
        self.assertIn("def test_plan_create_status_transition_and_verify", cli_tests)
        self.assertNotIn("def test_verify_run_executes_validation_checklist_and_records_pass", cli_tests)
        self.assertNotIn("def test_audit_record_allows_close_only_after_pass", cli_tests)
        self.assertNotIn("def test_memory_add_and_search_by_type_and_keyword", cli_tests)
        self.assertNotIn("def test_route_recommends_reading_order_for_close_question", cli_tests)
        self.assertNotIn("def test_report_health_json_empty_workspace", cli_tests)

    def test_ci_workflow_runs_full_abh_pull_request_checks(self) -> None:
        workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )

        for command in (
            "python3 -m pip install -e .",
            "python3 -m unittest discover -v",
            "python3 -m abh doctor --json",
            "python3 -m abh roadmap check --json",
            "git diff --check",
            "python3 -m abh report health --json",
        ):
            self.assertIn(command, workflow)
        self.assertNotIn("python3 -m unittest tests/test_cli.py -v", workflow)

    def test_ci_docs_define_gating_and_informational_boundary(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        readme = (repo / "README.md").read_text(encoding="utf-8")
        recipe = (repo / "docs" / "recipes" / "ci.md").read_text(encoding="utf-8")

        for text in (readme, recipe):
            self.assertIn("Gating checks", text)
            self.assertIn("Informational checks", text)
            self.assertIn("`python3 -m abh report health --json` is informational", text)
            self.assertIn("does not fail solely because historical semantic pressure exists", text)

    def test_readme_exposes_zero_python_skill_onboarding(self) -> None:
        readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

        self.assertIn("## 零基础使用：不装 Python", readme)
        self.assertIn("powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"", readme)
        self.assertIn("curl -LsSf https://astral.sh/uv/install.sh | sh", readme)
        self.assertIn("uvx --from git+https://github.com/worm-ai/harness-before.git abh --help", readme)
        self.assertIn("uv tool install --from git+https://github.com/worm-ai/harness-before.git abh", readme)
        self.assertIn("Use the skill at `skills/abh-workflow`", readme)
        self.assertIn("不需要自己写 plan、verification、audit 命令", readme)

    def test_readme_documents_codex_toggle_commands(self) -> None:
        readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

        self.assertIn("abh codex on --write --confirm --json", readme)
        self.assertIn("abh codex off --write --confirm --json", readme)
        self.assertIn("abh codex status --json", readme)

    def test_codex_recipe_mentions_managed_repo_config_toggle(self) -> None:
        recipe = (Path(__file__).resolve().parents[1] / "docs" / "recipes" / "codex.md").read_text(encoding="utf-8")

        self.assertIn(".codex/config.toml", recipe)
        self.assertIn("abh codex on --write --confirm --json", recipe)
        self.assertIn("abh codex off --write --confirm --json", recipe)
        self.assertIn("ABH-managed", recipe)

    def test_stage7_docs_reconcile_ci_boundary_blocked_sharing_and_skill_slice(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        roadmap = (repo / "docs" / "development-roadmap.md").read_text(encoding="utf-8")
        task_board = (repo / "docs" / "task-board.md").read_text(encoding="utf-8")
        codebase_map = (repo / "docs" / "context" / "codebase-map.md").read_text(encoding="utf-8")
        skill = (repo / "skills" / "abh-workflow" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Stage 7 CI drift boundary", roadmap)
        self.assertIn("roadmap consistency, whitespace drift, and read-only health posture", roadmap)
        self.assertIn("does not run standalone `abh drift analyze`", roadmap)
        self.assertIn("Current focus: `plan-057-codex-repo-toggle`; next queue: `stage7.team-policy-and-release-automation`", task_board)
        self.assertIn("`stage7.multi-repo-sharing` -> `plan-054-multi-repo-sharing`（blocked/deferred）", task_board)
        self.assertIn("`adoption.abh-workflow-skill` -> `plan-055-abh-workflow-skill`（closed）", task_board)
        self.assertIn("Stage 7 completed slice: `plan-053-ci-templates`", codebase_map)
        self.assertIn("`plan-054-multi-repo-sharing` is blocked/deferred", codebase_map)
        self.assertIn("`plan-055-abh-workflow-skill` is closed", codebase_map)
        self.assertIn("`plan-057-codex-repo-toggle` is the current open plan", codebase_map)
        self.assertIn("name: abh-workflow", skill)
        self.assertIn("Use when the user asks to manage a task with ABH", skill)
        self.assertIn("must not self-sign independent audit", skill)

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

        codex_status = command_contract("codex.status")
        self.assertEqual(codex_status.cli_command, "codex status")
        self.assertTrue(codex_status.read_only)
        self.assertEqual(codex_status.confirmation, "none")
        self.assertEqual(codex_status.side_effects, [])
        self.assertEqual(codex_status.output_keys, ["codex"])

        codex_on = command_contract("codex.on")
        self.assertEqual(codex_on.cli_command, "codex on")
        self.assertFalse(codex_on.read_only)
        self.assertEqual(codex_on.confirmation, "--write --confirm")
        self.assertIn("write", codex_on.input_schema["properties"])
        self.assertIn("confirm", codex_on.input_schema["properties"])
        self.assertIn("write .codex/config.toml", codex_on.side_effects)

        codex_off = command_contract("codex.off")
        self.assertEqual(codex_off.cli_command, "codex off")
        self.assertFalse(codex_off.read_only)
        self.assertEqual(codex_off.confirmation, "--write --confirm")
        self.assertIn("write", codex_off.input_schema["properties"])
        self.assertIn("confirm", codex_off.input_schema["properties"])
        self.assertIn("write .codex/config.toml", codex_off.side_effects)

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

        health_report = command_contract("report.health")
        self.assertEqual(health_report.cli_command, "report health")
        self.assertEqual(health_report.mcp_tool, "abh_report_health")
        self.assertTrue(health_report.read_only)
        self.assertEqual(health_report.confirmation, "none")
        self.assertEqual(health_report.side_effects, [])
        self.assertEqual(health_report.output_keys, ["health_report"])

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
        self.assertEqual(envelope["schema_version"], "2")
        self.assertTrue(envelope["ok"])
        self.assertEqual(envelope["command"], "plan.status")

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
        self.assertEqual(payload["schema_version"], "2")
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
        self.assertEqual(payload["schema_version"], "2")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["command"], "plan status")
        self.assertEqual(payload["data"], {})
        self.assertEqual(payload["errors"][0]["code"], "abh_error")
        self.assertEqual(payload["errors"][0]["category"], "not_found")
        self.assertEqual(payload["errors"][0]["message"], "plan not found: missing-plan")

    def test_core_read_commands_support_json_output(self) -> None:
        self.run_cli("init", "--write", "--confirm", "--json")
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-json-contract",
            "--title",
            "JSON Contract Plan",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "exercise core JSON read commands",
            "--non-goal",
            "write flow coverage",
            "--exit-criterion",
            "read commands emit envelopes",
            "--validation",
            "unit tests pass",
            "--closure-evidence",
            "tests/test_command_contracts.py",
        )
        self.assertEqual(code, 0, err)
        self.run_cli(
            "audit", "request",
            "plan-json-contract",
            "--id", "audit-json-contract",
            "--auditor", "reviewer",
            "--scope", "json contract",
            "--evidence", "tests/test_command_contracts.py",
        )
        self.run_cli(
            "memory", "add",
            "--id", "mem-json-contract",
            "--type", "false_assumption",
            "--summary", "json contract memory",
            "--context", "testing json",
            "--implication", "agents can parse memory",
            "--evidence", "tests/test_command_contracts.py",
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
