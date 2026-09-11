from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from engineering_graph.config import ContextBudget, GraphSettings, Neo4jSettings
from engineering_graph.context import ContextPackage, build_context, render_context_markdown


class FakeStore:
    source_revision = "abc123"

    def query_file(self, filename: str, parameters: dict[str, object]):
        self.filename = filename
        self.parameters = parameters
        return [
            {
                "sourceRevision": self.source_revision,
                "task": {
                    "canonicalId": "SPEC-010-EXAMPLE:T001",
                    "title": "Implement",
                    "sourcePath": "specs/010-example/tasks.md",
                    "sourceRevision": self.source_revision,
                },
                "spec": {
                    "canonicalId": "SPEC-010-EXAMPLE",
                    "title": "Example",
                    "sourcePath": "specs/010-example/spec.md",
                    "sourceRevision": self.source_revision,
                },
                "requirements": [
                    {"canonicalId": "SPEC-010-EXAMPLE:FR-001", "text": "Trace"},
                    {"canonicalId": "SPEC-010-EXAMPLE:SC-001", "text": "Measure"},
                ],
                "adrs": [{"canonicalId": "ADR-0018", "title": "Context"}],
                "dependencies": [{"canonicalId": "SPEC-010-EXAMPLE:T000", "status": "done"}],
                "code": [{"canonicalId": "src/a.py", "path": "src/a.py"}],
                "tests": [{"canonicalId": "tests/a.test.py", "path": "tests/a.test.py"}],
                "pullRequests": [{"canonicalId": "example/project#1", "number": 1}],
            }
        ]


class StaleFakeStore(FakeStore):
    source_revision = "old-revision"


class LargeFakeStore(FakeStore):
    def query_file(self, filename: str, parameters: dict[str, object]):
        row = super().query_file(filename, parameters)[0]
        row["code"] = [
            {
                "canonicalId": f"src/generated_{index}.py",
                "path": f"src/generated_{index}.py",
                "title": "x" * 240,
            }
            for index in range(40)
        ]
        return [row]


class ContextTests(unittest.TestCase):
    def settings(self) -> GraphSettings:
        root = Path.cwd()
        return GraphSettings(
            tool_root=root,
            repo_root=root,
            repository_id="example/project",
            neo4j=Neo4jSettings("bolt://unused", "neo4j", "unused", "neo4j"),
            context=ContextBudget(3, 80, 65536),
            validation_rules={},
            historical_spec_prefixes=(),
            specs_glob="",
            tasks_name="tasks.md",
            plans_name="plan.md",
            adr_glob="",
            prune_stale=True,
        )

    @patch("engineering_graph.context.current_git_revision", return_value="abc123")
    def test_depth_one_excludes_spec_second_hop_requirements_and_adrs(self, _revision) -> None:
        package = build_context(FakeStore(), self.settings(), "SPEC-010-EXAMPLE:T001", ContextBudget(1, 20))
        self.assertIsNotNone(package.spec)
        self.assertEqual(package.requirements, ())
        self.assertEqual(package.adrs, ())
        self.assertEqual(len(package.dependencies), 1)
        self.assertEqual(len(package.code_artifacts), 1)
        self.assertTrue(package.truncated)

    @patch("engineering_graph.context.current_git_revision", return_value="abc123")
    def test_node_budget_is_hard_bound(self, _revision) -> None:
        package = build_context(FakeStore(), self.settings(), "SPEC-010-EXAMPLE:T001", ContextBudget(3, 4))
        payload = package.to_dict()
        related = sum(
            len(payload[name])
            for name in ("requirements", "adrs", "dependencies", "codeArtifacts", "tests", "pullRequests")
        )
        self.assertLessEqual(1 + (1 if payload["spec"] else 0) + related, 4)
        self.assertTrue(package.truncated)
        self.assertGreater(package.summary.truncated_nodes, 0)

    @patch("engineering_graph.context.current_git_revision", return_value="abc123")
    def test_node_budget_rejects_less_than_mandatory_task_and_spec(self, _revision) -> None:
        with self.assertRaisesRegex(ValueError, "cannot fit mandatory task/spec"):
            build_context(FakeStore(), self.settings(), "SPEC-010-EXAMPLE:T001", ContextBudget(3, 1))

    @patch("engineering_graph.context.current_git_revision", return_value="abc123")
    def test_semantic_package_is_reproducible_excluding_operational_timestamp(self, _revision) -> None:
        first = build_context(FakeStore(), self.settings(), "SPEC-010-EXAMPLE:T001")
        second = build_context(FakeStore(), self.settings(), "SPEC-010-EXAMPLE:T001")
        self.assertEqual(first.semantic_json(), second.semantic_json())
        self.assertEqual(first.source_revision, "abc123")
        self.assertEqual(first.repository, "example/project")
        self.assertEqual(first.freshness, "current")

    @patch("engineering_graph.context.current_git_revision", return_value="new-revision")
    def test_stale_graph_projection_is_marked_stale_at_generation(self, _revision) -> None:
        package = build_context(StaleFakeStore(), self.settings(), "SPEC-010-EXAMPLE:T001")
        self.assertEqual(package.source_revision, "old-revision")
        self.assertEqual(package.freshness, "stale")

    @patch("engineering_graph.context.current_git_revision", return_value="abc123")
    def test_byte_budget_truncates_deterministically(self, _revision) -> None:
        package = build_context(
            LargeFakeStore(),
            self.settings(),
            "SPEC-010-EXAMPLE:T001",
            ContextBudget(3, 100, 2600),
        )
        self.assertLessEqual(package.summary.rendered_bytes, 2600)
        self.assertTrue(package.truncated)
        self.assertGreater(package.summary.truncated_nodes, 0)

    @patch("engineering_graph.context.current_git_revision", return_value="abc123")
    def test_round_trip_preserves_portable_contract(self, _revision) -> None:
        package = build_context(FakeStore(), self.settings(), "SPEC-010-EXAMPLE:T001")
        restored = ContextPackage.from_dict(package.to_dict())
        self.assertEqual(restored.semantic_json(), package.semantic_json())
        self.assertEqual(restored.package_version, "1")
        self.assertTrue(restored.provenance)

    @patch("engineering_graph.context.current_git_revision", return_value="abc123")
    def test_markdown_reminds_agent_that_graph_is_derived(self, _revision) -> None:
        package = build_context(FakeStore(), self.settings(), "SPEC-010-EXAMPLE:T001")
        rendered = render_context_markdown(package)
        self.assertIn("Source-of-truth rule", rendered)
        self.assertIn("do not treat Neo4j or generated context files as authoritative", rendered)
        self.assertIn("Source revision", rendered)
        self.assertIn("Freshness at generation", rendered)


if __name__ == "__main__":
    unittest.main()
