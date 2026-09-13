from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from .config import GraphSettings
from .embeddings import EmbeddingProvider
from .graphrag_index import SemanticIndex, inspect_index_freshness
from .store import GraphStore


RESULT_SCHEMA_VERSION = "1.0"
ARCHITECTURE_PREFIXES = ("docs/adr/", "docs/architecture/", "specs/")


@dataclass(frozen=True, slots=True)
class SemanticHit:
    chunk_id: str
    source_path: str
    ordinal: int
    start_line: int
    end_line: int
    score: float
    text: str

    def to_dict(self) -> dict[str, object]:
        return {
            "chunkId": self.chunk_id,
            "sourcePath": self.source_path,
            "ordinal": self.ordinal,
            "startLine": self.start_line,
            "endLine": self.end_line,
            "score": self.score,
            "text": self.text,
        }


@dataclass(frozen=True, slots=True)
class GraphAnchor:
    seed_chunk_id: str
    seed_source_path: str
    semantic_score: float
    label: str
    canonical_id: str
    source_path: str | None
    path: str | None
    title: str | None
    status: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "seedChunkId": self.seed_chunk_id,
            "seedSourcePath": self.seed_source_path,
            "semanticScore": self.semantic_score,
            "label": self.label,
            "canonicalId": self.canonical_id,
            "sourcePath": self.source_path,
            "path": self.path,
            "title": self.title,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class TraversalStep:
    relationship: str
    from_id: str
    to_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "relationship": self.relationship,
            "from": self.from_id,
            "to": self.to_id,
        }


@dataclass(frozen=True, slots=True)
class GraphEvidence:
    seed_chunk_ids: tuple[str, ...]
    anchor_canonical_ids: tuple[str, ...]
    canonical_id: str
    label: str
    distance: int
    source_path: str | None
    path: str | None
    title: str | None
    status: str | None
    via: tuple[TraversalStep, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "seedChunkIds": list(self.seed_chunk_ids),
            "anchorCanonicalIds": list(self.anchor_canonical_ids),
            "canonicalId": self.canonical_id,
            "label": self.label,
            "distance": self.distance,
            "sourcePath": self.source_path,
            "path": self.path,
            "title": self.title,
            "status": self.status,
            "via": [step.to_dict() for step in self.via],
        }


@dataclass(frozen=True, slots=True)
class GraphRagResult:
    repository: str
    source_revision: str
    index_semantic_sha256: str
    provider_id: str
    model_id: str
    query: str
    mode: str
    top_k: int
    min_score: float
    max_depth: int
    max_nodes: int
    semantic_hits: tuple[SemanticHit, ...]
    anchors: tuple[GraphAnchor, ...]
    graph_evidence: tuple[GraphEvidence, ...]
    truncated: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": RESULT_SCHEMA_VERSION,
            "repository": self.repository,
            "sourceRevision": self.source_revision,
            "indexSemanticSha256": self.index_semantic_sha256,
            "providerId": self.provider_id,
            "modelId": self.model_id,
            "query": self.query,
            "mode": self.mode,
            "topK": self.top_k,
            "minScore": self.min_score,
            "maxDepth": self.max_depth,
            "maxNodes": self.max_nodes,
            "semanticHits": [hit.to_dict() for hit in self.semantic_hits],
            "anchors": [anchor.to_dict() for anchor in self.anchors],
            "graphEvidence": [item.to_dict() for item in self.graph_evidence],
            "truncated": self.truncated,
        }


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Cannot compare vectors with different dimensions")
    return float(sum(a * b for a, b in zip(left, right)))


def search_semantic_index(
    index: SemanticIndex,
    query: str,
    provider: EmbeddingProvider,
    *,
    top_k: int,
    min_score: float,
    mode: str = "all",
) -> tuple[SemanticHit, ...]:
    if not query.strip():
        raise ValueError("GraphRAG query must not be empty")
    if top_k <= 0:
        raise ValueError("GraphRAG top_k must be positive")
    if provider.provider_id != index.manifest.provider_id:
        raise ValueError("Embedding provider does not match GraphRAG index")
    if provider.model_id != index.manifest.model_id:
        raise ValueError("Embedding model does not match GraphRAG index")
    if provider.expected_dimensions != index.manifest.dimensions:
        raise ValueError("Embedding dimensions do not match GraphRAG index")
    if mode not in {"all", "architecture"}:
        raise ValueError(f"Unsupported GraphRAG query mode: {mode}")

    vectors = provider.embed([query])
    if len(vectors) != 1:
        raise ValueError("Embedding provider did not return exactly one query vector")
    query_vector = vectors[0]
    scored: list[SemanticHit] = []
    for chunk in index.chunks:
        score = cosine_similarity(query_vector, chunk.vector)
        if score < min_score:
            continue
        scored.append(
            SemanticHit(
                chunk_id=chunk.chunk_id,
                source_path=chunk.source_path,
                ordinal=chunk.ordinal,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                score=score,
                text=chunk.text,
            )
        )

    if mode == "architecture":
        scored.sort(
            key=lambda item: (
                0 if item.source_path.startswith(ARCHITECTURE_PREFIXES) else 1,
                -item.score,
                item.source_path,
                item.ordinal,
                item.chunk_id,
            )
        )
    else:
        scored.sort(key=lambda item: (-item.score, item.source_path, item.ordinal, item.chunk_id))
    return tuple(scored[:top_k])


def resolve_graph_anchors(
    store: GraphStore,
    settings: GraphSettings,
    hits: Sequence[SemanticHit],
) -> tuple[GraphAnchor, ...]:
    paths = sorted({hit.source_path for hit in hits})
    if not paths:
        return ()
    rows = store.run(
        """
        MATCH (n {repository: $repository})
        WHERE n.sourcePath IN $paths OR n.path IN $paths
        RETURN labels(n)[0] AS label,
               n.canonicalId AS canonicalId,
               n.sourcePath AS sourcePath,
               n.path AS path,
               n.title AS title,
               n.status AS status
        ORDER BY label, canonicalId
        """,
        {"repository": settings.repository_id, "paths": paths},
    )

    anchors: list[GraphAnchor] = []
    for hit in hits:
        for row in rows:
            source_path = row.get("sourcePath")
            path = row.get("path")
            if hit.source_path not in {source_path, path}:
                continue
            canonical_id = row.get("canonicalId")
            label = row.get("label")
            if not canonical_id or not label:
                continue
            anchors.append(
                GraphAnchor(
                    seed_chunk_id=hit.chunk_id,
                    seed_source_path=hit.source_path,
                    semantic_score=hit.score,
                    label=str(label),
                    canonical_id=str(canonical_id),
                    source_path=str(source_path) if source_path is not None else None,
                    path=str(path) if path is not None else None,
                    title=str(row["title"]) if row.get("title") is not None else None,
                    status=str(row["status"]) if row.get("status") is not None else None,
                )
            )
    return tuple(
        sorted(
            anchors,
            key=lambda item: (
                -item.semantic_score,
                item.seed_source_path,
                item.canonical_id,
                item.seed_chunk_id,
            ),
        )
    )


def _steps(raw: Any) -> tuple[TraversalStep, ...]:
    if not isinstance(raw, list):
        return ()
    steps: list[TraversalStep] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        relationship = item.get("relationship")
        from_id = item.get("from")
        to_id = item.get("to")
        if relationship and from_id and to_id:
            steps.append(
                TraversalStep(
                    relationship=str(relationship),
                    from_id=str(from_id),
                    to_id=str(to_id),
                )
            )
    return tuple(steps)


def expand_graph(
    store: GraphStore,
    settings: GraphSettings,
    anchors: Sequence[GraphAnchor],
    *,
    max_depth: int,
    max_nodes: int,
) -> tuple[tuple[GraphEvidence, ...], bool]:
    depth = min(max(max_depth, 0), 5)
    limit = max(max_nodes, 1)
    aggregate: dict[str, dict[str, Any]] = {}
    truncated = False

    for anchor in anchors:
        query_limit = max(limit * 4, 20)
        rows = store.run(
            f"""
            MATCH (seed {{repository: $repository, canonicalId: $anchorId}})
            MATCH p=(seed)-[*0..{depth}]-(n {{repository: $repository}})
            WHERE all(r IN relationships(p) WHERE r.repository = $repository)
            RETURN labels(n)[0] AS label,
                   n.canonicalId AS canonicalId,
                   n.sourcePath AS sourcePath,
                   n.path AS path,
                   n.title AS title,
                   n.status AS status,
                   length(p) AS distance,
                   [r IN relationships(p) | {{
                     relationship: type(r),
                     from: startNode(r).canonicalId,
                     to: endNode(r).canonicalId
                   }}] AS via
            ORDER BY distance, canonicalId
            LIMIT $limit
            """,
            {
                "repository": settings.repository_id,
                "anchorId": anchor.canonical_id,
                "limit": query_limit,
            },
        )
        for row in rows:
            canonical_id = row.get("canonicalId")
            label = row.get("label")
            if not canonical_id or not label:
                continue
            key = str(canonical_id)
            existing = aggregate.get(key)
            distance = int(row.get("distance", 0))
            if existing is None:
                if len(aggregate) >= limit:
                    truncated = True
                    continue
                aggregate[key] = {
                    "seedChunkIds": {anchor.seed_chunk_id},
                    "anchorCanonicalIds": {anchor.canonical_id},
                    "canonicalId": key,
                    "label": str(label),
                    "distance": distance,
                    "sourcePath": row.get("sourcePath"),
                    "path": row.get("path"),
                    "title": row.get("title"),
                    "status": row.get("status"),
                    "via": _steps(row.get("via")),
                }
            else:
                existing["seedChunkIds"].add(anchor.seed_chunk_id)
                existing["anchorCanonicalIds"].add(anchor.canonical_id)
                if distance < int(existing["distance"]):
                    existing["distance"] = distance
                    existing["via"] = _steps(row.get("via"))

    evidence = tuple(
        GraphEvidence(
            seed_chunk_ids=tuple(sorted(value["seedChunkIds"])),
            anchor_canonical_ids=tuple(sorted(value["anchorCanonicalIds"])),
            canonical_id=str(value["canonicalId"]),
            label=str(value["label"]),
            distance=int(value["distance"]),
            source_path=str(value["sourcePath"]) if value.get("sourcePath") is not None else None,
            path=str(value["path"]) if value.get("path") is not None else None,
            title=str(value["title"]) if value.get("title") is not None else None,
            status=str(value["status"]) if value.get("status") is not None else None,
            via=tuple(value["via"]),
        )
        for value in sorted(
            aggregate.values(),
            key=lambda item: (int(item["distance"]), str(item["label"]), str(item["canonicalId"])),
        )
    )
    return evidence, truncated


def query_graphrag(
    store: GraphStore,
    settings: GraphSettings,
    index: SemanticIndex,
    provider: EmbeddingProvider,
    query: str,
    *,
    top_k: int = 8,
    min_score: float = 0.0,
    max_depth: int = 2,
    max_nodes: int = 80,
    mode: str = "all",
    strict: bool = True,
) -> GraphRagResult:
    freshness = inspect_index_freshness(index, settings, provider, strict=strict)
    if not freshness.valid:
        details = "; ".join(freshness.messages) or freshness.status
        raise ValueError(f"GraphRAG index is not valid for query: {details}")

    hits = search_semantic_index(
        index,
        query,
        provider,
        top_k=top_k,
        min_score=min_score,
        mode=mode,
    )
    anchors = resolve_graph_anchors(store, settings, hits)
    evidence, truncated = expand_graph(
        store,
        settings,
        anchors,
        max_depth=max_depth,
        max_nodes=max_nodes,
    )
    return GraphRagResult(
        repository=settings.repository_id,
        source_revision=index.manifest.source_revision,
        index_semantic_sha256=index.manifest.semantic_sha256,
        provider_id=index.manifest.provider_id,
        model_id=index.manifest.model_id,
        query=query,
        mode=mode,
        top_k=top_k,
        min_score=min_score,
        max_depth=max_depth,
        max_nodes=max_nodes,
        semantic_hits=hits,
        anchors=anchors,
        graph_evidence=evidence,
        truncated=truncated,
    )
