"""Valida que falhas de publicação do relatório não alterem o resultado dos testes."""
from pathlib import Path
import json
import shutil
import subprocess
import unittest

import yaml


class ReportCiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        node = shutil.which("node")
        if not node:
            raise RuntimeError("Node.js é necessário para testar o reporter reutilizável")
        cls.node = node
        workflow = Path(__file__).resolve().parents[1] / ".github/workflows/report_ci.yml"
        parsed = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        cls.script = parsed["jobs"]["report"]["steps"][0]["with"]["script"]

    def run_report(self, needs, **options):
        harness = r"""
const source = __SOURCE__;
const scenario = __SCENARIO__;
const sha = '0123456789abcdef0123456789abcdef01234567';
const originalBody = '## Descrição\nUma alteração de teste com descrição útil.\n\n' +
  '- [ ] O código foi devidamente testado e não causa novos bugs.';
const calls = { warnings: [], summary: '', body: originalBody };
const prEvent = { number: 7, head: { sha } };
const context = {
  payload: { pull_request: prEvent },
  repo: { owner: 'delta-app-ofc', repo: 'example' },
  runId: 23,
  workflow: 'Testes técnicos'
};
const process = {
  env: { NEEDS_RESULTS: scenario.invalidNeeds ? '{invalid' : JSON.stringify(scenario.needs) }
};
const core = {
  info: () => {},
  warning: message => calls.warnings.push(message),
  summary: {
    addRaw: text => { calls.summary += text; return core.summary; },
    write: async () => {}
  }
};
const jobs = Object.entries(scenario.needs).map(([name, result]) => ({
  name,
  conclusion: result.result,
  status: 'completed',
  steps: []
}));
const github = {
  paginate: async () => [],
  rest: {
    actions: {
      getWorkflowRun: async () => {
        if (scenario.failPreparation) throw new Error('synthetic read failure');
        return { data: { run_number: 23, html_url: 'https://example.test/run/23' } };
      },
      listJobsForWorkflowRun: async () => ({ data: { jobs } })
    },
    pulls: {
      get: async () => ({ data: { head: { sha }, body: originalBody } }),
      update: async ({ body }) => {
        if (scenario.failBody) throw new Error('synthetic PR update failure');
        calls.body = body;
        calls.bodyUpdated = true;
      }
    },
    issues: {
      listComments: async () => ({ data: [] }),
      createComment: async ({ body }) => {
        if (scenario.failComment) throw new Error('synthetic comment failure');
        calls.commentBody = body;
      },
      updateComment: async () => {}
    }
  }
};
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const run = new AsyncFunction('context', 'github', 'core', 'process', source);
run(context, github, core, process)
  .then(() => console.log(JSON.stringify(calls)))
  .catch(error => {
    console.error(error.stack || String(error));
    globalThis.process.exitCode = 1;
  });
""".replace("__SOURCE__", json.dumps(self.script)).replace(
            "__SCENARIO__", json.dumps({"needs": needs, **options})
        )
        result = subprocess.run(
            [self.node, "-e", harness], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=15
        )
        self.assertEqual(result.returncode, 0, (result.stdout or "") + (result.stderr or ""))
        return json.loads(result.stdout.strip().splitlines()[-1])

    def test_comment_failure_does_not_prevent_current_sha_marker_update(self):
        calls = self.run_report({"ci-tecnico": {"result": "success"}}, failComment=True)

        self.assertTrue(calls["bodyUpdated"])
        self.assertIn("<!-- delta-ci-result:0123456789abcdef0123456789abcdef01234567:success -->", calls["body"])
        self.assertIn("- [x] O código foi devidamente testado", calls["body"])
        self.assertIn("Não foi possível publicar o comentário do CI.", calls["warnings"])
        self.assertIn("Testes obrigatórios: **aprovados**", calls["summary"])

    def test_body_update_failure_is_reported_without_publishing_a_marker(self):
        calls = self.run_report({"ci-tecnico": {"result": "success"}}, failBody=True)

        self.assertNotIn("<!-- delta-ci-result:", calls["body"])
        self.assertIn("Não foi possível atualizar o resultado/checkbox", calls["warnings"][-1])
        self.assertIn("Corpo/checklist da PR: não atualizado", calls["summary"])

    def test_failed_cancelled_or_skipped_required_jobs_never_pass(self):
        for result in ("failure", "cancelled", "skipped"):
            with self.subTest(result=result):
                calls = self.run_report({"ci-tecnico": {"result": result}})

                self.assertIn("CI reprovado ❌", calls["commentBody"])
                self.assertIn(":failure -->", calls["body"])
                self.assertIn("- [ ] O código foi devidamente testado", calls["body"])
                self.assertIn("Testes obrigatórios: **reprovados**", calls["summary"])

    def test_preparation_failure_does_not_publish_a_false_marker(self):
        calls = self.run_report(
            {"ci-tecnico": {"result": "success"}}, failPreparation=True
        )

        self.assertNotIn("<!-- delta-ci-result:", calls["body"])
        self.assertNotIn("commentBody", calls)
        self.assertIn("SHA atual da PR não confirmado", calls["summary"])
        self.assertTrue(any("Não foi possível conferir" in item for item in calls["warnings"]))

    def test_invalid_job_results_are_reported_as_unavailable_without_a_marker(self):
        calls = self.run_report({}, invalidNeeds=True)

        self.assertNotIn("<!-- delta-ci-result:", calls["body"])
        self.assertNotIn("commentBody", calls)
        self.assertIn("Resultado dos testes: **indisponível**", calls["summary"])
        self.assertTrue(any("interpretar os resultados" in item for item in calls["warnings"]))
