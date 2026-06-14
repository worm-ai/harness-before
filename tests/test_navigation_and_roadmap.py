from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

from tests.support import WorkspaceCliTestCase


class NavigationAndRoadmapTests(WorkspaceCliTestCase):
    def test_next_json_recommends_materializing_next_queued_item_when_no_open_plans(self) -> None:
        self.run_cli("init", "--write", "--confirm", "--json")
        queue = self.root / ".abh" / "roadmap.json"
        queue.write_text(
            json.dumps(
                {
                    "schema_version": "2",
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

    def test_next_json_skips_blocked_plan_for_queued_roadmap_item(self) -> None:
        self.run_cli("init", "--write", "--confirm", "--json")
        code, out, err = self.run_cli(
            "plan",
            "create",
            "--id",
            "plan-201-deferred",
            "--title",
            "Deferred Plan",
            "--attractor",
            "docs/architecture/attractors/abh-core-attractor.md",
            "--baseline",
            "baseline",
            "--status",
            "ready",
            "--goal",
            "defer old work",
            "--non-goal",
            "block queued roadmap",
            "--exit-criterion",
            "blocked plan is skipped by next",
            "--validation",
            "python3 -m abh doctor",
            "--closure-evidence",
            "docs/plans/plan-201-deferred.md",
        )
        self.assertEqual(code, 0, err)
        code, out, err = self.run_cli("plan", "transition", "plan-201-deferred", "--to", "blocked")
        self.assertEqual(code, 0, err)
        queue = self.root / ".abh" / "roadmap.json"
        queue.write_text(
            json.dumps(
                {
                    "schema_version": "2",
                    "items": [
                        {
                            "key": "stage6.repository-write-transaction-boundary",
                            "title": "Repository Write Transaction Boundary",
                            "stage": "stage6",
                            "summary": "Unify JSON and Markdown write boundaries.",
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
        result = json.loads(out)["data"]["next"]
        self.assertEqual(result["next_action"], "materialize_roadmap_item")
        self.assertEqual(result["recommended_command"], "abh roadmap materialize stage6.repository-write-transaction-boundary --json")
        self.assertIn("no active open plans", result["rationale"])
        self.assertEqual(result["source"]["roadmap_key"], "stage6.repository-write-transaction-boundary")
        self.assertEqual(result["source"]["blocked_plan_ids"], ["plan-201-deferred"])

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
        command = f'"{sys.executable}" -c "print(\'verified\')"'
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
            command,
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

    def test_roadmap_next_id_list_and_materialize_queue_item(self) -> None:
        queue = self.root / ".abh" / "roadmap.json"
        queue.parent.mkdir(parents=True, exist_ok=True)
        queue.write_text(
            json.dumps(
                {
                    "schema_version": "2",
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
                    "schema_version": "2",
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
                    "schema_version": "2",
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
