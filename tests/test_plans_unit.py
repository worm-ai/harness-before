"""Unit tests for plan transition rules and closed-plan immutability."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from abh.attractors import create_attractor
from abh.errors import AbhError
from abh.plans import create_plan, save_plan, transition_plan, update_plan_record
from abh.models import PlanRecord


class ClosedPlanImmutabilityTests(unittest.TestCase):
    """Tests that closed plans reject mutation attempts."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs" / "architecture" / "attractors").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "architecture" / "attractors" / "test.md").write_text("# Attractor\n", encoding="utf-8")
        create_attractor(
            attractor_id="test-attractor",
            title="Test",
            version="1.0.0",
            path="docs/architecture/attractors/test.md",
            intent="Test attractor",
            cwd=self.root,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _make_plan_record(self, plan_id: str, status: str = "ready") -> PlanRecord:
        """Create a PlanRecord directly without touching storage."""
        return PlanRecord(
            id=plan_id,
            title="Test Plan",
            attractor="docs/architecture/attractors/test.md",
            baseline="baseline",
            status=status,
            goals=["goal"],
            non_goals=["non-goal"],
            exit_criteria=["criterion"],
            validation_checklist=["python3 -c 'print(1)'"],
            closure_evidence=["docs/plans/test.md"],
        )

    def test_save_closed_plan_raises_error(self) -> None:
        plan = self._make_plan_record("plan-closed-guard", status="draft")
        save_plan(plan, cwd=self.root)
        plan.status = "closed"
        save_plan(plan, cwd=self.root)  # transition to closed is allowed
        plan.title = "mutated after close"  # proof-bearing field change
        with self.assertRaises(AbhError) as ctx:
            save_plan(plan, cwd=self.root)
        self.assertIn("cannot modify closed plan", str(ctx.exception))

    def test_update_closed_plan_raises_error(self) -> None:
        plan = create_plan(
            plan_id="plan-closed-update-guard",
            title="Test Plan",
            attractor="docs/architecture/attractors/test.md",
            baseline="baseline",
            status="draft",
            goals=["goal"],
            non_goals=["non-goal"],
            exit_criteria=["criterion"],
            cwd=self.root,
        )
        plan.status = "closed"
        save_plan(plan, cwd=self.root)  # save as closed first
        plan.title = "mutated title"  # proof-bearing field change
        with self.assertRaises(AbhError) as ctx:
            save_plan(plan, cwd=self.root)
        self.assertIn("cannot modify closed plan", str(ctx.exception))


class PlanTransitionTests(unittest.TestCase):
    """Tests for plan state machine transitions."""

    def test_valid_transitions(self) -> None:
        from abh.plans import ALLOWED_TRANSITIONS
        self.assertEqual(ALLOWED_TRANSITIONS["draft"], {"ready"})
        self.assertEqual(ALLOWED_TRANSITIONS["ready"], {"running", "blocked"})
        self.assertEqual(ALLOWED_TRANSITIONS["running"], {"blocked", "closing"})
        self.assertEqual(ALLOWED_TRANSITIONS["blocked"], {"running", "closing"})
        self.assertEqual(ALLOWED_TRANSITIONS["closing"], set())
        self.assertEqual(ALLOWED_TRANSITIONS["closed"], set())

    def test_closed_is_terminal(self) -> None:
        from abh.plans import ALLOWED_TRANSITIONS
        self.assertEqual(ALLOWED_TRANSITIONS["closed"], set())


if __name__ == "__main__":
    unittest.main()