"""Unit tests for the structural import boundary checker."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from abh.boundary import (
    _import_targets_directory,
    _module_in_directory,
    analyze_structural_drift,
    build_import_map,
    check_boundary_rules,
    extract_module_imports,
    load_boundary_rules_from_attractor,
)
from abh.models import AttractorRecord, BoundaryRule


class ExtractModuleImportsTests(unittest.TestCase):
    """Tests for parsing module-level imports from Python source."""

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
        path = self._write("mod.py", "import os\nimport sys\nx = 1\n")
        imports = extract_module_imports(path)
        self.assertIn("os", imports)
        self.assertIn("sys", imports)

    def test_from_import(self) -> None:
        path = self._write("mod.py", "from pathlib import Path\nfrom os import path as osp\n")
        imports = extract_module_imports(path)
        self.assertIn("pathlib", imports)
        self.assertIn("os", imports)

    def test_excludes_function_body_imports(self) -> None:
        path = self._write(
            "mod.py",
            "import os\n\ndef foo():\n    import json\n    return json.dumps({})\n",
        )
        imports = extract_module_imports(path)
        self.assertIn("os", imports)
        self.assertNotIn("json", imports)

    def test_excludes_class_body_imports(self) -> None:
        path = self._write(
            "mod.py",
            "class Foo:\n    import sqlite3\n    def bar(self):\n        return sqlite3\n",
        )
        imports = extract_module_imports(path)
        self.assertNotIn("sqlite3", imports)

    def test_syntax_error_returns_empty(self) -> None:
        path = self._write("broken.py", "this is not valid python {{{")
        imports = extract_module_imports(path)
        self.assertEqual(imports, [])

    def test_empty_file_returns_empty(self) -> None:
        path = self._write("empty.py", "")
        imports = extract_module_imports(path)
        self.assertEqual(imports, [])

    def test_relative_import(self) -> None:
        path = self._write("pkg/mod.py", "from . import sibling\nfrom ..parent import thing\n")
        imports = extract_module_imports(path, parent_module="pkg.mod")
        # from . import sibling → module=sibling → resolved to "pkg.sibling"
        # from ..parent import thing → module=parent → resolved to "parent"
        self.assertIn("pkg.sibling", imports)
        self.assertIn("parent", imports)
        self.assertEqual(len(imports), 2)


class BuildImportMapTests(unittest.TestCase):
    """Tests for building import maps from directory trees."""

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
        self._write("src/app.py", "import os\nfrom pathlib import Path\n")
        import_map = build_import_map(self.root)
        self.assertIn("src.app", import_map)
        self.assertIn("os", import_map["src.app"])

    def test_multi_file_map(self) -> None:
        self._write("src/web/views.py", "import os\n")
        self._write("src/data/models.py", "import sqlalchemy\n")
        import_map = build_import_map(self.root)
        self.assertIn("src.web.views", import_map)
        self.assertIn("src.data.models", import_map)

    def test_excludes_virtualenv_dirs(self) -> None:
        self._write(".venv/lib/pkg.py", "import evil\n")
        self._write("src/main.py", "import os\n")
        import_map = build_import_map(self.root)
        self.assertNotIn(".venv.lib.pkg", import_map)
        self.assertIn("src.main", import_map)

    def test_skips_files_without_imports(self) -> None:
        self._write("src/empty.py", "x = 1\n")
        self._write("src/with_imports.py", "import os\n")
        import_map = build_import_map(self.root)
        self.assertNotIn("src.empty", import_map)
        self.assertIn("src.with_imports", import_map)


class ModuleInDirectoryTests(unittest.TestCase):
    """Tests for the module-path-to-directory matching helper."""

    def test_exact_prefix_match(self) -> None:
        self.assertTrue(_module_in_directory("abh.drift", "abh"))

    def test_no_match_different_root(self) -> None:
        self.assertFalse(_module_in_directory("tests.test_cli", "abh"))

    def test_single_component_match(self) -> None:
        self.assertTrue(_module_in_directory("abh", "abh"))


class ImportTargetsDirectoryTests(unittest.TestCase):
    """Tests for checking whether an import resolves into a directory."""

    def test_direct_target_match(self) -> None:
        import_map = {"abh.models": ["os"], "abh.drift": ["abh.models"]}
        self.assertTrue(_import_targets_directory("abh.models", "abh", import_map))

    def test_no_match(self) -> None:
        import_map = {"abh.models": ["os"]}
        self.assertFalse(_import_targets_directory("sqlalchemy", "abh", import_map))

    def test_known_module_resolves(self) -> None:
        import_map = {"src.data.database": ["os"]}
        self.assertTrue(_import_targets_directory("database", "src.data", import_map))


class CheckBoundaryRulesTests(unittest.TestCase):
    """Tests for boundary rule violation detection."""

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

    def test_no_violation_when_clean(self) -> None:
        self._write("src/ui/views.py", "import os\n")
        self._write("src/data/models.py", "import sqlalchemy\n")
        import_map = build_import_map(self.root)
        rules = [BoundaryRule(rule_id="ui-no-data", description="UI must not import data",
                              source_dir="src.ui", forbidden_dir="src.data")]
        findings = check_boundary_rules(import_map, rules, self.root)
        self.assertEqual(len(findings), 0)

    def test_violation_detected(self) -> None:
        self._write("src/ui/views.py", "from src.data.models import User\n")
        self._write("src/data/models.py", "class User: pass\n")
        import_map = build_import_map(self.root)
        rules = [BoundaryRule(rule_id="ui-no-data", description="UI must not import data",
                              source_dir="src.ui", forbidden_dir="src.data",
                              severity="high", recommendation="Move logic to a service layer.")]
        findings = check_boundary_rules(import_map, rules, self.root)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].drift_type, "import_boundary_drift")
        self.assertEqual(findings[0].severity, "high")
        self.assertEqual(findings[0].confidence, "high")
        self.assertIn("src.ui.views", findings[0].evidence)

    def test_multiple_violations_from_same_module(self) -> None:
        self._write("src/ui/views.py", "from src.data.models import User\nfrom src.data.db import get_db\n")
        self._write("src/data/models.py", "")
        self._write("src/data/db.py", "")
        import_map = build_import_map(self.root)
        rules = [BoundaryRule(rule_id="ui-no-data", description="UI must not import data",
                              source_dir="src.ui", forbidden_dir="src.data")]
        findings = check_boundary_rules(import_map, rules, self.root)
        self.assertEqual(len(findings), 2)


class LoadBoundaryRulesTests(unittest.TestCase):
    """Tests for loading boundary rules from an attractor."""

    def test_empty_attractor(self) -> None:
        attractor = AttractorRecord(id="test", title="Test", version="1.0", path="p.md", intent="intent")
        rules = load_boundary_rules_from_attractor(attractor)
        self.assertEqual(rules, [])

    def test_basic_rule(self) -> None:
        attractor = AttractorRecord(
            id="test", title="Test", version="1.0", path="p.md", intent="intent",
            boundary_rules=[{"rule_id": "no-ui-db", "source_dir": "ui", "forbidden_dir": "db",
                             "severity": "high", "recommendation": "Use repository."}],
        )
        rules = load_boundary_rules_from_attractor(attractor)
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].rule_id, "no-ui-db")
        self.assertEqual(rules[0].severity, "high")

    def test_skips_incomplete_rules(self) -> None:
        attractor = AttractorRecord(
            id="test", title="Test", version="1.0", path="p.md", intent="intent",
            boundary_rules=[
                {"rule_id": "valid", "source_dir": "a", "forbidden_dir": "b"},
                {"description": "missing required fields"},
            ],
        )
        rules = load_boundary_rules_from_attractor(attractor)
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].rule_id, "valid")


class AnalyzeStructuralDriftIntegrationTests(unittest.TestCase):
    """Integration test for the full structural drift pipeline."""

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

    def test_no_rules_returns_empty(self) -> None:
        self._write("src/main.py", "import os\n")
        findings = analyze_structural_drift(project_root=self.root)
        self.assertEqual(findings, [])

    def test_with_explicit_rules(self) -> None:
        self._write("src/ui/page.py", "import src.data.db\n")
        self._write("src/data/db.py", "")
        rules = [BoundaryRule(rule_id="r1", description="UI no data", source_dir="src.ui", forbidden_dir="src.data")]
        findings = analyze_structural_drift(project_root=self.root, boundary_rules=rules)
        self.assertEqual(len(findings), 1)

    def test_with_attractor_rules(self) -> None:
        self._write("src/ui/page.py", "from src.data.models import User\n")
        self._write("src/data/models.py", "")
        attractor = AttractorRecord(
            id="test", title="Test", version="1.0", path="p.md", intent="intent",
            boundary_rules=[{"rule_id": "ui-no-data", "source_dir": "src.ui", "forbidden_dir": "src.data"}],
        )
        findings = analyze_structural_drift(project_root=self.root, attractor=attractor)
        self.assertEqual(len(findings), 1)


if __name__ == "__main__":
    unittest.main()