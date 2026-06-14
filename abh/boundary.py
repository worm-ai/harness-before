"""Plan-bound structural drift detection.

Compares the project's import graph at plan-close time against the
baseline import graph captured during the plan's first verification.
New imports are checked against the plan's declared non-goals.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from .models import DriftFinding

DEFAULT_EXCLUDE_PATTERNS = {"__pycache__", ".git", ".abh", "venv", ".venv", ".tox", "node_modules", "build", "dist", ".eggs"}

# Prefixes that signal a non-goal is a negation — stripped before keyword extraction.
NEGATION_PREFIXES: tuple[str, ...] = tuple(sorted(
    ("不", "不要", "无需", "禁止", "避免", "no ", "not ", "don't ", "do not ", "avoid "),
    key=lambda s: -len(s),
))


def extract_module_imports(file_path: Path, *, parent_module: str = "") -> list[str]:
    """Parse a Python file and return all module-level imported module paths.

    Only walks top-level AST nodes — imports inside function or class bodies
    are excluded because they are runtime dependencies, not architectural ones.
    Relative imports are resolved against ``parent_module``.

    Returns an empty list for files that are not valid Python.
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
                for alias in node.names:
                    target = node.module if node.module is not None else alias.name
                    resolved = _resolve_relative_import(parent_module, node.level, target)
                    if resolved:
                        imports.append(resolved)
            elif node.module is not None:
                imports.append(node.module)
    return imports


def _resolve_relative_import(parent_module: str, level: int, target: str | None) -> str | None:
    if not parent_module:
        return None
    parts = parent_module.split(".")
    if level > len(parts):
        return None
    resolved_parts = parts[: len(parts) - level]
    if target:
        resolved_parts.append(target)
    return ".".join(resolved_parts) if resolved_parts else None


def _relative_module(file_path: Path, root: Path) -> str:
    rel = file_path.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


def build_import_map(root: Path, *, glob_pattern: str = "**/*.py", exclude: set[str] | None = None) -> dict[str, list[str]]:
    """Walk a directory tree and build a module-path → imported-modules map."""
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


def compute_structure_hash(root: Path, *, glob_pattern: str = "**/*.py") -> str:
    """Compute a deterministic SHA-256 hash of the project's import topology."""
    import_map = build_import_map(root, glob_pattern=glob_pattern)
    canonical = {module: sorted(set(imports)) for module, imports in sorted(import_map.items())}
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _strip_negation(text: str) -> str:
    """Remove negation prefixes from a non-goal string to extract positive keywords."""
    lowered = text.strip().lower()
    for prefix in NEGATION_PREFIXES:
        if lowered.startswith(prefix):
            return lowered[len(prefix):].strip()
    return lowered


def _extract_keywords(text: str) -> list[str]:
    """Extract searchable substrings from a non-goal after stripping negation.

    For space-delimited languages, returns individual words > 2 chars.
    For Chinese (no spaces between words), returns the full cleaned text
    plus individual characters > 1 char for substring matching.
    """
    clean = _strip_negation(text)
    words = clean.split()
    if words:
        return [w for w in words if len(w) > 2]
    # No spaces — treat the whole text as a search keyword.
    return [clean] if len(clean) > 2 else []


def analyze_plan_drift(*, plan_id: str, cwd: Path | None = None) -> list[DriftFinding]:
    """Compare current import graph against the plan's baseline verification.

    Loads the plan's first verification run (the baseline), retrieves the
    snapshotted import map, builds the current import map, and reports:

    1. New project-internal imports that match plan non-goal keywords.
    2. New external dependencies that match plan non-goal keywords.

    Returns a list of DriftFinding objects — empty if no violations found.
    """
    from .plans import load_plan
    from .verifications import load_verification

    root = Path.cwd() if cwd is None else Path(cwd)
    plan = load_plan(plan_id, cwd=root)

    if not plan.verification_runs:
        return []

    # Get baseline import map from the first verification run.
    baseline_run = load_verification(plan.verification_runs[0], cwd=root)
    baseline_map = baseline_run.environment.get("baseline_import_map")
    if not isinstance(baseline_map, dict):
        return []  # pre-structural-snapshot verification — no data to compare

    current_map = build_import_map(root)
    findings: list[DriftFinding] = []

    # Collect non-goal keywords for matching.
    non_goal_keywords: dict[str, list[str]] = {}
    for non_goal in plan.non_goals:
        keywords = _extract_keywords(non_goal)
        if keywords:
            non_goal_keywords[non_goal] = keywords

    # Find new imports (in current but not in baseline).
    for module, current_imports in current_map.items():
        baseline_imports = set(baseline_map.get(module, []))
        new_imports = [imp for imp in current_imports if imp not in baseline_imports]
        for imp in new_imports:
            # Check against non-goal keywords (bidirectional match).
            lowered = imp.lower()
            for non_goal, keywords in non_goal_keywords.items():
                if any(kw in lowered or lowered in kw for kw in keywords):
                    findings.append(
                        DriftFinding(
                            drift_type="dependency_drift",
                            evidence=f"New import {imp!r} in {module} matches non-goal: {non_goal}",
                            recommendation=f"Review plan '{plan_id}' non-goal: {non_goal}. Revert the import or update the plan scope.",
                            severity="high",
                            confidence="high",
                            rule_id=f"plan_non_goal:{plan_id}",
                            source_excerpt=f"{module} newly imports {imp}",
                            evidence_path=str(root / (module.replace(".", "/") + ".py")),
                        )
                    )

    # Find new modules (not in baseline at all).
    baseline_modules = set(baseline_map.keys())
    new_modules = set(current_map.keys()) - baseline_modules
    for module in sorted(new_modules):
        all_imports = set(current_map[module])
        for non_goal, keywords in non_goal_keywords.items():
            lowered = module.lower() + " " + " ".join(all_imports).lower()
            if any(kw in lowered for kw in keywords):
                findings.append(
                    DriftFinding(
                        drift_type="boundary_drift",
                        evidence=f"New module {module} (imports: {', '.join(sorted(all_imports)[:5])}) matches non-goal: {non_goal}",
                        recommendation=f"Review plan '{plan_id}' non-goal: {non_goal}.",
                        severity="medium",
                        confidence="medium",
                        rule_id=f"plan_non_goal:{plan_id}",
                        source_excerpt=f"New module {module}",
                        evidence_path=str(root / (module.replace(".", "/") + ".py")),
                    )
                )

    return findings


def _file_in_scope(file_path: str, scope_dirs: set[str]) -> bool:
    """Check whether a file path falls within at least one scope directory."""
    normalized = file_path.replace("\\", "/")
    for scope in scope_dirs:
        s = scope.rstrip("/") + "/"
        if normalized.startswith(s) or normalized == scope.rstrip("/"):
            return True
    return False


def infer_plan_scope(plan, cwd: Path) -> set[str]:
    """Extract directory scopes from plan goals.

    Heuristics:
    1. Path-like tokens containing ``/`` or ending in ``.py`` → directory prefix.
    2. Tokens that match existing directories under ``cwd``.
    3. Tokens that match known module paths from the codebase map.

    Returns an empty set if no scope can be inferred (meaning no restriction).
    """
    scopes: set[str] = set()
    for goal in plan.goals:
        for word in goal.split():
            word = word.strip(".,;:'\"/")
            if not word:
                continue
            # Path-like: contains / or ends with .py
            if "/" in word:
                # Use full path prefix, not just the first component.
                path_part = word.rstrip("/")
                scopes.add(path_part)
            elif word.endswith(".py"):
                scopes.add(word.rsplit("/", 1)[0] if "/" in word else word[:-3])
            else:
                # Check if it matches an existing directory
                candidate = cwd / word
                if candidate.is_dir():
                    scopes.add(word)
    # Also look for quoted paths or backtick paths in goals
    import re
    for goal in plan.goals:
        for match in re.finditer(r'[`"]([^`"]+)[`"]', goal):
            path_str = match.group(1)
            if "/" in path_str or path_str.endswith(".py"):
                scopes.add(path_str.split("/")[0])
    return scopes


def check_plan_scope(*, plan_id: str, cwd: Path | None = None) -> list[DriftFinding]:
    """Check whether git changes since baseline exceed the plan's declared scope.

    Uses ``plan.baseline_commit`` (captured at plan creation time) as the
    reference point. Compares files changed since that commit against the
    scope inferred from plan.goals (or explicit plan.scope).

    Returns a list of DriftFinding objects. An empty list with all checks
    passing means the plan's changes are within scope.
    """
    from .plans import load_plan

    root = Path.cwd() if cwd is None else Path(cwd)
    plan = load_plan(plan_id, cwd=root)

    baseline_commit = getattr(plan, "baseline_commit", "") or ""
    if not baseline_commit:
        # Plan was created without git — scope check not applicable.
        return []

    # Verify git is still available and the commit still exists.
    from .verifications import git_metadata
    current_git = git_metadata(root)
    if not current_git.get("available"):
        return [_no_git_finding(plan_id)]

    # Get changed files since the baseline commit.
    git_status_paths = _changed_files_since(baseline_commit, root)
    if git_status_paths is None:
        return [_no_git_finding(plan_id)]

    # Resolve scope: explicit plan.scope takes priority over goal inference.
    scope = set(getattr(plan, "scope", []) or [])
    if not scope:
        scope = infer_plan_scope(plan, root)

    findings: list[DriftFinding] = []

    # Empty scope with baseline → user needs to declare scope; don't flag everything.
    if not scope and git_status_paths:
        non_abh = [p for p in git_status_paths if not p.startswith((".abh/", "docs/audits/", "docs/plans/", "docs/memory/"))]
        if non_abh:
            findings.append(
                DriftFinding(
                    drift_type="boundary_drift",
                    evidence=f"Plan has no scope declared and {len(non_abh)} file(s) changed since baseline",
                    recommendation=f"Re-run 'abh plan update {plan_id} --scope <dirs>' to declare which directories this plan is allowed to touch, or add path-like goals to the plan.",
                    severity="need_info",
                    confidence="high",
                    rule_id=f"plan_scope_missing:{plan_id}",
                    source_excerpt=f"Changed files: {', '.join(non_abh[:5])}",
                    evidence_path="",
                )
            )
            return findings

    # Check each changed file against scope.
    for path in git_status_paths:
        if path.startswith((".abh/", "docs/audits/", "docs/plans/", "docs/memory/")):
            continue
        if scope and not _file_in_scope(path, scope):
            findings.append(
                DriftFinding(
                    drift_type="boundary_drift",
                    evidence=f"Changed file {path!r} is outside plan scope {sorted(scope)}",
                    recommendation=f"Review plan '{plan_id}' scope. If this change is intentional, update the plan scope. Otherwise, revert the out-of-scope change.",
                    severity="medium",
                    confidence="high",
                    rule_id=f"plan_scope:{plan_id}",
                    source_excerpt=f"git diff {baseline_commit[:8]}..HEAD includes {path}",
                    evidence_path=str(root / path),
                )
            )

    # Also check import changes against non-goals.
    if plan.verification_runs:
        import_findings = analyze_plan_drift(plan_id=plan_id, cwd=root)
        findings.extend(import_findings)

    return findings


def _no_git_finding(plan_id: str) -> DriftFinding:
    return DriftFinding(
        drift_type="boundary_drift",
        evidence=f"git unavailable; cannot verify plan scope for {plan_id}",
        recommendation="Ensure git is available and the plan was created with a valid baseline_commit. Re-create the plan if necessary.",
        severity="need_info",
        confidence="low",
        rule_id=f"plan_scope_git:{plan_id}",
        source_excerpt="git unavailable",
        evidence_path="",
    )


def _changed_files_since(commit: str, root: Path) -> list[str] | None:
    """Return files changed since a given commit, or None if unavailable."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", commit],
            cwd=root, text=True, capture_output=True, timeout=10, check=False,
        )
        if result.returncode != 0:
            return None
        return [p.strip().replace("\\", "/") for p in result.stdout.splitlines() if p.strip()]
    except (OSError, subprocess.TimeoutExpired):
        return None
