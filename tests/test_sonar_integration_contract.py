"""Simula APIs: não lê conta Sonar/GitHub nem publica comentários reais."""
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from scripts.sonar_policy import API, evaluate_pr, sonar_snapshot


class FakeGitHub:
    def __init__(self, changed=False, broken=False, existing=False):
        self.posts, self.reads = [], 0
        self.changed, self.broken, self.existing = changed, broken, existing

    def call(self, path, method="GET", data=None):
        if method != "GET":
            self.posts.append((path, method, data))
            return {}
        if path.endswith("/pulls/1"):
            self.reads += 1
            return {"state": "open", "head": {"sha": "changed" if self.changed and self.reads > 1 else "abc"},
                    "base": {"ref": "main"}, "user": {"login": "author"}}
        if path.endswith("/protection"):
            if self.broken:
                raise HTTPError(path, 403, "Forbidden", {}, None)
            return {"required_pull_request_reviews": {"required_approving_review_count": 1}}
        if "/rules/branches/" in path:
            return [{"type": "pull_request", "parameters": {"required_approving_review_count": 2}}]
        if path.endswith("/permission"):
            return {"permission": "write"}
        if path == "/user":
            return {"login": "automation"}
        raise AssertionError(path)

    def pages(self, path):
        if path.endswith("/reviews"):
            return [{"id": i, "state": "APPROVED", "commit_id": "abc", "user": {"login": f"reviewer{i}", "type": "User"}} for i in range(1, 4)]
        if path.endswith("/comments"):
            return [{"id": 4, "body": "<!-- delta-sonar-report -->", "user": {"login": "automation"}}] if self.existing else []
        raise AssertionError(path)


class FakeSonar:
    base, token = "https://sonarcloud.io", "synthetic"

    def __init__(self, sha="abc", coverage="80", changed=False, absent=False):
        self.sha, self.coverage, self.changed, self.absent, self.reads = sha, coverage, changed, absent, 0

    def call(self, path):
        if path.startswith("/api/ce/activity?"):
            self.reads += 1
            return {"tasks": [] if self.absent else [{"id": "changed" if self.changed and self.reads > 1 else "task1", "status": "SUCCESS"}]}
        if path.startswith("/api/ce/task?"):
            return {"task": {"id": "task1", "analysisId": "analysis1", "scannerContext":
                    f"sonar.projectKey=project\nsonar.pullrequest.key=1\nsonar.scm.revision={self.sha}"}}
        if path.startswith("/api/measures/component?"):
            return {"component": {"measures": [{"metric": "new_lines_to_cover", "period": {"value": "10"}},
                                                {"metric": "new_coverage", "period": {"value": self.coverage}}]}}
        if path.startswith("/api/issues/search?"):
            return {"issues": [{"type": "BUG"}, {"type": "CODE_SMELL"}], "paging": {"total": 2}}
        raise AssertionError(path)


class IntegrationContractTests(unittest.TestCase):
    def test_snapshot_accepts_current_sha_and_period_values(self):
        issues, measures = sonar_snapshot(FakeSonar(), "project", 1, "abc")
        self.assertEqual(len(issues), 2)
        self.assertEqual(measures["new_coverage"], "80")

    def test_stale_missing_and_racing_analysis_fail_closed(self):
        for sonar in [FakeSonar(sha="old"), FakeSonar(absent=True), FakeSonar(changed=True)]:
            with self.subTest(sonar=sonar), self.assertRaises(ValueError):
                sonar_snapshot(sonar, "project", 1, "abc")

    def test_publishes_status_and_separate_comment_using_maximum_baseline(self):
        github = FakeGitHub()
        evaluate_pr(github, FakeSonar(), "owner/repo", 1, "project")
        self.assertEqual(github.posts[0][2]["state"], "success")
        self.assertIn("3/3", github.posts[1][2]["body"])
        self.assertIn("somente aviso", github.posts[1][2]["body"])

    def test_low_coverage_and_permission_errors_do_not_approve(self):
        for github, sonar in [(FakeGitHub(), FakeSonar(coverage="69")), (FakeGitHub(broken=True), FakeSonar())]:
            with self.subTest(github=github):
                evaluate_pr(github, sonar, "owner/repo", 1, "project")
                self.assertEqual(github.posts[0][2]["state"], "failure")

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
