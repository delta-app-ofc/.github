"""Contratos de bloqueio e classificação da política Sonar, sem chamadas externas."""
import unittest
from scripts.sonar_policy import decide, scanner_context_matches


class PolicyTests(unittest.TestCase):
    def test_security_blocks_even_with_full_coverage(self):
        result = decide([{"type": "VULNERABILITY", "severity": "CRITICAL"}], {"new_lines_to_cover": "10", "new_coverage": "100"})
        self.assertFalse(result["passed"])
        self.assertEqual(result["counts"]["SECURITY"], 1)

    def test_reliability_only_warns(self):
        issues = [{"impacts": [{"softwareQuality": "RELIABILITY", "severity": "HIGH"}]}]
        result = decide(issues, {"new_lines_to_cover": "1", "new_coverage": "70"}, approvals=1)
        self.assertTrue(result["passed"])
        self.assertEqual(result["counts"]["RELIABILITY"], 1)
        self.assertEqual(result["required"], 1)
        self.assertEqual(result["approvals"], 1)

    def test_maintenance_only_warns(self):
        result = decide([{"type": "CODE_SMELL", "severity": "CRITICAL"}], {"new_lines_to_cover": "0"})
        self.assertTrue(result["passed"])
        self.assertEqual(result["counts"]["MAINTAINABILITY"], 1)
        self.assertIsNone(result["coverage"])

    def test_zero_coverable_lines_are_not_applicable(self):
        result = decide([], {"new_lines": "8", "new_lines_to_cover": "0"})
        self.assertTrue(result["passed"])
        self.assertIsNone(result["coverage"])

    def test_zero_new_lines_is_evidence_for_not_applicable(self):
        result = decide([], {"new_lines": "0"})
        self.assertTrue(result["passed"])
        self.assertIsNone(result["coverage"])

    def test_security_still_blocks_when_coverage_is_not_applicable(self):
        result = decide([{"type": "VULNERABILITY", "severity": "CRITICAL"}], {"new_lines": "0"})
        self.assertFalse(result["passed"])
        self.assertIsNone(result["coverage"])
        self.assertEqual(result["counts"]["SECURITY"], 1)

    def test_coverage_has_no_small_change_exception(self):
        for percentage, expected in [("69.99", False), ("70", True), ("100", True)]:
            with self.subTest(percentage=percentage):
                self.assertEqual(decide([], {"new_lines_to_cover": "1", "new_coverage": percentage})["passed"], expected)

    def test_smaller_issues_do_not_block(self):
        issues = [{"type": "VULNERABILITY", "severity": "MAJOR"},
                  {"type": "BUG", "severity": "MINOR"},
                  {"impacts": [{"softwareQuality": "SECURITY", "severity": "MEDIUM"}]}]
        result = decide(issues, {"new_lines_to_cover": "0"})
        self.assertTrue(result["passed"])
        self.assertEqual(sum(result["counts"].values()), 0)

    def test_missing_metrics_are_unavailable_not_zero_or_not_applicable(self):
        for measures in [
            {},
            {"new_lines": "4"},
            {"new_lines": "4", "new_coverage": "80"},
            {"new_lines_to_cover": "4"},
        ]:
            with self.subTest(measures=measures), self.assertRaises(ValueError):
                decide([], measures)

    def test_invalid_coverage_rejected(self):
        for value in ["-1", "101", "nan"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                decide([], {"new_lines_to_cover": "1", "new_coverage": value})

    def test_invalid_metric_values_are_rejected_even_when_coverage_is_not_applicable(self):
        for name, value in [
            ("new_lines", "NaN"),
            ("new_lines", "inf"),
            ("new_lines", "-1"),
            ("new_lines", "1.5"),
            ("new_lines_to_cover", "Infinity"),
            ("new_lines_to_cover", "-1"),
            ("new_coverage", "inf"),
        ]:
            measures = {"new_lines_to_cover": "0"}
            measures[name] = value
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                decide([], measures)

    def test_resolved_issues_do_not_block(self):
        self.assertTrue(decide([{"type": "BUG", "severity": "CRITICAL", "resolution": "FIXED"}], {"new_lines_to_cover": "0"})["passed"])

    def test_unknown_classification_blocks_instead_of_ignoring(self):
        with self.assertRaises(ValueError):
            decide([{"type": "NEW_KIND", "severity": "CRITICAL"}], {"new_lines_to_cover": "0"})

    def test_multi_impact_issue_with_security_blocks(self):
        issue = {"impacts": [{"softwareQuality": "SECURITY", "severity": "HIGH"}, {"softwareQuality": "RELIABILITY", "severity": "HIGH"}]}
        result = decide([issue], {"new_lines_to_cover": "0"})
        self.assertFalse(result["passed"])
        self.assertEqual(result["counts"]["RELIABILITY"], 1)

    def test_scanner_context_binds_project_pr_and_revision(self):
        context = "  - sonar.projectKey=delta\n  - sonar.pullrequest.key=12\n  - sonar.scm.revision=abc"
        self.assertTrue(scanner_context_matches(context, "delta", 12, "abc"))
        self.assertFalse(scanner_context_matches(context, "other", 12, "abc"))
        self.assertFalse(scanner_context_matches(context, "delta", 13, "abc"))
        self.assertFalse(scanner_context_matches(context, "delta", 12, "old"))


if __name__ == "__main__":
    unittest.main()
