# Research: GraphRAG V4

## Decision summary

V4 uses a **derived semantic sidecar index** plus **deterministic Neo4j expansion**.

```text
Git-tracked repository files
        │
        ▼
 deterministic chunker
        │
        ▼
 EmbeddingProvider
        │
        ▼
 derived SemanticIndex (.graphrag/)
        │
 natural-language query
        ▼
 ranked semantic chunks
        │
 path/canonical anchor resolution
        ▼
 existing Engineering Graph nodes
        │
 bounded deterministic traversal
        ▼
 GraphRAG result package
```

The semantic layer helps locate seeds. It never writes inferred edges into Neo4j.

## Why not store embeddings as canonical Neo4j properties?

The current graph model intentionally has a small stable vocabulary and deterministic extraction contract. Storing retrieval vectors directly on canonical graph nodes would couple provider/model lifecycle to the graph projection and blur the governance boundary between explicit repository evidence and semantic assistance.

V4 therefore keeps vector state outside Neo4j. The sidecar can be deleted/rebuilt independently while graph nodes/edges remain deterministic.

## Index persistence

Use a versioned JSON index in `engineering-graph/.graphrag/` for V4. Repository scale does not yet justify a hosted vector database or an additional local service. Search is performed in Python using cosine similarity.

This deliberately optimizes for:

- transparent artifacts;
- deterministic tests;
- no new service dependency;
- simple reproducibility/freshness validation;
- migration freedom if a larger vector backend becomes necessary later.

The storage interface should remain separable so a future backend can replace JSON without changing query semantics.

## Indexed corpus

Only `git ls-files` output is eligible. V4 applies configurable extension/include/exclude filters afterward. This prevents untracked secrets, generated outputs and local caches from entering the semantic corpus accidentally.

Default text types cover architecture/spec/docs and common source/test formats. Binary files are skipped.

## Chunking

Chunking is deterministic, path-ordered and paragraph/line aware. Each chunk records:

- stable chunk ID;
- source path;
- ordinal;
- start/end line;
- normalized text;
- content SHA-256.

Chunk IDs derive from repository/path/ordinal/content hash so regeneration at the same content is reproducible.

## Embedding provider boundary

`EmbeddingProvider` owns:

- provider ID;
- model ID;
- batch embedding;
- returned dimensionality.

Two V4 providers are planned:

1. **hashing** — deterministic zero-network surrogate used by CI/offline development. It is useful for mechanics/reproducibility and controlled lexical-semantic fixtures, but documentation MUST NOT describe it as equivalent to a learned embedding model.
2. **http** — configurable learned-embedding endpoint using Python stdlib HTTP. URL, API key and model come from environment/config; credentials are never persisted.

No mandatory provider SDK is introduced.

## Query semantics

A query embeds once, then performs cosine similarity against index vectors. Ranking is deterministic by `(-score, sourcePath, ordinal, chunkId)`.

Top semantic chunks become **seeds**. Seed paths are resolved to graph nodes by existing `sourcePath` or `path` properties. A chunk may resolve to multiple graph entities; that ambiguity is surfaced rather than silently collapsed.

## Graph expansion

Expansion uses only existing Neo4j relationships. It is bounded by depth and total nodes and returns:

- canonical ID / label;
- path/title/status when present;
- hop distance;
- traversal relationship/direction;
- originating semantic seed(s).

Semantic score and graph distance remain separate fields; V4 does not fabricate one opaque ranking score that hides provenance.

## ADR/spec discovery

Architecture discovery is implemented as a query mode/filter that prioritizes/retains `ADR`, `Spec` and `Requirement` anchors/expanded nodes. It does not add similarity edges such as `RELATED_TO`.

## Freshness

The index manifest is revision-bound. Strict query mode compares:

- repository ID;
- Git HEAD;
- provider ID;
- model ID;
- dimensions;
- chunk configuration.

A mismatch fails closed and instructs the operator to rebuild the index.

## Atomic build

Build complete content in memory, write temporary files in the destination directory, fsync/replace into the final index path, and publish the manifest last. A failed build must not leave a new manifest pointing to partial vectors.

## Security / privacy

- only tracked files are indexed;
- configured excluded paths remain excluded even if tracked;
- API keys stay in environment/config process memory only;
- index artifacts are gitignored;
- query/result packages are derived context;
- product runtime imports remain prohibited.

## Deferred

- vector DB / Neo4j vector index backend;
- cross-repository corpus;
- hybrid BM25 + vector fusion;
- learned reranker;
- LLM answer synthesis over retrieval results;
- semantic relationship promotion workflow.
