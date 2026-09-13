from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from engineering_graph.config import ContextBudget, GraphRagSettings, GraphSettings, Neo4jSettings
from engineering_graph.graphrag_corpus import build_corpus, chunk_text, eligible_tracked_paths


class GraphRagCorpusTests(unittest.TestCase):
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
        (self.repo / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        (self.repo / "docs").mkdir()
        (self.repo / "docs/architecture.md").write_text(
            "Architecture worktree leases and deterministic context.\n",
            encoding="utf-8",
        )
        (self.repo / "src").mkdir()
        (self.repo / "src/example.py").write_text("VALUE = 'graph'\n", encoding="utf-8")
        (self.repo / "engineering-graph/.graphrag").mkdir(parents=True)
        (self.repo / "engineering-graph/.graphrag/tracked.md").write_text(
            "generated semantic state\n", encoding="utf-8"
        )
        (self.repo / "secret.md").write_text("untracked secret\n", encoding="utf-8")
        subprocess.run(
            [
                "git",
                "add",
                "AGENTS.md",
                "docs/architecture.md",
                "src/example.py",
                "engineering-graph/.graphrag/tracked.md",
            ],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=self.repo, check=True, capture_output=True)
        self.settings = GraphSettings(
            tool_root=self.repo / "engineering-graph",
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
            graphrag=GraphRagSettings(dimensions=32, chunk_max_chars=40, chunk_overlap_chars=8),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_only_eligible_tracked_files_are_selected(self) -> None:
        paths = eligible_tracked_paths(self.settings)
        self.assertIn("AGENTS.md", paths)
        self.assertIn("docs/architecture.md", paths)
        self.assertIn("src/example.py", paths)
        self.assertNotIn("secret.md", paths)
        self.assertNotIn("engineering-graph/.graphrag/tracked.md", paths)

    def test_chunking_is_deterministic_and_stable(self) -> None:
        text = "alpha beta gamma\n" * 8
        first = chunk_text(
            "example/project",
            "docs/example.md",
            text,
            max_chars=40,
            overlap_chars=8,
        )
        second = chunk_text(
            "example/project",
            "docs/example.md",
            text,
            max_chars=40,
            overlap_chars=8,
        )
        self.assertEqual(first, second)
        self.assertGreater(len(first), 1)
        self.assertTrue(all(chunk.chunk_id for chunk in first))
        self.assertTrue(all(chunk.start_line <= chunk.end_line for chunk in first))

    def test_corpus_is_path_ordered(self) -> None:
        corpus = build_corpus(self.settings)
        keys = [(chunk.source_path, chunk.ordinal) for chunk in corpus]
        self.assertEqual(keys, sorted(keys))


if __name__ == "__main__":
    unittest.main()
