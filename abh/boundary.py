"""Structural drift detection: import boundary analysis for Python projects.

Uses only the stdlib ``ast`` module — no external dependencies, no LLM calls.
Checks whether module-level imports violate declared architectural boundary rules.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from .models import BoundaryRule, DriftFinding

# Directories excluded from project import scanning.
DEFAULT_EXCLUDE_PATTERNS = {"__pycache__", ".git", ".abh", "venv", ".venv", ".tox", "node_modules", "build", "dist", ".eggs"}


def extract_module_imports(file_path: Path, *, parent_module: str = "") -> list[str]:
    """Parse a Python file and return all module-level imported module paths.

    Only walks top-level AST nodes — imports inside function or class bodies
    are excluded because they are runtime dependencies, not architectural ones.

    Relative imports are resolved against ``parent_module``.

    Returns an empty list for files that are not valid Python (syntax errors,
    encoding issues, etc.).
    """
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return []

    imports: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                # Relative import. Resolve each imported name to its absolute module path.
                # from . import sibling (level=1, module=None, names=[alias('sibling')])
                # from .models import Thing (level=1, module="models", names=[alias('Thing')])
                for alias in node.names:
                    target = node.module if node.module is not None else alias.name
                    resolved = _resolve_relative_import(parent_module, node.level, target)
                    if resolved:
                        imports.append(resolved)
            elif node.module is not None:
                # Absolute import: from os import path → "os"
                imports.append(node.module)
    return imports


def _resolve_relative_import(parent_module: str, level: int, target: str | None) -> str | None:
    """Resolve a relative import against a parent module path.

    Args:
        parent_module: Dotted module path of the importing file (e.g. ``abh.drift``).
        level: Number of dots in the relative import (1 for ``.``, 2 for ``..``).
        target: The target module name after the dots, or None for bare ``from . import ...``.

    Returns:
        Resolved absolute module path, or None if resolution is impossible.
    """
    if not parent_module:
        return None
    parts = parent_module.split(".")
    if level > len(parts):
        return None  # beyond top-level package
    resolved_parts = parts[: len(parts) - level]
    if target:
        resolved_parts.append(target)
    return ".".join(resolved_parts) if resolved_parts else None


def _relative_module(file_path: Path, root: Path) -> str:
    """Return the dotted module path for a file relative to a project root."""
    rel = file_path.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


def build_import_map(root: Path, *, glob_pattern: str = "**/*.py", exclude: set[str] | None = None) -> dict[str, list[str]]:
    """Walk a directory tree and build a module-path → imported-modules map.

    Args:
        root: Project root directory to scan.
        glob_pattern: Pattern for files to include (default ``**/*.py``).
        exclude: Directory names to skip (defaults to common build/venv dirs).

    Returns a dict mapping each module's dotted path to its list of imported modules.
    """
    exclude_patterns = exclude if exclude is not None else DEFAULT_EXCLUDE_PATTERNS
    import_map: dict[str, list[str]] = {}
    for py_file in sorted(root.glob(glob_pattern)):
        if any(part in exclude_patterns for part in py_file.parts):
            continue
        module = _relative_module(py_file, root)
        imports = extract_module_imports(py_file, parent_module=module)
        if imports:
            import_map[module] = imports
    return import_map


def _module_in_directory(module_path: str, directory: str) -> bool:
    """Check whether a dotted module path lives under a given directory prefix.

    Examples:
        >>> _module_in_directory("abh.drift", "abh")
        True
        >>> _module_in_directory("abh", "abh")
        True
        >>> _module_in_directory("tests.test_cli", "abh")
        False
    """
    normalized_module = module_path.replace("/", ".")
    normalized_dir = directory.replace("/", ".").rstrip(".")
    return normalized_module == normalized_dir or normalized_module.startswith(normalized_dir + ".")


def _import_targets_directory(imported_module: str, directory: str, import_map: dict[str, list[str]]) -> bool:
    """Check whether an imported module name resolves to a file in the given directory.

    Returns True if:
    - The imported module itself lives in the directory (e.g., importing ``abh.models``
      when checking directory ``abh``).
    - OR the imported module is a known project module that lives in the directory.
    """
    if _module_in_directory(imported_module, directory):
        return True
    for known_module in import_map:
        if known_module.endswith("." + imported_module) or known_module == imported_module:
            if _module_in_directory(known_module, directory):
                return True
    return False


def check_boundary_rules(
    import_map: dict[str, list[str]],
    rules: list[BoundaryRule],
    root: Path,
) -> list[DriftFinding]:
    """Check import map against a list of boundary rules.

    Each rule says: "modules in ``source_dir`` must NOT import anything from
    ``forbidden_dir``".  For every violation, a structured ``DriftFinding`` is
    produced with the exact file path and import line as evidence.

    Args:
        import_map: Output of ``build_import_map``.
        rules: Boundary rules to check.
        root: Project root, used to reconstruct file paths for evidence.

    Returns:
        List of drift findings, one per violation.
    """
    findings: list[DriftFinding] = []
    for rule in rules:
        source_dir = rule.source_dir
        forbidden_dir = rule.forbidden_dir
        for module, imports in import_map.items():
            if not _module_in_directory(module, source_dir):
                continue
            for imp in imports:
                if _import_targets_directory(imp, forbidden_dir, import_map):
                    file_path = root / (module.replace(".", "/") + ".py")
                    findings.append(
                        DriftFinding(
                            drift_type="import_boundary_drift",
                            evidence=f"{module} imports {imp!r} from forbidden directory {forbidden_dir!r}",
                            recommendation=rule.recommendation or f"Remove import of {imp!r} from {module} or update boundary rule {rule.rule_id!r}.",
                            severity=rule.severity,
                            confidence="high",
                            rule_id=rule.rule_id,
                            matched_span={"file": str(file_path), "line": 0, "text": f"import {imp}"},
                            source_excerpt=f"In {file_path}: imports {imp} (blocked by rule {rule.rule_id})",
                            evidence_path=str(file_path),
                        )
                    )
    return findings


def load_boundary_rules_from_attractor(attractor) -> list[BoundaryRule]:
    """Parse boundary rules from an AttractorRecord's boundary_rules field.

    Each entry in ``attractor.boundary_rules`` should be a dict with keys:
    ``rule_id``, ``source_dir``, ``forbidden_dir``, and optionally
    ``severity``, ``description``, ``recommendation``.
    """
    rules: list[BoundaryRule] = []
    for item in getattr(attractor, "boundary_rules", []) or []:
        if not isinstance(item, dict):
            continue
        rule_id = item.get("rule_id", "")
        source_dir = item.get("source_dir", "")
        forbidden_dir = item.get("forbidden_dir", "")
        if not rule_id or not source_dir or not forbidden_dir:
            continue
        rules.append(
            BoundaryRule(
                rule_id=str(rule_id),
                description=str(item.get("description", "")),
                source_dir=str(source_dir),
                forbidden_dir=str(forbidden_dir),
                severity=str(item.get("severity", "high")),
                recommendation=str(item.get("recommendation", "")),
            )
        )
    return rules


def analyze_structural_drift(
    *,
    project_root: Path,
    attractor=None,
    boundary_rules: list[BoundaryRule] | None = None,
) -> list[DriftFinding]:
    """Run boundary rule checks against a project's import graph.

    Args:
        project_root: Root directory of the project to analyze.
        attractor: Optional AttractorRecord whose boundary_rules are used.
        boundary_rules: Optional explicit list of BoundaryRule objects.

    Returns:
        List of DriftFinding objects describing violations.

    Rules are resolved in order: explicit ``boundary_rules`` first, then
    attractor-derived rules.
    """
    rules = list(boundary_rules or [])
    if attractor is not None:
        rules.extend(load_boundary_rules_from_attractor(attractor))
    if not rules:
        return []
    import_map = build_import_map(project_root)
    return check_boundary_rules(import_map, rules, project_root)


def compute_structure_hash(root: Path, *, glob_pattern: str = "**/*.py") -> str:
    """Compute a deterministic hash of the project's import topology.

    Serializes the import map to canonical JSON and returns its SHA-256.
    When any module-level import changes, the hash changes — this serves
    as a structural fingerprint that can be snapshotted at verification
    time and compared later for staleness detection.
    """
    import_map = build_import_map(root, glob_pattern=glob_pattern)
    # Canonicalize: sort keys, sort import lists for determinism.
    canonical = {module: sorted(set(imports)) for module, imports in sorted(import_map.items())}
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
