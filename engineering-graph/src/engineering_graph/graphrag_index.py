from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Sequence

from .config import GraphSettings, current_git_revision
from .embeddings import EmbeddingProvider
from .graphrag_corpus import CorpusChunk, build_corpus


INDEX_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class IndexedChunk:
    chunk_id: str
    source_path: str
    ordinal: int
    start_line: int
    end_line: int
    text: str
    content_sha256: str
    vector: tuple[float, ...]

    @classmethod
    def from_corpus(cls, chunk: CorpusChunk, vector: Sequence[float]) -> "IndexedChunk":
        return cls(
            chunk_id=chunk.chunk_id,
            source_path=chunk.source_path,
            ordinal=chunk.ordinal,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            text=chunk.text,
            content_sha256=chunk.content_sha256,
            vector=tuple(float(value) for value in vector),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "chunkId": self.chunk_id,
            "sourcePath": self.source_path,
            "ordinal": self.ordinal,
            "startLine": self.start_line,
            "endLine": self.end_line,
            "text": self.text,
            "contentSha256": self.content_sha256,
            "vector": list(self.vector),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "IndexedChunk":
        vector = payload.get("vector")
        if not isinstance(vector, list):
            raise ValueError("GraphRAG chunk vector must be an array")
        return cls(
            chunk_id=str(payload["chunkId"]),
            source_path=str(payload["sourcePath"]),
            ordinal=int(payload["ordinal"]),
            start_line=int(payload["startLine"]),
            end_line=int(payload["endLine"]),
            text=str(payload["text"]),
            content_sha256=str(payload["contentSha256"]),
            vector=tuple(float(value) for value in vector),
        )


@dataclass(frozen=True, slots=True)
class SemanticIndexManifest:
    schema_version: str
    repository: str
    source_revision: str
    provider_id: str
    model_id: str
    dimensions: int
    chunk_max_chars: int
    chunk_overlap_chars: int
    include_extensions: tuple[str, ...]
    excluded_prefixes: tuple[str, ...]
    chunk_count: int
    semantic_sha256: str
    generated_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": self.schema_version,
            "repository": self.repository,
            "sourceRevision": self.source_revision,
            "providerId": self.provider_id,
            "modelId": self.model_id,
            "dimensions": self.dimensions,
            "chunkMaxChars": self.chunk_max_chars,
            "chunkOverlapChars": self.chunk_overlap_chars,
            "includeExtensions": list(self.include_extensions),
            "excludedPrefixes": list(self.excluded_prefixes),
            "chunkCount": self.chunk_count,
            "semanticSha256": self.semantic_sha256,
            "generatedAt": self.generated_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SemanticIndexManifest":
        return cls(
            schema_version=str(payload["schemaVersion"]),
            repository=str(payload["repository"]),
            source_revision=str(payload["sourceRevision"]),
            provider_id=str(payload["providerId"]),
            model_id=str(payload["modelId"]),
            dimensions=int(payload["dimensions"]),
            chunk_max_chars=int(payload["chunkMaxChars"]),
            chunk_overlap_chars=int(payload["chunkOverlapChars"]),
            include_extensions=tuple(str(value) for value in payload.get("includeExtensions", [])),
            excluded_prefixes=tuple(str(value) for value in payload.get("excludedPrefixes", [])),
            chunk_count=int(payload["chunkCount"]),
            semantic_sha256=str(payload["semanticSha256"]),
            generated_at=str(payload["generatedAt"]),
        )


@dataclass(frozen=True, slots=True)
class SemanticIndex:
    manifest: SemanticIndexManifest
    chunks: tuple[IndexedChunk, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest": self.manifest.to_dict(),
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }

    def semantic_payload(self) -> dict[str, object]:
        manifest = self.manifest.to_dict()
        manifest.pop("generatedAt", None)
        return {
            "manifest": manifest,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }

    def semantic_json(self) -> str:
        return json.dumps(self.semantic_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class GraphRagFreshnessReport:
    valid: bool
    status: str
    index_revision: str
    current_revision: str | None
    repository_matches: bool
    provider_matches: bool
    model_matches: bool
    dimensions_match: bool
    config_matches: bool
    messages: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "status": self.status,
            "indexRevision": self.index_revision,
            "currentRevision": self.current_revision,
            "repositoryMatches": self.repository_matches,
            "providerMatches": self.provider_matches,
            "modelMatches": self.model_matches,
            "dimensionsMatch": self.dimensions_match,
            "configMatches": self.config_matches,
            "messages": list(self.messages),
        }


def default_index_path(settings: GraphSettings) -> Path:
    return settings.tool_root / ".graphrag" / "index.json"


def _hash_payload(
    manifest: SemanticIndexManifest,
    chunks: Sequence[IndexedChunk],
) -> str:
    semantic_manifest = manifest.to_dict()
    semantic_manifest.pop("generatedAt", None)
    semantic_manifest.pop("semanticSha256", None)
    payload = {
        "manifest": semantic_manifest,
        "chunks": [chunk.to_dict() for chunk in chunks],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _embed_chunks(
    chunks: Sequence[CorpusChunk],
    provider: EmbeddingProvider,
    batch_size: int,
) -> tuple[IndexedChunk, ...]:
    indexed: list[IndexedChunk] = []
    size = max(batch_size, 1)
    for offset in range(0, len(chunks), size):
        batch = chunks[offset : offset + size]
        vectors = provider.embed([chunk.text for chunk in batch])
        if len(vectors) != len(batch):
            raise ValueError("Embedding provider returned an unexpected vector count")
        for chunk, vector in zip(batch, vectors):
            if len(vector) != provider.expected_dimensions:
                raise ValueError(
                    f"Embedding dimension mismatch for {chunk.chunk_id}: "
                    f"expected {provider.expected_dimensions}, got {len(vector)}"
                )
            indexed.append(IndexedChunk.from_corpus(chunk, vector))
    return tuple(indexed)


def build_semantic_index(
    settings: GraphSettings,
    provider: EmbeddingProvider,
) -> SemanticIndex:
    revision = current_git_revision(settings.repo_root)
    if not revision:
        raise RuntimeError("Unable to determine Git revision for GraphRAG index")
    corpus = build_corpus(settings)
    chunks = _embed_chunks(corpus, provider, settings.graphrag.batch_size)
    generated_at = datetime.now(timezone.utc).isoformat()
    manifest = SemanticIndexManifest(
        schema_version=INDEX_SCHEMA_VERSION,
        repository=settings.repository_id,
        source_revision=revision,
        provider_id=provider.provider_id,
        model_id=provider.model_id,
        dimensions=provider.expected_dimensions,
        chunk_max_chars=settings.graphrag.chunk_max_chars,
        chunk_overlap_chars=settings.graphrag.chunk_overlap_chars,
        include_extensions=settings.graphrag.include_extensions,
        excluded_prefixes=settings.graphrag.excluded_prefixes,
        chunk_count=len(chunks),
        semantic_sha256="",
        generated_at=generated_at,
    )
    manifest = replace(manifest, semantic_sha256=_hash_payload(manifest, chunks))
    return SemanticIndex(manifest=manifest, chunks=chunks)


def write_semantic_index(index: SemanticIndex, destination: Path) -> None:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(index.to_dict(), indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, destination)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def load_semantic_index(path: Path) -> SemanticIndex:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("GraphRAG index root must be an object")
    manifest_raw = payload.get("manifest")
    chunks_raw = payload.get("chunks")
    if not isinstance(manifest_raw, dict) or not isinstance(chunks_raw, list):
        raise ValueError("GraphRAG index must contain manifest and chunks")
    manifest = SemanticIndexManifest.from_dict(manifest_raw)
    if manifest.schema_version != INDEX_SCHEMA_VERSION:
        raise ValueError(f"Unsupported GraphRAG index schema: {manifest.schema_version}")
    chunks = tuple(IndexedChunk.from_dict(item) for item in chunks_raw if isinstance(item, dict))
    if len(chunks) != manifest.chunk_count:
        raise ValueError("GraphRAG manifest chunk count does not match index chunks")
    if any(len(chunk.vector) != manifest.dimensions for chunk in chunks):
        raise ValueError("GraphRAG chunk vector dimensions do not match manifest")
    expected_hash = _hash_payload(manifest, chunks)
    if expected_hash != manifest.semantic_sha256:
        raise ValueError("GraphRAG semantic index hash mismatch")
    return SemanticIndex(manifest=manifest, chunks=chunks)


def inspect_index_freshness(
    index: SemanticIndex,
    settings: GraphSettings,
    provider: EmbeddingProvider,
    *,
    strict: bool,
) -> GraphRagFreshnessReport:
    current_revision = current_git_revision(settings.repo_root)
    manifest = index.manifest
    repository_matches = manifest.repository == settings.repository_id
    revision_matches = current_revision is not None and manifest.source_revision == current_revision
    provider_matches = manifest.provider_id == provider.provider_id
    model_matches = manifest.model_id == provider.model_id
    dimensions_match = manifest.dimensions == provider.expected_dimensions
    config_matches = (
        manifest.chunk_max_chars == settings.graphrag.chunk_max_chars
        and manifest.chunk_overlap_chars == settings.graphrag.chunk_overlap_chars
        and manifest.include_extensions == settings.graphrag.include_extensions
        and manifest.excluded_prefixes == settings.graphrag.excluded_prefixes
    )

    messages: list[str] = []
    if not repository_matches:
        messages.append("index repository does not match current repository")
    if current_revision is None:
        messages.append("current Git revision is unknown")
    elif not revision_matches:
        messages.append("index source revision is stale relative to current Git HEAD")
    if not provider_matches:
        messages.append("embedding provider does not match index provider")
    if not model_matches:
        messages.append("embedding model does not match index model")
    if not dimensions_match:
        messages.append("embedding dimensions do not match index dimensions")
    if not config_matches:
        messages.append("GraphRAG corpus/chunk configuration differs from index")

    compatible = (
        repository_matches
        and provider_matches
        and model_matches
        and dimensions_match
        and config_matches
    )
    if not compatible:
        status = "incompatible"
    elif not revision_matches:
        status = "stale" if current_revision is not None else "unknown"
    else:
        status = "current"
    valid = compatible and (revision_matches or not strict)
    return GraphRagFreshnessReport(
        valid=valid,
        status=status,
        index_revision=manifest.source_revision,
        current_revision=current_revision,
        repository_matches=repository_matches,
        provider_matches=provider_matches,
        model_matches=model_matches,
        dimensions_match=dimensions_match,
        config_matches=config_matches,
        messages=tuple(messages),
    )
