from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from engineering_graph.config import ContextBudget, GraphRagSettings, GraphSettings, Neo4jSettings
from engineering_graph.embeddings import HashingEmbeddingProvider
from engineering_graph.graphrag_index import (
    build_semantic_index,
    inspect_index_freshness,
    load_semantic_index,
    write_semantic_index,
)


class GraphRagIndexTests(unittest.TestCase):
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
        (self.repo / "docs/example.md").write_text(
            "Execution worktree leases preserve deterministic graph authority.\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
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
            graphrag=GraphRagSettings(dimensions=32, chunk_max_chars=200, chunk_overlap_chars=20),
        )
        self.provider = HashingEmbeddingProvider(dimensions=32)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_index_semantic_payload_is_reproducible(self) -> None:
        first = build_semantic_index(self.settings, self.provider)
        second = build_semantic_index(self.settings, self.provider)
        self.assertEqual(first.manifest.semantic_sha256, second.manifest.semantic_sha256)
        self.assertEqual(first.semantic_json(), second.semantic_json())

    def test_index_roundtrip_and_freshness(self) -> None:
        index = build_semantic_index(self.settings, self.provider)
        path = self.repo / "engineering-graph/.graphrag/index.json"
        write_semantic_index(index, path)
        loaded = load_semantic_index(path)
        self.assertEqual(index.semantic_json(), loaded.semantic_json())
        report = inspect_index_freshness(loaded, self.settings, self.provider, strict=True)
        self.assertTrue(report.valid)
        self.assertEqual(report.status, "current")

    def test_strict_freshness_rejects_new_git_revision(self) -> None:
        index = build_semantic_index(self.settings, self.provider)
        (self.repo / "docs/example.md").write_text("changed\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "change"], cwd=self.repo, check=True, capture_output=True)
        report = inspect_index_freshness(index, self.settings, self.provider, strict=True)
        self.assertFalse(report.valid)
        self.assertEqual(report.status, "stale")

    def test_provider_mismatch_is_incompatible(self) -> None:
        index = build_semantic_index(self.settings, self.provider)
        other = HashingEmbeddingProvider(model_id="hashing-v2", dimensions=32)
        report = inspect_index_freshness(index, self.settings, other, strict=False)
        self.assertFalse(report.valid)
        self.assertEqual(report.status, "incompatible")


if __name__ == "__main__":
    unittest.main()
