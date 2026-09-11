from __future__ import annotations

from pathlib import Path
import unittest

from engineering_graph.config import ContextBudget, GraphSettings, Neo4jSettings
from engineering_graph.context import build_context, render_context_markdown


class FakeStore:
    def query_file(self, filename: str, parameters: dict[str, object]):
        self.filename = filename
        self.parameters = parameters
        return [
            {
                "task": {"canonicalId": "SPEC-009-EXAMPLE:T001", "title": "Implement"},
                "spec": {"canonicalId": "SPEC-009-EXAMPLE", "title": "Example"},
                "requirements": [
                    {"canonicalId": "SPEC-009-EXAMPLE:FR-001", "text": "Trace"},
                    {"canonicalId": "SPEC-009-EXAMPLE:SC-001", "text": "Measure"},
                ],
                "adrs": [{"canonicalId": "ADR-0017", "title": "Graph"}],
                "dependencies": [{"canonicalId": "SPEC-009-EXAMPLE:T000"}],
                "code": [{"canonicalId": "src/a.py", "path": "src/a.py"}],
                "tests": [{"canonicalId": "tests/a.test.py", "path": "tests/a.test.py"}],
                "pullRequests": [{"canonicalId": "example/project#1", "number": 1}],
            }
        ]


class ContextTests(unittest.TestCase):
    def settings(self) -> GraphSettings:
        root = Path.cwd()
        return GraphSettings(
            tool_root=root,
            repo_root=root,
            repository_id="example/project",
            neo4j=Neo4jSettings("bolt://unused", "neo4j", "unused", "neo4j"),
            context=ContextBudget(3, 80),
            validation_rules={},
            historical_spec_prefixes=(),
            specs_glob="",
            tasks_name="tasks.md",
            plans_name="plan.md",
            adr_glob="",
            prune_stale=True,
        )

    def test_depth_one_excludes_spec_second_hop_requirements_and_adrs(self) -> None:
        package = build_context(FakeStore(), self.settings(), "SPEC-009-EXAMPLE:T001", ContextBudget(1, 20))
        self.assertIsNotNone(package.spec)
        self.assertEqual(package.requirements, ())
        self.assertEqual(package.adrs, ())
        self.assertEqual(len(package.dependencies), 1)
        self.assertEqual(len(package.code), 1)
        self.assertTrue(package.truncated)

    def test_node_budget_is_hard_bound(self) -> None:
        package = build_context(FakeStore(), self.settings(), "SPEC-009-EXAMPLE:T001", ContextBudget(3, 4))
        payload = package.to_dict()
        related = sum(
            len(payload[name])
            for name in ("requirements", "adrs", "dependencies", "code", "tests", "pullRequests")
        )
        self.assertLessEqual(1 + (1 if payload["spec"] else 0) + related, 4)
        self.assertTrue(package.truncated)

    def test_markdown_reminds_agent_that_graph_is_derived(self) -> None:
        package = build_context(FakeStore(), self.settings(), "SPEC-009-EXAMPLE:T001")
        rendered = render_context_markdown(package)
        self.assertIn("Source-of-truth rule", rendered)
        self.assertIn("do not treat Neo4j as authoritative", rendered)


if __name__ == "__main__":
    unittest.main()
