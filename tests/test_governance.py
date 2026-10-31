"""Casos de governança sem editar PRs nem solicitar revisores reais."""
import os
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import patch
from scripts import route_checks, validate_commits, validate_gitignore


class GovernanceTests(unittest.TestCase):
    def test_conventional_subjects(self):
        for subject in ["test: adiciona validações", "fix(api): corrige entrada", "Initial Commit", "Merge branch 'main'"]:
            self.assertTrue(validate_commits.is_valid_subject(subject))
        for subject in ["arrumei", "feat:", "unknown: altera código", "test: "]:
            self.assertFalse(validate_commits.is_valid_subject(subject))

    def test_ignore_rules_and_env_file_detection(self):
        self.assertEqual(validate_gitignore.active_rules("# comentário\n.env\n\n dist/ \n"), [".env", "dist/"])
        self.assertTrue(validate_gitignore.contains_required_rules([".env", "dist/"], [".env"]))
        self.assertFalse(validate_gitignore.contains_required_rules(["dist/"], [".env"]))
        result = subprocess.CompletedProcess([], 0, ".env\n.env.example\nsub/.env.production\n.env.test\n")
        with patch("subprocess.run", return_value=result):
            self.assertEqual(validate_gitignore.tracked_env_files(Path(".")), [".env", "sub/.env.production"])

    def test_short_description_and_template_rejected(self):
        for body in ["", "## 📄 Descrição\nCurta\n## ✨ Tipo de PR",
                     "## 📄 Descrição\n> Descreva o que foi implementado.\n## ✨ Tipo de PR"]:
            self.assertTrue(route_checks.check_description(body))
        self.assertFalse(route_checks.check_description("## 📄 Descrição\nAdiciona testes de contratos e relatórios de qualidade para o pipeline.\n## ✨ Tipo de PR"))

    def test_missing_checkboxes_are_reported_individually(self):
        errors = route_checks.check_options(["scope"], ["type"], ["required1", "required2"], ["ai"], "")
        self.assertEqual(len(errors), 5)
        self.assertEqual(route_checks.check_options(["scope"], ["type"], ["required1"], ["ai"], "SCOPE TYPE required1 AI"), [])

    def test_reviewers_deduplicated_and_unselected_scopes_ignored(self):
        body = "- [x] API REST (Spring Boot)\n- [x] Mobile (Android / iOS / Firebase)\n- [ ] IA Multiagente (FastAPI / Langgraph)"
        with patch.dict(os.environ, {"PR_BODY": body, "PR_URL": "https://github.com/example/repo/pull/1", "ORG_NAME": "delta-app-ofc"}), patch("subprocess.run") as command:
            runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/route_reviewers.py"))
        command.assert_called_once_with(["gh", "pr", "edit", "https://github.com/example/repo/pull/1", "--add-reviewer", "delta-app-ofc/backend-2ano"], check=False)
