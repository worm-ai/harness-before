"""Tests for plan-bound structural drift against baseline verification."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from abh.boundary import (
    _strip_negation,
    _extract_keywords,
    analyze_plan_drift,
    build_import_map,
    compute_structure_hash,
    extract_module_imports,
)
from abh.attractors import create_attractor
from abh.plans import create_plan, load_plan
from abh.verifications import record_verification, load_verification


class ExtractModuleImportsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_simple_import(self) -> None:
        path = self._write("mod.py", "import os\nimport sys\n")
        imports = extract_module_imports(path)
        self.assertIn("os", imports)
        self.assertIn("sys", imports)

    def test_excludes_function_body_imports(self) -> None:
        path = self._write("mod.py", "import os\ndef foo():\n    import json\n")
        imports = extract_module_imports(path)
        self.assertIn("os", imports)
        self.assertNotIn("json", imports)

    def test_syntax_error_returns_empty(self) -> None:
        path = self._write("broken.py", "{{{")
        imports = extract_module_imports(path)
        self.assertEqual(imports, [])

    def test_relative_import(self) -> None:
        path = self._write("pkg/mod.py", "from . import sibling\nfrom ..parent import thing\n")
        imports = extract_module_imports(path, parent_module="pkg.mod")
        self.assertIn("pkg.sibling", imports)
        self.assertIn("parent", imports)


class BuildImportMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_single_file_map(self) -> None:
        self._write("src/app.py", "import os\n")
        import_map = build_import_map(self.root)
        self.assertIn("src.app", import_map)

    def test_excludes_virtualenv(self) -> None:
        self._write(".venv/lib/pkg.py", "import evil\n")
        self._write("src/main.py", "import os\n")
        import_map = build_import_map(self.root)
        self.assertNotIn(".venv.lib.pkg", import_map)
        self.assertIn("src.main", import_map)


class StructureHashTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_hash_same_for_same_structure(self) -> None:
        self._write("a.py", "import os\n")
        self._write("b.py", "import sys\n")
        h1 = compute_structure_hash(self.root)
        h2 = compute_structure_hash(self.root)
        self.assertEqual(h1, h2)

    def test_hash_changes_when_import_changes(self) -> None:
        self._write("a.py", "import os\n")
        h1 = compute_structure_hash(self.root)
        self._write("a.py", "import os\nimport json\n")
        h2 = compute_structure_hash(self.root)
        self.assertNotEqual(h1, h2)


class NegationAndKeywordTests(unittest.TestCase):
    def test_strip_chinese_negation(self) -> None:
        self.assertEqual(_strip_negation("不要加数据库"), "加数据库")

    def test_strip_english_negation(self) -> None:
        self.assertEqual(_strip_negation("do not add database"), "add database")

    def test_no_negation_passes_through(self) -> None:
        self.assertEqual(_strip_negation("add logging"), "add logging")

    def test_extract_keywords(self) -> None:
        # "不" is the shortest negation prefix but checked last (sorted by length desc).
        # Strips to the positive form.
        keywords = _extract_keywords("不引入新的数据库依赖")
        self.assertIn("引入新的数据库依赖", keywords)


class AnalyzePlanDriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # Setup minimal ABH workspace.
        (self.root / "docs" / "architecture" / "attractors").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "architecture" / "attractors" / "test.md").write_text("# Attractor\n", encoding="utf-8")
        create_attractor(
            attractor_id="test-attr", title="Test", version="1.0",
            path="docs/architecture/attractors/test.md", intent="test",
            cwd=self.root,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_no_verification_runs_returns_empty(self) -> None:
        plan = create_plan(
            plan_id="plan-no-verify", title="No Verify", attractor="docs/architecture/attractors/test.md", baseline="b",
            status="draft", goals=["g"], non_goals=["不要加数据库"], exit_criteria=["ec"],
            cwd=self.root,
        )
        findings = analyze_plan_drift(plan_id="plan-no-verify", cwd=self.root)
        self.assertEqual(findings, [])

    def test_no_non_goal_match_returns_empty(self) -> None:
        self._write("src/main.py", "import os\n")
        plan = create_plan(
            plan_id="plan-clean", title="Clean", attractor="docs/architecture/attractors/test.md", baseline="b",
            status="draft", goals=["g"], non_goals=["不引入数据库"], exit_criteria=["ec"],
            cwd=self.root,
        )
        record_verification(plan_id="plan-clean", command="echo ok", result="pass", cwd=self.root)
        findings = analyze_plan_drift(plan_id="plan-clean", cwd=self.root)
        self.assertEqual(findings, [])

    def test_non_goal_violation_detected(self) -> None:
        self._write("src/main.py", "import os\n")
        plan = create_plan(
            plan_id="plan-ng-violate", title="NG Violate", attractor="docs/architecture/attractors/test.md", baseline="b",
            status="draft", goals=["g"], non_goals=["不引入sqlalchemy"], exit_criteria=["ec"],
            cwd=self.root,
        )
        record_verification(plan_id="plan-ng-violate", command="echo ok", result="pass", cwd=self.root)
        # After verification, add a dependency that violates non-goal.
        self._write("src/main.py", "import os\nimport sqlalchemy\n")
        findings = analyze_plan_drift(plan_id="plan-ng-violate", cwd=self.root)
        self.assertGreaterEqual(len(findings), 1)
        self.assertTrue(any("sqlalchemy" in f.evidence for f in findings))


if __name__ == "__main__":
    unittest.main()