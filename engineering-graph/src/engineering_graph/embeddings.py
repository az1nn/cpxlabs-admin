from __future__ import annotations

import hashlib
import json
import math
import os
import re
from typing import Protocol, Sequence
from urllib import request

from .config import GraphSettings


_TOKEN_RE = re.compile(r"[\w./:-]+", flags=re.UNICODE)


class EmbeddingProvider(Protocol):
    provider_id: str
    model_id: str
    expected_dimensions: int

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]: ...


def normalize_vector(values: Sequence[float]) -> tuple[float, ...]:
    vector = tuple(float(value) for value in values)
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return tuple(value / magnitude for value in vector)


def validate_embeddings(
    vectors: Sequence[Sequence[float]],
    *,
    expected_count: int,
    expected_dimensions: int,
) -> tuple[tuple[float, ...], ...]:
    if len(vectors) != expected_count:
        raise ValueError(
            f"Embedding provider returned {len(vectors)} vectors for {expected_count} inputs"
        )
    normalized: list[tuple[float, ...]] = []
    for vector in vectors:
        if len(vector) != expected_dimensions:
            raise ValueError(
                f"Embedding dimension mismatch: expected {expected_dimensions}, got {len(vector)}"
            )
        normalized.append(normalize_vector(vector))
    return tuple(normalized)


class HashingEmbeddingProvider:
    """Deterministic offline retrieval surrogate for CI and local mechanics."""

    provider_id = "hashing"

    def __init__(self, model_id: str = "hashing-v1", dimensions: int = 256) -> None:
        if dimensions <= 0:
            raise ValueError("Embedding dimensions must be positive")
        self.model_id = model_id
        self.expected_dimensions = dimensions

    @staticmethod
    def _features(text: str) -> tuple[str, ...]:
        tokens = tuple(token.casefold() for token in _TOKEN_RE.findall(text))
        bigrams = tuple(f"{left}::{right}" for left, right in zip(tokens, tokens[1:]))
        return tokens + bigrams

    def _embed_one(self, text: str) -> tuple[float, ...]:
        values = [0.0] * self.expected_dimensions
        for feature in self._features(text):
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(digest[:8], "little") % self.expected_dimensions
            sign = -1.0 if digest[8] & 1 else 1.0
            values[index] += sign
        return normalize_vector(values)

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        return tuple(self._embed_one(text) for text in texts)


class HttpEmbeddingProvider:
    provider_id = "http"

    def __init__(
        self,
        *,
        endpoint: str,
        model_id: str,
        dimensions: int,
        api_key: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        if not endpoint.strip():
            raise ValueError("HTTP embedding endpoint is required")
        if not model_id.strip():
            raise ValueError("HTTP embedding model is required")
        if dimensions <= 0:
            raise ValueError("HTTP embedding dimensions must be positive")
        self.endpoint = endpoint
        self.model_id = model_id
        self.expected_dimensions = dimensions
        self.api_key = api_key
        self.timeout_seconds = max(timeout_seconds, 1)

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        if not texts:
            return ()
        payload = json.dumps({"model": self.model_id, "input": list(texts)}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = request.Request(self.endpoint, data=payload, headers=headers, method="POST")
        with request.urlopen(req, timeout=self.timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))

        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list):
            raise ValueError("HTTP embedding response must contain a data array")

        ordered = sorted(
            data,
            key=lambda item: int(item.get("index", 0)) if isinstance(item, dict) else 0,
        )
        vectors: list[Sequence[float]] = []
        for item in ordered:
            if not isinstance(item, dict) or not isinstance(item.get("embedding"), list):
                raise ValueError("HTTP embedding response item is missing embedding array")
            vectors.append(item["embedding"])
        return validate_embeddings(
            vectors,
            expected_count=len(texts),
            expected_dimensions=self.expected_dimensions,
        )


def build_embedding_provider(
    settings: GraphSettings,
    *,
    provider_name: str | None = None,
    model_id: str | None = None,
    dimensions: int | None = None,
) -> EmbeddingProvider:
    name = (provider_name or settings.graphrag.provider).strip().lower()
    model = (model_id or settings.graphrag.model).strip()
    dims = int(dimensions or settings.graphrag.dimensions)

    if name == "hashing":
        return HashingEmbeddingProvider(model_id=model, dimensions=dims)
    if name == "http":
        endpoint = os.getenv("GRAPH_RAG_EMBEDDING_URL", "").strip()
        if not endpoint:
            raise ValueError("GRAPH_RAG_EMBEDDING_URL is required for provider=http")
        return HttpEmbeddingProvider(
            endpoint=endpoint,
            model_id=model,
            dimensions=dims,
            api_key=os.getenv("GRAPH_RAG_EMBEDDING_API_KEY"),
            timeout_seconds=settings.graphrag.http_timeout_seconds,
        )
    raise ValueError(f"Unsupported GraphRAG embedding provider: {name}")
