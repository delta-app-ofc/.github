"""Impede chaves YAML duplicadas que o parser comum aceita e o Actions rejeita."""
from pathlib import Path
import unittest
import yaml


class UniqueKeysLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise ValueError(f"Chave YAML duplicada: {key}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueKeysLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


class WorkflowYamlTests(unittest.TestCase):
    @staticmethod
    def load_workflow(name):
        path = Path(__file__).resolve().parents[1] / ".github/workflows" / name
        return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeysLoader)

    def test_all_workflows_have_unique_mapping_keys(self):
        folder = Path(__file__).resolve().parents[1] / ".github/workflows"
        for workflow in folder.glob("*.yml"):
            with self.subTest(workflow=workflow.name):
                yaml.load(workflow.read_text(encoding="utf-8"), Loader=UniqueKeysLoader)

    def test_required_technical_check_names_are_stable(self):
        technical = self.load_workflow("test.yml")
        sonar = self.load_workflow("sonar.yml")
        governance = self.load_workflow("local_checks.yml")

        self.assertEqual(technical["jobs"]["python"]["name"], "ci-tecnico")
        self.assertEqual(technical["jobs"]["report-ci"]["needs"], ["python"])
        self.assertEqual(sonar["jobs"]["tests"]["name"], "Testes Sonar")
        self.assertEqual(sonar["jobs"]["scan"]["needs"], "tests")
        self.assertEqual(
            governance["jobs"]["pr-checks"]["name"],
            "validate-pr-checks / Governança da Pull Request",
        )

    def test_duplicate_reusable_workflow_input_is_rejected(self):
        text = "inputs:\n  artifact_path: reports\n  artifact_path: target\n"
        with self.assertRaises(ValueError):
            yaml.load(text, Loader=UniqueKeysLoader)
