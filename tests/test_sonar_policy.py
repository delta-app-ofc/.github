"""Contratos de bloqueio, classificação e validade de revisões sem chamadas externas."""
import unittest
from scripts.sonar_policy import decide, count_approvals, scanner_context_matches


class PolicyTests(unittest.TestCase):
    def test_security_blocks_even_with_coverage_and_reviews(self):
        result = decide([{"type": "VULNERABILITY", "severity": "CRITICAL"}], {"new_lines_to_cover": "10", "new_coverage": "100"}, 5, 1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["counts"]["SECURITY"], 1)

    def test_reliability_requires_one_more_than_baseline(self):
        issues = [{"impacts": [{"softwareQuality": "RELIABILITY", "severity": "HIGH"}]}]
        measures = {"new_lines_to_cover": "1", "new_coverage": "70"}
        self.assertFalse(decide(issues, measures, 2, 2)["passed"])
        self.assertTrue(decide(issues, measures, 3, 2)["passed"])

    def test_maintenance_only_warns(self):
        result = decide([{"type": "CODE_SMELL", "severity": "CRITICAL"}], {"new_lines_to_cover": "0"}, 0, 0)
        self.assertTrue(result["passed"])
        self.assertEqual(result["counts"]["MAINTAINABILITY"], 1)
        self.assertIsNone(result["coverage"])

    def test_coverage_has_no_small_change_exception(self):
        for percentage, expected in [("69.99", False), ("70", True), ("100", True)]:
            with self.subTest(percentage=percentage):
                self.assertEqual(decide([], {"new_lines_to_cover": "1", "new_coverage": percentage}, 0, 0)["passed"], expected)

    def test_smaller_issues_do_not_block_or_require_extra_review(self):
        issues = [{"type": "VULNERABILITY", "severity": "MAJOR"},
                  {"type": "BUG", "severity": "MINOR"},
                  {"impacts": [{"softwareQuality": "SECURITY", "severity": "MEDIUM"}]}]
        result = decide(issues, {"new_lines_to_cover": "0"}, 1, 1)
        self.assertTrue(result["passed"])
        self.assertEqual(result["required"], 1)
        self.assertEqual(sum(result["counts"].values()), 0)

    def test_missing_report_is_not_zero_new_lines(self):
        with self.assertRaises(KeyError):
            decide([], {}, 0, 0)
        with self.assertRaises(KeyError):
            decide([], {"new_lines_to_cover": "1"}, 0, 0)

    def test_invalid_coverage_rejected(self):
        for value in ["-1", "101", "nan"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                decide([], {"new_lines_to_cover": "1", "new_coverage": value}, 0, 0)

    def test_resolved_issues_do_not_block(self):
        self.assertTrue(decide([{"type": "BUG", "severity": "CRITICAL", "resolution": "FIXED"}], {"new_lines_to_cover": "0"}, 0, 0)["passed"])

    def test_unknown_classification_blocks_instead_of_ignoring(self):
        with self.assertRaises(ValueError):
            decide([{"type": "NEW_KIND", "severity": "CRITICAL"}], {"new_lines_to_cover": "0"}, 0, 0)

    def test_multi_impact_issue_counts_security_and_reliability(self):
        issue = {"impacts": [{"softwareQuality": "SECURITY", "severity": "HIGH"}, {"softwareQuality": "RELIABILITY", "severity": "HIGH"}]}
        result = decide([issue], {"new_lines_to_cover": "0"}, 1, 1)
        self.assertEqual(result["required"], 2)
        self.assertFalse(result["passed"])

    def test_only_current_human_writer_approval_counts(self):
        def review(identifier, login, state="APPROVED", sha="current", kind="User"):
            return {"id": identifier, "user": {"login": login, "type": kind}, "state": state, "commit_id": sha}
        reviews = [review(1, "author"), review(2, "old", sha="old"), review(3, "reader"),
                   review(4, "bot", kind="Bot"), review(5, "revoked"),
                   review(6, "revoked", state="DISMISSED"), review(7, "writer"),
                   review(8, "writer", state="COMMENTED")]
        permissions = {name: "write" for name in ["author", "old", "bot", "revoked", "writer"]}
        permissions["reader"] = "read"
        self.assertEqual(count_approvals(reviews, "current", "author", permissions), 1)

    def test_scanner_context_binds_project_pr_and_revision(self):
        context = "  - sonar.projectKey=delta\n  - sonar.pullrequest.key=12\n  - sonar.scm.revision=abc"
        self.assertTrue(scanner_context_matches(context, "delta", 12, "abc"))
        self.assertFalse(scanner_context_matches(context, "other", 12, "abc"))
        self.assertFalse(scanner_context_matches(context, "delta", 13, "abc"))
        self.assertFalse(scanner_context_matches(context, "delta", 12, "old"))


if __name__ == "__main__":
    unittest.main()
