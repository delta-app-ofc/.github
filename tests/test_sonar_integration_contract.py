"""Simula APIs: não lê conta Sonar/GitHub nem publica comentários reais."""
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
from scripts.sonar_policy import API, decide, evaluate_pr, sonar_snapshot, metric_value


class FakeGitHub:
    def __init__(self, changed=False, existing=False):
        self.posts, self.reads = [], 0
        self.changed, self.existing = changed, existing

    def call(self, path, method="GET", data=None):
        if method != "GET":
            self.posts.append((path, method, data))
            return {}
        if path.endswith("/pulls/1"):
            self.reads += 1
            return {"state": "open", "head": {"sha": "changed" if self.changed and self.reads > 1 else "abc"},
                    "base": {"ref": "main"}, "user": {"login": "author"}}
        if path == "/user":
            return {"login": "automation"}
        raise AssertionError(path)

    def pages(self, path):
        if path.endswith("/comments"):
            return [{"id": 4, "body": "<!-- delta-sonar-report -->", "user": {"login": "automation"}}] if self.existing else []
        raise AssertionError(path)


class FakeSonar:
    base, token = "https://sonarcloud.io", "synthetic"

    def __init__(self, sha="abc", coverage="80", changed=False, absent=False,
                 measures=None, tree=None):
        self.sha, self.coverage, self.changed, self.absent, self.reads = sha, coverage, changed, absent, 0
        self.measures = measures
        self.calls = []
        self.tree = tree or {"baseComponent": {"key": "project", "pullRequest": "1"},
                             "paging": {"total": 1}, "components": [{"key": "project:file.py"}]}

    def call(self, path):
        self.calls.append(path)
        if path.startswith("/api/ce/activity?"):
            self.reads += 1
            return {"tasks": [] if self.absent else [{"id": "changed" if self.changed and self.reads > 1 else "task1", "status": "SUCCESS"}]}
        if path.startswith("/api/ce/task?"):
            return {"task": {"id": "task1", "analysisId": "analysis1", "scannerContext":
                    f"sonar.projectKey=project\nsonar.pullrequest.key=1\nsonar.scm.revision={self.sha}"}}
        if path.startswith("/api/measures/component?"):
            measures = self.measures
            if measures is None:
                measures = [{"metric": "new_lines_to_cover", "periods": [{"index": 1, "value": "10"}]},
                            {"metric": "new_coverage", "periods": [{"index": 1, "value": self.coverage}]}]
            return {"component": {"measures": measures}}
        if path.startswith("/api/components/tree?"):
            return self.tree
        if path.startswith("/api/issues/search?"):
            return {"issues": [{"type": "BUG", "severity": "CRITICAL"}, {"type": "CODE_SMELL", "severity": "CRITICAL"}], "paging": {"total": 2}}
        raise AssertionError(path)


class IntegrationContractTests(unittest.TestCase):
    def test_metric_payloads_match_cloud_and_server_formats(self):
        self.assertEqual(metric_value({"periods": [{"index": 1, "value": "0"}]}), "0")
        self.assertEqual(metric_value({"period": {"value": "70"}}), "70")
        self.assertEqual(metric_value({"value": "80"}), "80")
        self.assertIsNone(metric_value({}))

    def test_snapshot_accepts_current_sha_and_period_values(self):
        sonar = FakeSonar()
        issues, measures, no_files_analyzed = sonar_snapshot(sonar, "project", 1, "abc")
        self.assertEqual(len(issues), 2)
        self.assertEqual(measures["new_coverage"], "80")
        self.assertFalse(no_files_analyzed)
        measures_path = next(path for path in sonar.calls if path.startswith("/api/measures/component?"))
        metrics = parse_qs(urlparse(measures_path).query)["metricKeys"][0].split(",")
        self.assertIn("new_lines", metrics)

    def test_empty_inventory_is_n_a_only_for_the_matching_current_pr(self):
        empty_tree = {"baseComponent": {"key": "project", "pullRequest": "1"},
                      "paging": {"total": 0}, "components": []}
        sonar = FakeSonar(measures=[], tree=empty_tree)
        issues, measures, no_files_analyzed = sonar_snapshot(
            sonar, "project", 1, "abc")
        self.assertEqual(measures, {})
        self.assertTrue(no_files_analyzed)
        tree_path = next(path for path in sonar.calls if path.startswith("/api/components/tree?"))
        tree_query = parse_qs(urlparse(tree_path).query)
        self.assertEqual(tree_query, {"component": ["project"], "pullRequest": ["1"],
                                      "qualifiers": ["FIL"], "ps": ["1"]})

    def test_empty_measures_with_a_file_remain_unavailable(self):
        sonar = FakeSonar(measures=[])
        with self.assertRaisesRegex(ValueError, "new_lines_to_cover"):
            issues, measures, no_files_analyzed = sonar_snapshot(sonar, "project", 1, "abc")
            decide(issues, measures, no_files_analyzed=no_files_analyzed)

    def test_empty_inventory_requires_matching_identity_and_valid_shape(self):
        invalid_trees = [
            {"baseComponent": {"key": "other", "pullRequest": "1"}, "paging": {"total": 0}, "components": []},
            {"baseComponent": {"key": "project", "pullRequest": "2"}, "paging": {"total": 0}, "components": []},
            {"baseComponent": {"key": "project", "pullRequest": "1"}, "paging": {"total": "NaN"}, "components": []},
            {"baseComponent": {"key": "project", "pullRequest": "1"}, "paging": {"total": 0}, "components": [{}]},
        ]
        for tree in invalid_trees:
            with self.subTest(tree=tree), self.assertRaises(ValueError):
                sonar_snapshot(FakeSonar(measures=[], tree=tree), "project", 1, "abc")

    def test_security_still_blocks_when_empty_inventory_makes_coverage_n_a(self):
        github = FakeGitHub()
        empty_tree = {"baseComponent": {"key": "project", "pullRequest": "1"},
                      "paging": {"total": 0}, "components": []}
        sonar = FakeSonar(measures=[], tree=empty_tree)
        original = sonar.call

        def response(path):
            if path.startswith("/api/issues/search?"):
                return {"issues": [{"type": "VULNERABILITY", "severity": "CRITICAL"}],
                        "paging": {"total": 1}}
            return original(path)

        with patch.object(sonar, "call", side_effect=response):
            evaluate_pr(github, sonar, "owner/repo", 1, "project")
        self.assertEqual(github.posts[0][2]["state"], "failure")
        self.assertIn("N/A: nenhum arquivo analisado nesta PR", github.posts[1][2]["body"])
        self.assertIn("Seguran", github.posts[1][2]["body"])

    def test_empty_inventory_without_security_approves_with_explicit_n_a(self):
        github = FakeGitHub()
        empty_tree = {"baseComponent": {"key": "project", "pullRequest": "1"},
                      "paging": {"total": 0}, "components": []}
        evaluate_pr(github, FakeSonar(measures=[], tree=empty_tree), "owner/repo", 1, "project")
        self.assertEqual(github.posts[0][2]["state"], "success")
        self.assertIn("N/A: nenhum arquivo analisado nesta PR", github.posts[1][2]["body"])
        self.assertRegex(github.posts[1][2]["body"], r"Seguran.a: 0")

    def test_inventory_api_failure_does_not_authorize_n_a(self):
        github, sonar = FakeGitHub(), FakeSonar(measures=[])
        original = sonar.call

        def response(path):
            if path.startswith("/api/components/tree?"):
                raise OSError("temporary API outage")
            return original(path)

        with patch.object(sonar, "call", side_effect=response):
            evaluate_pr(github, sonar, "owner/repo", 1, "project")
        self.assertEqual(github.posts[0][2]["state"], "failure")
        self.assertIn("Validação indisponível", github.posts[1][2]["body"])

    def test_stale_missing_and_racing_analysis_fail_closed(self):
        for sonar in [FakeSonar(sha="old"), FakeSonar(absent=True), FakeSonar(changed=True)]:
            with self.subTest(sonar=sonar), self.assertRaises(ValueError):
                sonar_snapshot(sonar, "project", 1, "abc")

    def test_latest_failed_task_does_not_fall_back_to_old_success(self):
        sonar = FakeSonar()
        original = sonar.call
        def response(path):
            if path.startswith("/api/ce/activity?"):
                return {"tasks": [{"id": "new", "status": "FAILED"}, {"id": "old", "status": "SUCCESS"}]}
            return original(path)
        with patch.object(sonar, "call", side_effect=response), self.assertRaises(ValueError):
            sonar_snapshot(sonar, "project", 1, "abc")

    def test_publishes_status_and_separate_comment(self):
        github = FakeGitHub()
        evaluate_pr(github, FakeSonar(), "owner/repo", 1, "project")
        self.assertEqual(github.posts[0][2]["state"], "success")
        self.assertNotIn("Aprovações", github.posts[1][2]["body"])
        self.assertIn("somente aviso", github.posts[1][2]["body"])

    def test_low_coverage_does_not_approve(self):
        github = FakeGitHub()
        evaluate_pr(github, FakeSonar(coverage="69"), "owner/repo", 1, "project")
        self.assertEqual(github.posts[0][2]["state"], "failure")

    def test_old_grave_security_is_warning_and_does_not_block_fix_pr(self):
        github, sonar = FakeGitHub(), FakeSonar()
        original = sonar.call
        def response(path):
            if path.startswith("/api/issues/search?"):
                issues = [{"type": "VULNERABILITY", "severity": "CRITICAL"}] if "branch=main" in path else []
                return {"issues": issues, "paging": {"total": len(issues)}}
            return original(path)
        with patch.object(sonar, "call", side_effect=response):
            evaluate_pr(github, sonar, "owner/repo", 1, "project")
        self.assertEqual(github.posts[0][2]["state"], "success")
        self.assertIn("SECURITY=1", github.posts[1][2]["body"])
        self.assertIn("somente aviso", github.posts[1][2]["body"])

    def test_does_not_publish_for_obsolete_head(self):
        github = FakeGitHub(changed=True)
        evaluate_pr(github, FakeSonar(), "owner/repo", 1, "project")
        self.assertEqual(github.posts, [])

    def test_updates_own_comment_instead_of_duplicating(self):
        github = FakeGitHub(existing=True)
        evaluate_pr(github, FakeSonar(), "owner/repo", 1, "project")
        self.assertEqual(github.posts[1][1], "PATCH")
        self.assertTrue(github.posts[1][0].endswith("/comments/4"))

    def test_api_refuses_insecure_or_embedded_credentials(self):
        for url in ["http://sonarcloud.io", "https://user:pass@sonarcloud.io", "https://sonarcloud.io?token=value"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                API(url, "synthetic")

    def test_github_pagination(self):
        api = API("https://api.github.com", "synthetic")
        with patch.object(api, "call", side_effect=[[{}] * 100, [{"last": True}]]):
            self.assertEqual(len(api.pages("/items")), 101)
