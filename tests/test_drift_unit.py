"""Unit tests for drift analysis rules and text matching."""

from __future__ import annotations

import unittest

from abh.drift import DRIFT_RULES, analyze_drift_text, matched_span, excerpt_for_span


class DriftAnalysisTests(unittest.TestCase):
    """Tests for the drift text analysis engine."""

    def test_boundary_drift_matched(self) -> None:
        findings = analyze_drift_text("The module boundary was moved to a new location")
        self.assertTrue(any(f.drift_type == "boundary_drift" for f in findings))

    def test_dependency_drift_matched(self) -> None:
        findings = analyze_drift_text("Added an external database dependency")
        self.assertTrue(any(f.drift_type == "dependency_drift" for f in findings))

    def test_test_drift_matched(self) -> None:
        findings = analyze_drift_text("We skipped tests for this feature")
        self.assertTrue(any(f.drift_type == "test_drift" for f in findings))

    def test_terminology_drift_matched(self) -> None:
        findings = analyze_drift_text("The API was renamed to v2")
        self.assertTrue(any(f.drift_type == "terminology_drift" for f in findings))

    def test_no_drift_for_clean_text(self) -> None:
        findings = analyze_drift_text("This is a normal clean commit message")
        self.assertEqual(len(findings), 0)

    def test_chinese_boundary_drift(self) -> None:
        findings = analyze_drift_text("模块边界混入了新的逻辑")
        self.assertTrue(any(f.drift_type == "boundary_drift" for f in findings))

    def test_chinese_dependency_drift(self) -> None:
        findings = analyze_drift_text("新增了外部数据库依赖")
        self.assertTrue(any(f.drift_type == "dependency_drift" for f in findings))

    def test_matched_span_returns_correct_location(self) -> None:
        span = matched_span("hello world", "hello world".lower(), "world")
        self.assertEqual(span.get("text"), "world")
        self.assertEqual(span.get("start"), 6)
        self.assertEqual(span.get("end"), 11)

    def test_matched_span_returns_empty_for_missing(self) -> None:
        span = matched_span("hello", "hello".lower(), "absent")
        self.assertEqual(span, {})

    def test_excerpt_for_span(self) -> None:
        text = "0123456789" * 10  # 100 chars
        excerpt = excerpt_for_span(text, 50, 54, radius=10)
        self.assertIn("4567", excerpt)

    def test_drift_rules_have_required_fields(self) -> None:
        for drift_type, rule in DRIFT_RULES.items():
            self.assertIn("keywords", rule, f"{drift_type} missing keywords")
            self.assertIn("severity", rule, f"{drift_type} missing severity")
            self.assertIn("recommendation", rule, f"{drift_type} missing recommendation")


if __name__ == "__main__":
    unittest.main()