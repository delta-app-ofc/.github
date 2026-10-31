import unittest
from unittest.mock import Mock
from scripts.configure_sonar_checks import configure


class ConfigureTests(unittest.TestCase):
    def test_preserves_existing_checks_and_strictness(self):
        api = Mock()
        api.call.side_effect = [{"required_status_checks": {"strict": False,
                                "checks": [{"context": "Existing", "app_id": 42}], "contexts": ["Existing", "Legacy"]}}, {}]
        configure(api, "delta-app-ofc/example", "main", ["Tests", "Tests"])
        payload = api.call.call_args.args[2]
        self.assertFalse(payload["strict"])
        self.assertEqual(payload["checks"], [{"context": "Existing", "app_id": 42}, {"context": "Legacy"},
                                            {"context": "Delta / Política Sonar"}, {"context": "Tests"}])

    def test_failure_reading_protection_does_not_write(self):
        api = Mock()
        api.call.side_effect = RuntimeError("permission denied")
        with self.assertRaises(RuntimeError):
            configure(api, "delta-app-ofc/example", "main", [])
        self.assertEqual(api.call.call_count, 1)

    def test_rejects_other_organization_and_empty_check(self):
        api = Mock()
        for repo, checks in [("other/example", []), ("delta-app-ofc/example", [""])]:
            with self.assertRaises(ValueError):
                configure(api, repo, "main", checks)
        api.call.assert_not_called()
