from __future__ import annotations

import os
import sys
import hashlib
import shlex
import subprocess
import time
import uuid
from pathlib import Path

from . import __version__
from .errors import AbhError
from .models import VERIFICATION_RESULTS, VERIFICATION_TRUST_LEVELS, VerificationRun
from .plans import load_plan, plan_verification_snapshot, save_plan
from .storage import ensure_workspace, read_json, verification_path, write_json

GIT_STATUS_HASH_IGNORED_PREFIXES = (
    ".abh/audits/",
    ".abh/memory/",
    ".abh/plans/",
    ".abh/verifications/",
    "docs/audits/",
    "docs/memory/",
    "docs/plans/",
)

RUNNER_EXECUTION_POLICY = "guarded_local_shell"
RUNNER_COMMAND_SOURCE = "plan_validation_checklist"
RUNNER_ISOLATION = "none"

# Execution policy allowlist: commands that are safe to run locally.
# Each entry is a (prefix, reason) pair. Commands matching a prefix are allowed.
SAFE_COMMAND_PREFIXES: tuple[tuple[str, str], ...] = (
    ("python3 -m ", "python module invocation"),
    ("python -m ", "python module invocation"),
    ("python3 ", "python script invocation"),
    ("python ", "python script invocation"),
    ("pytest", "pytest test runner"),
    ("abh ", "abh CLI command"),
    ("git diff", "git diff check"),
    ("git status", "git status check"),
    ("tox", "tox test runner"),
    ("make ", "make target"),
)

# Patterns that are always blocked regardless of allowlist.
DANGEROUS_PATTERNS: tuple[str, ...] = (
    "rm -rf",
    "rm -r",
    "del /",
    "mkfs",
    "dd if=",
    "> /dev/",
    "curl ",
    "wget ",
    "| bash",
    "| sh",
    "| zsh",
    "| fish",
    "/dev/null",
    "shutdown",
    "reboot",
    "kill -9",
    "killall",
)


class CommandPolicyResult:
    """Result of checking a command against the execution policy."""

    __slots__ = ("allowed", "reason", "policy")

    def __init__(self, allowed: bool, reason: str, policy: str) -> None:
        self.allowed = allowed
        self.reason = reason
        self.policy = policy


def check_command_policy(command: str, policy: str = RUNNER_EXECUTION_POLICY) -> CommandPolicyResult:
    """Check whether a command is allowed under the current execution policy.

    Policy modes:
    - ``local_shell``: legacy mode, all commands allowed (no checks).
    - ``guarded_local_shell``: allowlist + dangerous pattern block.
    - ``ci_only``: only allowlisted commands, must be in CI environment.
    """
    if policy == "local_shell":
        return CommandPolicyResult(allowed=True, reason="legacy local_shell policy: all commands allowed", policy=policy)

    stripped = command.strip()

    # Block dangerous patterns first. Normalize whitespace to prevent bypass.
    lowered = " ".join(stripped.lower().split())
    for pattern in DANGEROUS_PATTERNS:
        if pattern in lowered:
            return CommandPolicyResult(
                allowed=False,
                reason=f"blocked by dangerous pattern: {pattern!r}",
                policy=policy,
            )

    # Normalize the command: resolve absolute paths and strip quotes from the executable.
    # Allow commands like "/path/to/python3" -c "..." by extracting the first token.
    import shlex as _shlex
    try:
        parts = _shlex.split(stripped)
    except ValueError:
        parts = [stripped]

    if not parts:
        return CommandPolicyResult(allowed=False, reason="empty command", policy=policy)

    exe_basename = parts[0].replace("\\", "/").split("/")[-1].lower()

    # Match against known safe basenames.
    safe_basenames = {
        "python3", "python", "py", "python3.exe", "python.exe",
        "pytest", "tox", "make", "abh", "abh.exe",
        "git",
    }
    if exe_basename in safe_basenames:
        if policy == "ci_only":
            import os

            if os.environ.get("CI") != "true":
                return CommandPolicyResult(
                    allowed=False,
                    reason="ci_only policy requires CI=true environment variable",
                    policy=policy,
                )
        return CommandPolicyResult(allowed=True, reason=f"allowed by safe basename: {exe_basename}", policy=policy)

    # Also match safe prefixes for module invocations.
    for prefix, reason in SAFE_COMMAND_PREFIXES:
        if stripped.startswith(prefix):
            if policy == "ci_only":
                import os

                if os.environ.get("CI") != "true":
                    return CommandPolicyResult(
                        allowed=False,
                        reason="ci_only policy requires CI=true environment variable",
                        policy=policy,
                    )
            return CommandPolicyResult(allowed=True, reason=f"allowed by prefix: {reason}", policy=policy)

    # Commands not in allowlist and not in blocklist are blocked in guarded mode.
    return CommandPolicyResult(
        allowed=False,
        reason=f"command not in allowlist: {stripped!r}",
        policy=policy,
    )


def load_verification(run_id: str, cwd: Path | None = None) -> VerificationRun:
    path = verification_path(run_id, cwd)
    if not path.exists():
        raise AbhError(f"verification run not found: {run_id}")
    return VerificationRun.from_dict(read_json(path))


def record_verification(
    *,
    plan_id: str,
    command: str,
    result: str,
    artifacts: list[str] | None = None,
    failed_checks: list[str] | None = None,
    failure_classifications: list[dict[str, object]] | None = None,
    environment: dict | None = None,
    trust_level: str = "manual_record",
    cwd: Path | None = None,
) -> VerificationRun:
    if result not in VERIFICATION_RESULTS:
        raise AbhError(f"invalid verification result: {result}")
    if trust_level not in VERIFICATION_TRUST_LEVELS:
        raise AbhError(f"invalid verification trust level: {trust_level}")
    if not command.strip():
        raise AbhError("verification command is required")
    plan = load_plan(plan_id, cwd)
    ensure_workspace(cwd)
    metadata = dict(environment or {})
    metadata.setdefault("plan", plan_verification_snapshot(plan))
    # Embed structural baseline for plan-bound drift analysis.
    root = Path.cwd() if cwd is None else Path(cwd)
    try:
        from .boundary import _import_map_hash, build_import_map as _bim
        import_map = _bim(root)
        metadata.setdefault("structure_hash", _import_map_hash(import_map))
        metadata.setdefault("baseline_import_map", import_map)
        metadata.setdefault("git", git_metadata(root))
    except Exception:
        pass
    run = VerificationRun(
        id=f"ver-{uuid.uuid4().hex[:12]}",
        plan_id=plan_id,
        command=command,
        result=result,
        artifacts=list(artifacts or []),
        failed_checks=list(failed_checks or []),
        failure_classifications=[dict(item) for item in failure_classifications or []],
        environment=metadata,
        trust_level=trust_level,
    )
    write_json(verification_path(run.id, cwd), run.to_dict())
    plan.verification_runs.append(run.id)
    if result in {"fail", "partial"} and plan.status in {"ready", "running"}:
        plan.status = "blocked"
    save_plan(plan, cwd)
    return run


def is_recursive_verify_command(command: str, plan_id: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    if len(parts) < 4:
        return False

    for index in range(len(parts)):
        if _is_abh_executable(parts[index]) and _verify_run_targets_plan(parts[index + 1:], plan_id):
            return True
        if (
            _is_python_executable(parts[index])
            and parts[index + 1:index + 4] == ["-m", "abh", "verify"]
            and _verify_run_targets_plan(parts[index + 4:], plan_id)
        ):
            return True
    return False


def _is_python_executable(token: str) -> bool:
    name = token.replace("\\", "/").split("/")[-1].lower()
    return name in {"py", "python", "python3", "python.exe", "python3.exe"}


def _is_abh_executable(token: str) -> bool:
    name = token.replace("\\", "/").split("/")[-1].lower()
    return name in {"abh", "abh.exe"}


def _verify_run_targets_plan(parts: list[str], plan_id: str) -> bool:
    if len(parts) >= 3 and parts[0:2] == ["verify", "run"]:
        return plan_id in parts[2:]
    if len(parts) >= 2 and parts[0] == "run":
        return plan_id in parts[1:]
    return False


def git_metadata(root: Path) -> dict[str, object]:
    metadata: dict[str, object] = {
        "commit": None,
        "dirty": None,
        "status_hash": None,
        "available": False,
    }
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
        if commit.returncode != 0:
            return metadata
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return metadata

    metadata["commit"] = commit.stdout.strip()
    normalized_status = normalized_git_status(status.stdout) if status.returncode == 0 else ""
    metadata["dirty"] = bool(normalized_status) if status.returncode == 0 else None
    metadata["status_hash"] = (
        hashlib.sha256(normalized_status.encode("utf-8")).hexdigest() if status.returncode == 0 else None
    )
    metadata["available"] = True
    return metadata


def normalized_git_status(status: str) -> str:
    lines = [line for line in status.splitlines() if not is_ignored_git_status_line(line)]
    return "\n".join(lines)


def is_ignored_git_status_line(line: str) -> bool:
    if len(line) < 4:
        return False
    path = line[3:]
    paths = path.split(" -> ")
    return all(any(item.startswith(prefix) for prefix in GIT_STATUS_HASH_IGNORED_PREFIXES) for item in paths)


def split_command(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return []


def failure_classification(
    *,
    command: str,
    category: str,
    message: str,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "command": command,
        "category": category,
        "message": message,
        "details": dict(details or {}),
    }


def environment_snapshot(*, root: Path, commands: list[str], timeout_seconds: int) -> dict[str, object]:
    env_allowlist = {name: os.environ[name] for name in ("CI", "VIRTUAL_ENV") if name in os.environ}
    snapshot: dict[str, object] = {
        "cwd": str(root.resolve()),
        "git": git_metadata(root),
        "abh": {"version": __version__},
        "python": {"version": sys.version, "executable": sys.executable},
        "runner": {
            "timeout_seconds": timeout_seconds,
            "shell": True,
            "check_count": len(commands),
            "execution_policy": RUNNER_EXECUTION_POLICY,
            "trust_level": "local_shell",
            "command_source": RUNNER_COMMAND_SOURCE,
            "isolation": RUNNER_ISOLATION,
        },
        "commands": [{"command": command, "argv": split_command(command)} for command in commands],
        "environment_variables": env_allowlist,
    }
    try:
        from .boundary import compute_structure_hash, build_import_map
        snapshot["structure_hash"] = compute_structure_hash(root)
        # Save full import map on the first verification as the plan's structural baseline.
        snapshot["baseline_import_map"] = build_import_map(root)
    except Exception:
        pass  # best-effort; structural data is optional
    return snapshot


def run_verification(
    *,
    plan_id: str,
    timeout_seconds: int = 120,
    cwd: Path | None = None,
) -> VerificationRun:
    plan = load_plan(plan_id, cwd)
    if not plan.validation_checklist:
        raise AbhError("plan has no validation checklist")
    if timeout_seconds <= 0:
        raise AbhError("timeout must be greater than zero")

    root = Path.cwd() if cwd is None else Path(cwd)
    execution_policy = RUNNER_EXECUTION_POLICY
    artifacts: list[str] = []
    failed_checks: list[str] = []
    failure_classifications: list[dict[str, object]] = []
    commands = list(plan.validation_checklist)
    environment = environment_snapshot(root=root, commands=commands, timeout_seconds=timeout_seconds)
    environment["execution_policy"] = execution_policy

    for command in commands:
        if is_recursive_verify_command(command, plan_id):
            artifacts.append(f"command={command!r}; exit_code=recursive_verify_guard")
            failed_checks.append(command)
            failure_classifications.append(
                failure_classification(
                    command=command,
                    category="recursive_guard",
                    message="validation command would recursively invoke verify run for the same plan",
                )
            )
            continue
        policy_result = check_command_policy(command, execution_policy)
        if not policy_result.allowed:
            artifacts.append(f"command={command!r}; exit_code=policy_blocked")
            failed_checks.append(command)
            failure_classifications.append(
                failure_classification(
                    command=command,
                    category="policy_blocked",
                    message=f"command blocked by execution policy: {policy_result.reason}",
                    details={"policy": policy_result.policy, "reason": policy_result.reason},
                )
            )
            continue
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=root,
                shell=True,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
            duration = time.perf_counter() - started
            stdout = completed.stdout.strip().replace("\n", "\\n")[:500]
            stderr = completed.stderr.strip().replace("\n", "\\n")[:500]
            artifacts.append(
                f"command={command!r}; exit_code={completed.returncode}; duration_seconds={duration:.3f}; "
                f"stdout={stdout!r}; stderr={stderr!r}"
            )
            if completed.returncode != 0:
                failed_checks.append(command)
                failure_classifications.append(
                    failure_classification(
                        command=command,
                        category="validation_failure",
                        message="validation command exited with non-zero status",
                        details={"exit_code": completed.returncode},
                    )
                )
        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - started
            stdout = (exc.stdout or "").strip().replace("\n", "\\n")[:500] if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "").strip().replace("\n", "\\n")[:500] if isinstance(exc.stderr, str) else ""
            artifacts.append(
                f"command={command!r}; exit_code=timeout; duration_seconds={duration:.3f}; "
                f"timeout_seconds={timeout_seconds}; stdout={stdout!r}; stderr={stderr!r}"
            )
            failed_checks.append(command)
            failure_classifications.append(
                failure_classification(
                    command=command,
                    category="timeout",
                    message="validation command exceeded timeout",
                    details={"timeout_seconds": timeout_seconds},
                )
            )
        except OSError as exc:
            duration = time.perf_counter() - started
            artifacts.append(
                f"command={command!r}; exit_code=environment_error; duration_seconds={duration:.3f}; "
                f"exception_type={type(exc).__name__!r}; error={str(exc)!r}"
            )
            failed_checks.append(command)
            failure_classifications.append(
                failure_classification(
                    command=command,
                    category="environment_failure",
                    message="validation command could not be executed by the local runner",
                    details={"exception_type": type(exc).__name__},
                )
            )

    # Run drift checks as additional structural validation.
    try:
        from .boundary import check_plan_scope, analyze_plan_drift, analyze_terminology_drift
        scope_findings = check_plan_scope(plan_id=plan_id, cwd=root)
        import_findings = analyze_plan_drift(plan_id=plan_id, cwd=root)
        term_findings = analyze_terminology_drift(plan_id=plan_id, cwd=root)
        drift_findings = list(scope_findings) + list(import_findings) + list(term_findings)
        if drift_findings:
            for f in drift_findings:
                artifacts.append(
                    f"drift_check={f.drift_type}; severity={f.severity}; "
                    f"evidence={f.evidence[:200]}; recommendation={f.recommendation[:200]}"
                )
            high_drift = [f for f in drift_findings if f.severity == "high"]
            if high_drift:
                for f in high_drift[:5]:
                    failed_checks.append(f"drift:{f.drift_type}:{f.evidence[:120]}")
                    failure_classifications.append(
                        failure_classification(
                            command=f"drift:{f.drift_type}",
                            category="drift_violation",
                            message=f.evidence[:200],
                            details={"drift_type": f.drift_type, "severity": f.severity, "recommendation": f.recommendation},
                        )
                    )
    except Exception:
        pass  # best-effort; drift checks are supplementary

    result = "pass" if not failed_checks else "fail"
    return record_verification(
        plan_id=plan_id,
        command=" && ".join(commands),
        result=result,
        artifacts=artifacts,
        failed_checks=failed_checks,
        failure_classifications=failure_classifications,
        environment=environment,
        trust_level="local_shell",
        cwd=cwd,
    )
