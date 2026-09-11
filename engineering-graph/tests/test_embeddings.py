from __future__ import annotations

import json
import math
import unittest
from unittest.mock import patch

from engineering_graph.embeddings import (
    HashingEmbeddingProvider,
    HttpEmbeddingProvider,
    normalize_vector,
)


class _Response:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class EmbeddingProviderTests(unittest.TestCase):
    def test_hashing_provider_is_deterministic(self) -> None:
        provider = HashingEmbeddingProvider(dimensions=32)
        first = provider.embed(["worktree lease architecture"])
        second = provider.embed(["worktree lease architecture"])
        self.assertEqual(first, second)
        self.assertEqual(len(first[0]), 32)
        magnitude = math.sqrt(sum(value * value for value in first[0]))
        self.assertAlmostEqual(magnitude, 1.0)

    def test_normalize_zero_vector_is_stable(self) -> None:
        self.assertEqual(normalize_vector([0.0, 0.0]), (0.0, 0.0))

    def test_http_provider_orders_and_validates_response(self) -> None:
        provider = HttpEmbeddingProvider(
            endpoint="https://embedding.example/v1/embeddings",
            model_id="example-model",
            dimensions=3,
            api_key="secret",
        )
        payload = {
            "data": [
                {"index": 1, "embedding": [0.0, 2.0, 0.0]},
                {"index": 0, "embedding": [1.0, 0.0, 0.0]},
            ]
        }
        with patch("engineering_graph.embeddings.request.urlopen", return_value=_Response(payload)) as mocked:
            vectors = provider.embed(["first", "second"])
        self.assertEqual(vectors, ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
        request_object = mocked.call_args.args[0]
        self.assertEqual(request_object.headers.get("Authorization"), "Bearer secret")

    def test_http_provider_rejects_dimension_mismatch(self) -> None:
        provider = HttpEmbeddingProvider(
            endpoint="https://embedding.example/v1/embeddings",
            model_id="example-model",
            dimensions=3,
        )
        payload = {"data": [{"index": 0, "embedding": [1.0, 0.0]}]}
        with patch("engineering_graph.embeddings.request.urlopen", return_value=_Response(payload)):
            with self.assertRaisesRegex(ValueError, "dimension mismatch"):
                provider.embed(["first"])


if __name__ == "__main__":
    unittest.main()
