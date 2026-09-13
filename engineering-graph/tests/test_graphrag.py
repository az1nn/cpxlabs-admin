from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from engineering_graph.config import ContextBudget, GraphSettings, Neo4jSettings
from engineering_graph.graphrag import (
    expand_graph,
    query_graphrag,
    resolve_graph_anchors,
    search_semantic_index,
)
from engineering_graph.graphrag_index import IndexedChunk, SemanticIndex, SemanticIndexManifest


class StaticProvider:
    provider_id = "static"
    model_id = "static-v1"
    expected_dimensions = 2

    def embed(self, texts):
        return tuple((1.0, 0.0) for _ in texts)


class FakeStore:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def run(self, query: str, parameters=None):
        self.queries.append(query)
        parameters = parameters or {}
        if "n.sourcePath IN $paths" in query:
            rows = []
            paths = set(parameters.get("paths", []))
            if "specs/012-graphrag/spec.md" in paths:
                rows.append(
                    {
                        "label": "Spec",
                        "canonicalId": "SPEC-012-GRAPHRAG",
                        "sourcePath": "specs/012-graphrag/spec.md",
                        "path": None,
                        "title": "GraphRAG V4",
                        "status": "active",
                    }
                )
            if "src/example.py" in paths:
                rows.append(
                    {
                        "label": "CodeArtifact",
                        "canonicalId": "src/example.py",
                        "sourcePath": None,
                        "path": "src/example.py",
                        "title": None,
                        "status": None,
                    }
                )
            return rows
        if "MATCH p=(seed)" in query:
            anchor = parameters["anchorId"]
            if anchor == "SPEC-012-GRAPHRAG":
                return [
                    {
                        "label": "Spec",
                        "canonicalId": "SPEC-012-GRAPHRAG",
                        "sourcePath": "specs/012-graphrag/spec.md",
                        "path": None,
                        "title": "GraphRAG V4",
                        "status": "active",
                        "distance": 0,
                        "via": [],
                    },
                    {
                        "label": "ADR",
                        "canonicalId": "ADR-0020",
                        "sourcePath": "docs/adr/0020-graphrag-derived-semantic-index-boundary.md",
                        "path": None,
                        "title": "GraphRAG boundary",
                        "status": "accepted",
                        "distance": 1,
                        "via": [
                            {
                                "relationship": "CONSTRAINED_BY",
                                "from": "SPEC-012-GRAPHRAG",
                                "to": "ADR-0020",
                            }
                        ],
                    },
                ]
            return []
        raise AssertionError(f"Unexpected query: {query}")


def make_index() -> SemanticIndex:
    manifest = SemanticIndexManifest(
        schema_version="1.0",
        repository="example/project",
        source_revision="fixture-rev",
        provider_id="static",
        model_id="static-v1",
        dimensions=2,
        chunk_max_chars=1800,
        chunk_overlap_chars=200,
        include_extensions=(".md", ".py"),
        excluded_prefixes=(),
        chunk_count=2,
        semantic_sha256="fixture-hash",
        generated_at="2026-09-11T00:00:00+00:00",
    )
    return SemanticIndex(
        manifest=manifest,
        chunks=(
            IndexedChunk(
                chunk_id="code",
                source_path="src/example.py",
                ordinal=0,
                start_line=1,
                end_line=1,
                text="worktree lease runtime implementation",
                content_sha256="code-hash",
                vector=(1.0, 0.0),
            ),
            IndexedChunk(
                chunk_id="spec",
                source_path="specs/012-graphrag/spec.md",
                ordinal=0,
                start_line=1,
                end_line=10,
                text="GraphRAG architecture retrieval specification",
                content_sha256="spec-hash",
                vector=(0.8, 0.6),
            ),
        ),
    )


class GraphRagTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        repo = Path(self.temporary.name)
        self.settings = GraphSettings(
            tool_root=repo / "engineering-graph",
            repo_root=repo,
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
        self.index = make_index()
        self.provider = StaticProvider()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_semantic_ranking_and_architecture_mode(self) -> None:
        regular = search_semantic_index(
            self.index,
            "worktree",
            self.provider,
            top_k=2,
            min_score=0.0,
        )
        self.assertEqual([item.chunk_id for item in regular], ["code", "spec"])
        architecture = search_semantic_index(
            self.index,
            "worktree",
            self.provider,
            top_k=1,
            min_score=0.0,
            mode="architecture",
        )
        self.assertEqual(architecture[0].chunk_id, "spec")
        self.assertAlmostEqual(architecture[0].score, 0.8)

    def test_anchor_resolution_preserves_seed_provenance(self) -> None:
        store = FakeStore()
        hits = search_semantic_index(
            self.index,
            "worktree",
            self.provider,
            top_k=2,
            min_score=0.0,
        )
        anchors = resolve_graph_anchors(store, self.settings, hits)
        self.assertEqual({item.canonical_id for item in anchors}, {"SPEC-012-GRAPHRAG", "src/example.py"})
        spec = next(item for item in anchors if item.canonical_id == "SPEC-012-GRAPHRAG")
        self.assertEqual(spec.seed_chunk_id, "spec")

    def test_bounded_expansion_uses_existing_relationships(self) -> None:
        store = FakeStore()
        hits = search_semantic_index(
            self.index,
            "architecture",
            self.provider,
            top_k=1,
            min_score=0.0,
            mode="architecture",
        )
        anchors = resolve_graph_anchors(store, self.settings, hits)
        evidence, truncated = expand_graph(
            store,
            self.settings,
            anchors,
            max_depth=2,
            max_nodes=10,
        )
        self.assertFalse(truncated)
        self.assertEqual([item.canonical_id for item in evidence], ["SPEC-012-GRAPHRAG", "ADR-0020"])
        adr = next(item for item in evidence if item.canonical_id == "ADR-0020")
        self.assertEqual(adr.via[0].relationship, "CONSTRAINED_BY")
        self.assertTrue(all("CREATE" not in query.upper() and "MERGE" not in query.upper() for query in store.queries))

    def test_full_query_can_run_non_strict_for_unknown_local_revision(self) -> None:
        store = FakeStore()
        # Align corpus config with the synthetic index for compatibility.
        settings = GraphSettings(
            tool_root=self.settings.tool_root,
            repo_root=self.settings.repo_root,
            repository_id=self.settings.repository_id,
            neo4j=self.settings.neo4j,
            context=self.settings.context,
            validation_rules={},
            historical_spec_prefixes=(),
            specs_glob=self.settings.specs_glob,
            tasks_name=self.settings.tasks_name,
            plans_name=self.settings.plans_name,
            adr_glob=self.settings.adr_glob,
            prune_stale=True,
            graphrag=self.settings.graphrag.__class__(
                provider="static",
                model="static-v1",
                dimensions=2,
                chunk_max_chars=1800,
                chunk_overlap_chars=200,
                include_extensions=(".md", ".py"),
                excluded_prefixes=(),
            ),
        )
        result = query_graphrag(
            store,
            settings,
            self.index,
            self.provider,
            "architecture",
            top_k=1,
            mode="architecture",
            strict=False,
        )
        self.assertEqual(result.anchors[0].canonical_id, "SPEC-012-GRAPHRAG")
        self.assertEqual(result.graph_evidence[1].canonical_id, "ADR-0020")


if __name__ == "__main__":
    unittest.main()
