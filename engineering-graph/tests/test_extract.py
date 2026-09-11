from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from engineering_graph.config import ContextBudget, GraphSettings, Neo4jSettings
from engineering_graph.extract import extract_repository


class ExtractRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        subprocess.run(["git", "init"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "graph@example.test"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Graph Test"], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/example/project.git"],
            cwd=self.repo,
            check=True,
        )

        (self.repo / "specs/009-example").mkdir(parents=True)
        (self.repo / "docs/adr").mkdir(parents=True)
        (self.repo / "src").mkdir(parents=True)
        (self.repo / "tests").mkdir(parents=True)
        (self.repo / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        (self.repo / "src/example.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.repo / "tests/example.test.py").write_text("# validation\n", encoding="utf-8")
        (self.repo / "docs/adr/0017-example.md").write_text(
            "# ADR-0017: Example\n\n**Status**: Accepted\n",
            encoding="utf-8",
        )
        (self.repo / "specs/009-example/spec.md").write_text(
            """---
graph:
  enforced: true
  constrained_by:
    - ADR-0017
---
# Feature Specification: Example

**Status**: Ready

- **FR-001**: The system MUST trace implementation.
- **SC-001**: Traceability is queryable.
""",
            encoding="utf-8",
        )
        (self.repo / "specs/009-example/plan.md").write_text(
            "# Plan\n\nConstrained by ADR-0017.\n",
            encoding="utf-8",
        )
        (self.repo / "specs/009-example/tasks.md").write_text(
            """---
graph:
  task_links:
    T002:
      validated_by:
        - tests/example.test.py
---
# Tasks

## Phase 1
- [x] T001 Implement source `src/example.py`
- [ ] T002 [P] [US1] Validate source (`depends: T001`)
""",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=self.repo, check=True, capture_output=True)

        tool_root = Path(__file__).resolve().parents[1]
        self.settings = GraphSettings(
            tool_root=tool_root,
            repo_root=self.repo,
            repository_id="example/project",
            neo4j=Neo4jSettings("bolt://unused", "neo4j", "unused", "neo4j"),
            context=ContextBudget(3, 80),
            validation_rules={},
            historical_spec_prefixes=(),
            specs_glob="specs/[0-9][0-9][0-9]-*/spec.md",
            tasks_name="tasks.md",
            plans_name="plan.md",
            adr_glob="docs/adr/[0-9][0-9][0-9][0-9]-*.md",
            prune_stale=True,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_extracts_spec_requirements_tasks_adr_code_and_test_relationships(self) -> None:
        result = extract_repository(self.settings)
        model = result.model
        spec_id = "SPEC-009-EXAMPLE"

        self.assertIsNotNone(model.node("Spec", spec_id))
        self.assertIsNotNone(model.node("Requirement", f"{spec_id}:FR-001"))
        self.assertIsNotNone(model.node("Requirement", f"{spec_id}:SC-001"))
        self.assertIsNotNone(model.node("ADR", "ADR-0017"))
        self.assertIsNotNone(model.node("Task", f"{spec_id}:T001"))
        self.assertIsNotNone(model.node("Task", f"{spec_id}:T002"))
        self.assertIsNotNone(model.node("CodeArtifact", "src/example.py"))
        self.assertIsNotNone(model.node("Test", "tests/example.test.py"))

        self.assertTrue(
            any(
                edge.relationship == "CONSTRAINED_BY" and edge.target_id == "ADR-0017"
                for edge in model.edges_from("Spec", spec_id)
            )
        )
        self.assertTrue(
            any(
                edge.relationship == "DEPENDS_ON" and edge.target_id == f"{spec_id}:T001"
                for edge in model.edges_from("Task", f"{spec_id}:T002")
            )
        )
        self.assertTrue(
            any(
                edge.relationship == "VALIDATED_BY" and edge.target_id == "tests/example.test.py"
                for edge in model.edges_from("Task", f"{spec_id}:T002")
            )
        )
        self.assertEqual(model.dangling_edges(), [])

    def test_same_revision_produces_same_logical_graph(self) -> None:
        first = extract_repository(self.settings)
        second = extract_repository(self.settings)
        self.assertEqual(first.source_revision, second.source_revision)
        self.assertEqual(first.model.logical_signature(), second.model.logical_signature())


if __name__ == "__main__":
    unittest.main()
