from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from engineering_graph.agent_adapters import render_agent_handoff, validation_commands
from engineering_graph.config import ContextBudget, GraphSettings, Neo4jSettings
from engineering_graph.context import build_context


class FakeStore:
    source_revision = "abc123"

    def query_file(self, filename: str, parameters: dict[str, object]):
        return [
            {
                "sourceRevision": self.source_revision,
                "task": {
                    "canonicalId": "SPEC-010-EXAMPLE:T001",
                    "title": "Implement package",
                    "sourcePath": "specs/010-example/tasks.md",
                    "sourceRevision": self.source_revision,
                },
                "spec": {
                    "canonicalId": "SPEC-010-EXAMPLE",
                    "sourcePath": "specs/010-example/spec.md",
                    "sourceRevision": self.source_revision,
                },
                "requirements": [],
                "adrs": [
                    {
                        "canonicalId": "ADR-0018",
                        "sourcePath": "docs/adr/0018-agent-context-package-boundary.md",
                    }
                ],
                "dependencies": [],
                "code": [
                    {
                        "canonicalId": "engineering-graph/src/engineering_graph/context.py",
                        "path": "engineering-graph/src/engineering_graph/context.py",
                    }
                ],
                "tests": [
                    {
                        "canonicalId": "engineering-graph/tests/test_context.py",
                        "path": "engineering-graph/tests/test_context.py",
                    }
                ],
                "pullRequests": [],
            }
        ]


def settings() -> GraphSettings:
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


class AgentAdapterTests(unittest.TestCase):
    @patch("engineering_graph.context.current_git_revision", return_value="abc123")
    def package(self, _revision):
        return build_context(FakeStore(), settings(), "SPEC-010-EXAMPLE:T001")

    def test_codex_handoff_uses_agents_map_and_canonical_paths(self) -> None:
        rendered = render_agent_handoff(self.package(), "codex", "context.json")
        self.assertIn("AGENTS.md", rendered)
        self.assertIn("engineering-graph/src/engineering_graph/context.py", rendered)
        self.assertIn("Git/Markdown/code/tests remain authoritative", rendered)

    def test_claude_handoff_uses_same_portable_package_evidence(self) -> None:
        package = self.package()
        codex = render_agent_handoff(package, "codex")
        claude = render_agent_handoff(package, "claude")
        for value in (
            "SPEC-010-EXAMPLE:T001",
            "abc123",
            "specs/010-example/spec.md",
            "docs/adr/0018-agent-context-package-boundary.md",
            "engineering-graph/tests/test_context.py",
        ):
            self.assertIn(value, codex)
            self.assertIn(value, claude)

    def test_graph_changes_receive_graph_validation_commands(self) -> None:
        commands = validation_commands(self.package())
        self.assertIn("python -m unittest discover -s engineering-graph/tests -v", commands)
        self.assertIn("graph-engineering validate", commands)

    def test_adapter_is_deterministic(self) -> None:
        package = self.package()
        self.assertEqual(
            render_agent_handoff(package, "codex"),
            render_agent_handoff(package, "codex"),
        )

    def test_unknown_adapter_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported agent adapter"):
            render_agent_handoff(self.package(), "other")


if __name__ == "__main__":
    unittest.main()
