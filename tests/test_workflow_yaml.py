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
    def test_all_workflows_have_unique_mapping_keys(self):
        folder = Path(__file__).resolve().parents[1] / ".github/workflows"
        for workflow in folder.glob("*.yml"):
            with self.subTest(workflow=workflow.name):
                yaml.load(workflow.read_text(encoding="utf-8"), Loader=UniqueKeysLoader)

    def test_duplicate_reusable_workflow_input_is_rejected(self):
        text = "inputs:\n  artifact_path: reports\n  artifact_path: target\n"
        with self.assertRaises(ValueError):
            yaml.load(text, Loader=UniqueKeysLoader)
