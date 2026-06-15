from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
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
from abh.models import validate_record_schema
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

    def test_codex_status_json_reports_disabled_when_no_config_exists(self) -> None:
        code, out, err = self.run_cli("codex", "status", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "codex status")
        codex = payload["data"]["codex"]
        self.assertFalse(codex["enabled"])
        self.assertEqual(codex["path"], ".codex/config.toml")
        self.assertEqual(codex["mode"], "status")
        self.assertFalse((self.root / ".codex" / "config.toml").exists())

    def test_codex_on_json_previews_managed_write_without_creating_files(self) -> None:
        code, out, err = self.run_cli("codex", "on", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "codex on")
        codex = payload["data"]["codex"]
        self.assertEqual(codex["mode"], "preview")
        self.assertFalse(codex["write"])
        self.assertFalse(codex["confirmed"])
        self.assertEqual(codex["path"], ".codex/config.toml")
        self.assertEqual(codex["writes"][0]["path"], ".codex/config.toml")
        self.assertEqual(codex["blockers"], [])
        self.assertFalse((self.root / ".codex" / "config.toml").exists())

    def test_codex_on_write_requires_confirm(self) -> None:
        code, out, err = self.run_cli("codex", "on", "--write", "--json")

        self.assertEqual(code, 2)
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertIn("--confirm", payload["errors"][0]["message"])
        self.assertFalse((self.root / ".codex" / "config.toml").exists())

    def test_codex_on_write_confirm_creates_managed_config(self) -> None:
        code, out, err = self.run_cli("codex", "on", "--write", "--confirm", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "codex on")
        codex = payload["data"]["codex"]
        self.assertEqual(codex["mode"], "write")
        self.assertTrue(codex["write"])
        self.assertTrue(codex["confirmed"])
        config_path = self.root / ".codex" / "config.toml"
        self.assertTrue(config_path.exists())
        content = config_path.read_text(encoding="utf-8")
        self.assertIn("ABH MANAGED CODEX CONFIG", content)
        self.assertIn("developer_instructions", content)
        self.assertIn("abh onboarding check --json", content)
        self.assertIn("abh next --json", content)
        self.assertIn("abh doctor --json", content)
        self.assertIn("abh roadmap check --json", content)

    def test_codex_status_json_reports_enabled_after_managed_write(self) -> None:
        code, out, err = self.run_cli("codex", "on", "--write", "--confirm", "--json")
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("codex", "status", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "codex status")
        codex = payload["data"]["codex"]
        self.assertTrue(codex["enabled"])
        self.assertTrue(codex["managed"])
        self.assertEqual(codex["state"], "managed")
        self.assertEqual(codex["path"], ".codex/config.toml")
        self.assertEqual(codex["mode"], "status")

    def test_codex_on_does_not_overwrite_unmanaged_config(self) -> None:
        config_path = self.root / ".codex" / "config.toml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("model = \"gpt-5\"\n", encoding="utf-8")

        code, out, err = self.run_cli("codex", "on", "--write", "--confirm", "--json")

        self.assertEqual(code, 2)
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertIn("existing unmanaged Codex config", payload["errors"][0]["message"])
        self.assertEqual(config_path.read_text(encoding="utf-8"), "model = \"gpt-5\"\n")

    def test_codex_off_json_previews_removal_when_managed_config_exists(self) -> None:
        self.run_cli("codex", "on", "--write", "--confirm", "--json")

        code, out, err = self.run_cli("codex", "off", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "codex off")
        codex = payload["data"]["codex"]
        self.assertEqual(codex["mode"], "preview")
        self.assertEqual(codex["writes"][0]["path"], ".codex/config.toml")
        self.assertTrue((self.root / ".codex" / "config.toml").exists())

    def test_codex_off_write_requires_confirm(self) -> None:
        self.run_cli("codex", "on", "--write", "--confirm", "--json")

        code, out, err = self.run_cli("codex", "off", "--write", "--json")

        self.assertEqual(code, 2)
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertIn("--confirm", payload["errors"][0]["message"])
        self.assertTrue((self.root / ".codex" / "config.toml").exists())

    def test_codex_off_write_confirm_removes_managed_config(self) -> None:
        self.run_cli("codex", "on", "--write", "--confirm", "--json")

        code, out, err = self.run_cli("codex", "off", "--write", "--confirm", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "codex off")
        codex = payload["data"]["codex"]
        self.assertEqual(codex["mode"], "write")
        self.assertTrue(codex["write"])
        self.assertTrue(codex["confirmed"])
        self.assertFalse((self.root / ".codex" / "config.toml").exists())

    def test_codex_off_does_not_remove_unmanaged_config(self) -> None:
        config_path = self.root / ".codex" / "config.toml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("model = \"gpt-5\"\n", encoding="utf-8")

        code, out, err = self.run_cli("codex", "off", "--write", "--confirm", "--json")

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        codex = payload["data"]["codex"]
        self.assertFalse(codex["enabled"])
        self.assertEqual(codex["blockers"][0]["reason"], "existing unmanaged Codex config; will not remove")
        self.assertTrue(config_path.exists())
        self.assertEqual(config_path.read_text(encoding="utf-8"), "model = \"gpt-5\"\n")

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

    def test_plan_record_legacy_reads_commitment_phase_state_defaults(self) -> None:
        plan = PlanRecord.from_dict(
            {
                "id": "plan-legacy-commitment",
                "title": "Legacy Commitment",
                "attractor": "docs/architecture/attractors/abh-core-attractor.md",
                "baseline": "baseline",
            }
        )

        self.assertEqual(
            plan.to_dict()["commitment_phase_state"],
            {
                "stable_state_now": [],
                "active_change_pressure": [],
                "target_stable_state": [],
                "conversion_proof": [],
                "residual_pressure": [],
            },
        )

    def test_plan_status_json_exposes_commitment_phase_state(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-116-commitment-phase-state",
            "--title",
            "Commitment Phase State",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--goal",
            "express stable commitments",
            "--non-goal",
            "infer commitments automatically",
            "--exit-criterion",
            "json exposes commitment phase state",
            "--validation",
            "python3 -m abh doctor",
            "--closure-evidence",
            "docs/plans/plan-116-commitment-phase-state.md",
            "--stable-state-now",
            "Current CLI loop is stable.",
            "--active-change-pressure",
            "Need to convert implicit commitments into explicit fields.",
            "--target-stable-state",
            "Plans expose stable commitments explicitly.",
            "--conversion-proof",
            "Plan status JSON shows commitment phase state.",
            "--residual-pressure",
            "Owner-doc follow-up|Non-blocking until later Stage 6 slice.",
            "--json",
        )
        self.assertEqual(code, 0, err)

        payload = json.loads(out)
        commitment = payload["data"]["plan"]["commitment_phase_state"]
        self.assertEqual(commitment["stable_state_now"], ["Current CLI loop is stable."])
        self.assertEqual(commitment["active_change_pressure"], ["Need to convert implicit commitments into explicit fields."])
        self.assertEqual(commitment["target_stable_state"], ["Plans expose stable commitments explicitly."])
        self.assertEqual(commitment["conversion_proof"], ["Plan status JSON shows commitment phase state."])
        self.assertEqual(
            commitment["residual_pressure"],
            [
                {
                    "pressure": "Owner-doc follow-up",
                    "non_blocking_rationale": "Non-blocking until later Stage 6 slice.",
                }
            ],
        )

        code, out, err = self.run_cli("plan", "status", "plan-116-commitment-phase-state", "--json")
        self.assertEqual(code, 0, err)
        commitment = json.loads(out)["data"]["plan"]["commitment_phase_state"]
        self.assertEqual(commitment["stable_state_now"], ["Current CLI loop is stable."])

    def test_plan_update_appends_commitment_phase_state_and_renders_markdown(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-117-commitment-update",
            "--title",
            "Commitment Update",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--goal",
            "track commitment transitions",
            "--non-goal",
            "infer commitments automatically",
            "--exit-criterion",
            "markdown shows commitment phase state",
            "--validation",
            "python3 -m abh doctor",
            "--closure-evidence",
            "docs/plans/plan-117-commitment-update.md",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli(
            "plan",
            "update",
            "plan-117-commitment-update",
            "--stable-state-now",
            "Current release loop is stable.",
            "--active-change-pressure",
            "Need explicit commitment tracking.",
            "--target-stable-state",
            "Stable commitments are encoded in plan state.",
            "--conversion-proof",
            "JSON and Markdown both show commitment phase state.",
            "--residual-pressure",
            "Owner-doc alignment|Non-blocking until later owner-doc slice.",
            "--json",
        )
        self.assertEqual(code, 0, err)

        plan = json.loads(out)["data"]["plan"]
        self.assertEqual(plan["commitment_phase_state"]["active_change_pressure"], ["Need explicit commitment tracking."])

        doc = (self.root / "docs" / "plans" / "plan-117-commitment-update.md").read_text(encoding="utf-8")
        self.assertIn("## Commitment Phase State", doc)
        self.assertIn("- Current release loop is stable.", doc)
        self.assertIn("- Need explicit commitment tracking.", doc)
        self.assertIn("- Stable commitments are encoded in plan state.", doc)
        self.assertIn("- JSON and Markdown both show commitment phase state.", doc)
        self.assertIn("Owner-doc alignment", doc)
        self.assertIn("Non-blocking until later owner-doc slice.", doc)

    def test_plan_status_json_does_not_mark_commitment_phase_state_updates_stale(self) -> None:
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-118-commitment-stale",
            "--title",
            "Commitment Stale",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "keep close gate unchanged",
            "--non-goal",
            "change close semantics",
            "--exit-criterion",
            "commitment updates stay non-blocking",
            "--validation",
            f'"{sys.executable}" -c "print(\'commitment-stale\')"',
            "--closure-evidence",
            "docs/plans/plan-118-commitment-stale.md",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("verify", "run", "plan-118-commitment-stale", "--json")
        self.assertEqual(code, 0, err)
        verification_id = json.loads(out)["data"]["verification"]["id"]

        code, out, err = self.run_cli(
            "plan",
            "update",
            "plan-118-commitment-stale",
            "--stable-state-now",
            "Current release loop is stable.",
            "--json",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli("plan", "status", "plan-118-commitment-stale", "--json")
        self.assertEqual(code, 0, err)
        summary = json.loads(out)["data"]["verification_summary"]
        self.assertEqual(summary["latest_id"], verification_id)
        self.assertFalse(summary["stale"])
        self.assertNotIn("plan_updated_after_verification", summary["reasons"])
        self.assertNotIn("validation_checklist_changed", summary["reasons"])

    def test_plan_template_documents_commitment_phase_state(self) -> None:
        template = (Path(__file__).resolve().parents[1] / "docs" / "plans" / "templates" / "plan-template.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Commitment Phase State", template)
        self.assertIn("stable state", template)
        self.assertIn("active pressure", template)
        self.assertIn("target state", template)
        self.assertIn("conversion proof", template)
        self.assertIn("residual pressure", template)

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

    # ── Reference Set tests ──

    def test_plan_status_json_includes_reference_set_legacy_defaults(self) -> None:
        (self.root / ".abh" / "plans").mkdir(parents=True, exist_ok=True)
        write_json(
            self.root / ".abh" / "plans" / "plan-109-legacy-reference.json",
            {
                "schema_version": "2",
                "id": "plan-109-legacy-reference",
                "title": "Legacy Reference",
                "attractor": "docs/architecture/attractors/abh-core-attractor.md",
                "baseline": "baseline",
                "owner": "platform",
                "status": "draft",
                "goals": ["goal"],
                "non_goals": ["non-goal"],
                "exit_criteria": ["exit"],
                "validation_checklist": ["python3 -m abh doctor"],
                "closure_evidence": ["tests/test_cli.py"],
                "verification_runs": [],
                "audit_ids": [],
            },
        )
        code, out, err = self.run_cli("plan", "status", "plan-109-legacy-reference", "--json")
        self.assertEqual(code, 0, err)
        reference_set = json.loads(out)["data"]["plan"]["reference_set"]
        self.assertEqual(
            reference_set,
            {
                "context_routing": [],
                "active_owner_docs": [],
                "live_code_routes": [],
                "tests_baseline": [],
                "known_issues": [],
                "external_contracts": [],
                "plan_audit_evidence": [],
            },
        )

    def test_plan_create_and_update_reference_set_json_and_markdown(self) -> None:
        code, out, err = self.run_cli(
            "plan", "create",
            "--id", "plan-110-reference-set",
            "--title", "Reference Set",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
            "--goal", "bind context",
            "--non-goal", "mandatory policy",
            "--exit-criterion", "reference set is visible",
            "--validation", "python3 -m abh doctor",
            "--closure-evidence", "tests/test_cli.py",
            "--reference-set", "active_owner_docs=docs/context/source-of-truth.md",
            "--reference-set", "live_code_routes=abh/plans.py",
            "--reference-set", "tests_baseline=tests/test_cli.py",
        )
        self.assertEqual(code, 0, err)

        code, out, err = self.run_cli(
            "plan", "update", "plan-110-reference-set",
            "--reference-set", "known_issues=mem-post-close-doc-sync-001",
            "--reference-set", "plan_audit_evidence=docs/audits/audit-042-project-health-report.md",
            "--json",
        )
        self.assertEqual(code, 0, err)
        plan = json.loads(out)["data"]["plan"]
        self.assertEqual(plan["reference_set"]["active_owner_docs"], ["docs/context/source-of-truth.md"])
        self.assertEqual(plan["reference_set"]["live_code_routes"], ["abh/plans.py"])
        self.assertEqual(plan["reference_set"]["tests_baseline"], ["tests/test_cli.py"])
        self.assertEqual(plan["reference_set"]["known_issues"], ["mem-post-close-doc-sync-001"])
        self.assertEqual(plan["reference_set"]["plan_audit_evidence"], ["docs/audits/audit-042-project-health-report.md"])

        doc = (self.root / "docs" / "plans" / "plan-110-reference-set.md").read_text(encoding="utf-8")
        self.assertIn("## Reference Set", doc)
        self.assertIn("### Active Owner Docs", doc)
        self.assertIn("- docs/context/source-of-truth.md", doc)
        self.assertIn("### Live Code Routes", doc)
        self.assertIn("- abh/plans.py", doc)
        self.assertIn("### Known Issues", doc)
        self.assertIn("- mem-post-close-doc-sync-001", doc)

    def test_plan_reference_set_rejects_unknown_keys(self) -> None:
        code, out, err = self.run_cli(
            "plan", "create",
            "--id", "plan-111-bad-reference",
            "--title", "Bad Reference",
            "--attractor", "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline", "baseline",
            "--reference-set", "random_key=docs/context/source-of-truth.md",
        )
        self.assertNotEqual(code, 0)
        self.assertIn("invalid reference set key", err)

    def test_roadmap_materialize_carries_reference_set(self) -> None:
        (self.root / ".abh").mkdir(parents=True, exist_ok=True)
        write_json(
            self.root / ".abh" / "roadmap.json",
            {
                "schema_version": "2",
                "items": [
                    {
                        "key": "stage6.reference-alpha",
                        "title": "Reference Alpha",
                        "stage": "stage6",
                        "summary": "Reference alpha",
                        "attractor": "docs/architecture/attractors/abh-core-attractor.md",
                        "baseline": "baseline",
                        "goals": ["goal"],
                        "non_goals": ["non-goal"],
                        "exit_criteria": ["exit"],
                        "validation_checklist": ["python3 -m abh doctor"],
                        "closure_evidence": ["tests/test_cli.py"],
                        "reference_set": {
                            "active_owner_docs": ["docs/context/source-of-truth.md"],
                            "live_code_routes": ["abh/roadmap.py"],
                        },
                        "status": "queued",
                        "plan_id": None,
                    }
                ],
            },
        )
        code, out, err = self.run_cli("roadmap", "materialize", "stage6.reference-alpha", "--json")
        self.assertEqual(code, 0, err)
        plan = json.loads(out)["data"]["plan"]
        self.assertEqual(plan["reference_set"]["active_owner_docs"], ["docs/context/source-of-truth.md"])
        self.assertEqual(plan["reference_set"]["live_code_routes"], ["abh/roadmap.py"])
