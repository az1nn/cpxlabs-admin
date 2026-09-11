from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil
import tempfile
import unittest

import yaml

from engineering_graph.config import load_settings
from engineering_graph.model import CORE_LABELS, CORE_RELATIONSHIPS
from engineering_graph.schema import (
    SchemaDefinitionError,
    constraint_statements,
    validate_schema_definitions,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class SchemaTests(unittest.TestCase):
    def test_repository_schema_matches_core_model_and_constraints(self) -> None:
        settings = load_settings(repo_root=REPO_ROOT)
        validate_schema_definitions(settings)
        statements = constraint_statements(settings)

        self.assertEqual(len(CORE_LABELS), 7)
        self.assertEqual(len(CORE_RELATIONSHIPS), 8)
        self.assertGreaterEqual(len(statements), len(CORE_LABELS))
        for label in CORE_LABELS:
            matching = [statement for statement in statements if f"FOR (n:{label})" in statement]
            self.assertTrue(matching, f"missing schema statement for {label}")
            self.assertTrue(
                any("n.repository, n.canonicalId" in statement for statement in matching),
                f"missing composite identity constraint for {label}",
            )

    def test_schema_validation_rejects_missing_core_label(self) -> None:
        settings = load_settings(repo_root=REPO_ROOT)
        with tempfile.TemporaryDirectory() as directory:
            tool_root = Path(directory)
            shutil.copytree(settings.tool_root / "schema", tool_root / "schema")
            nodes_path = tool_root / "schema" / "nodes.yaml"
            nodes = yaml.safe_load(nodes_path.read_text(encoding="utf-8"))
            nodes["nodes"].pop("PullRequest")
            nodes_path.write_text(yaml.safe_dump(nodes, sort_keys=False), encoding="utf-8")

            with self.assertRaisesRegex(SchemaDefinitionError, "missing=.*PullRequest"):
                validate_schema_definitions(replace(settings, tool_root=tool_root))

    def test_schema_validation_rejects_unknown_relationship_endpoint(self) -> None:
        settings = load_settings(repo_root=REPO_ROOT)
        with tempfile.TemporaryDirectory() as directory:
            tool_root = Path(directory)
            shutil.copytree(settings.tool_root / "schema", tool_root / "schema")
            path = tool_root / "schema" / "relationships.yaml"
            relationships = yaml.safe_load(path.read_text(encoding="utf-8"))
            relationships["relationships"]["IMPLEMENTS"]["to"].append("UnknownNode")
            path.write_text(yaml.safe_dump(relationships, sort_keys=False), encoding="utf-8")

            with self.assertRaisesRegex(SchemaDefinitionError, "unknown labels"):
                validate_schema_definitions(replace(settings, tool_root=tool_root))


if __name__ == "__main__":
    unittest.main()
