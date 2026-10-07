"""Testes locais do bypass, sem token nem chamadas reais ao GitHub."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_ci_bypass as bypass


def label_event(actor="samuelpimentah", action="labeled", label="ci-bypass"):
    return {"actor": {"login": actor}, "event": action, "label": {"name": label}}


class BypassTests(unittest.TestCase):
    def test_only_samuel_can_authorize(self):
        self.assertTrue(bypass.authorized_label_actor([label_event()]))
        self.assertFalse(bypass.authorized_label_actor([label_event("another-user")]))

    def test_missing_event_does_not_authorize(self):
        self.assertFalse(bypass.authorized_label_actor([]))

    def test_removed_label_revokes_authorization(self):
        self.assertFalse(
            bypass.authorized_label_actor([label_event(), label_event(action="unlabeled")])
        )

    def test_reapplication_by_another_user_revokes_authorization(self):
        self.assertFalse(
            bypass.authorized_label_actor([
                label_event(), label_event(action="unlabeled"), label_event("another-user")
            ])
        )

    def test_unrelated_labels_do_not_change_authorization(self):
        self.assertTrue(
            bypass.authorized_label_actor([label_event(), label_event("another-user", label="bug")])
        )

    def test_app_cannot_impersonate_authorized_user(self):
        event = label_event()
        event["performed_via_github_app"] = {"id": 1}
        self.assertFalse(bypass.authorized_label_actor([event]))

    def test_null_actor_does_not_authorize(self):
        event = label_event()
        event["actor"] = None
        self.assertFalse(bypass.authorized_label_actor([event]))

    @patch.object(bypass, "github_get")
    def test_pagination(self, api):
        api.side_effect = [[label_event("another-user")] * 100, [label_event()]]
        events = bypass.github_paginate("repos/org/repo/issues/1/timeline")
        self.assertTrue(bypass.authorized_label_actor(events))
        self.assertEqual(api.call_count, 2)

    def run_main(self, responses):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            event_path = root / "event.json"
            event_path.write_text(json.dumps({"pull_request": {"number": 1}}), encoding="utf-8")
            output_path = root / "output"
            summary_path = root / "summary"
            environment = {
                "GITHUB_EVENT_PATH": str(event_path),
                "GITHUB_REPOSITORY": "delta-app-ofc/example",
                "GITHUB_OUTPUT": str(output_path),
                "GITHUB_STEP_SUMMARY": str(summary_path),
            }
            with patch.dict(os.environ, environment), patch.object(bypass, "github_get") as api:
                api.side_effect = responses
                bypass.main()
            return (
                output_path.read_text(encoding="utf-8"),
                summary_path.read_text(encoding="utf-8") if summary_path.exists() else "",
            )

    def test_no_label_runs_normal_checks(self):
        output, summary = self.run_main([[]])
        self.assertEqual(output, "enabled=false\n")
        self.assertEqual(summary, "")

    def test_authorized_label_skips_checks_and_records_summary(self):
        output, summary = self.run_main([[{"name": "ci-bypass"}], [label_event()]])
        self.assertEqual(output, "enabled=true\n")
        self.assertIn("não foram executadas", summary)
        self.assertIn("samuelpimentah", summary)

    def test_unauthorized_label_runs_normal_checks(self):
        output, summary = self.run_main([[{"name": "ci-bypass"}], [label_event("another-user")]])
        self.assertEqual(output, "enabled=false\n")
        self.assertEqual(summary, "")

    def test_api_error_does_not_authorize(self):
        with self.assertRaises(ConnectionError):
            self.run_main([ConnectionError("API indisponível")])


if __name__ == "__main__":
    unittest.main()
