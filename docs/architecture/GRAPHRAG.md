# GraphRAG V4

## Purpose

GraphRAG adds natural-language discovery to the Engineering Graph without changing repository authority. It retrieves semantically relevant chunks from tracked repository content and then expands those seeds through the existing deterministic Neo4j graph.

It is retrieval assistance, not a new source of truth.

## Authority boundary

```text
Git / Markdown / code / tests / Git history
          │
          ├──────────────► deterministic Engineering Graph
          │                       │
          │                       └─ existing explicit edges only
          │
          └──────────────► derived semantic corpus/index
                                  │
                                  └─ similarity scores only
```

Canonical relationships remain the ones extracted from explicit repository evidence. GraphRAG never writes similarity/inferred relationships into Neo4j.

Semantic chunks, vectors, manifests, scores and query results are disposable. Deleting `engineering-graph/.graphrag/` loses no canonical project knowledge.

## Retrieval pipeline

```text
Git-tracked eligible files
        │
        ▼
 deterministic chunking
        │
        ▼
 EmbeddingProvider
        │
        ▼
 SemanticIndex (.graphrag/index.json)
        │
        ▼
 natural-language query embedding
        │
        ▼
 cosine-ranked SemanticHit[]
        │
        ▼
 sourcePath/path anchor resolution
        │
        ▼
 existing Neo4j nodes
        │
        ▼
 bounded existing-edge expansion
        │
        ▼
 GraphRagResult
```

## Corpus safety

Only paths returned by `git ls-files` are eligible for indexing. V4 then applies explicit extension and excluded-prefix filters.

This matters because a local file merely existing on disk does not make it eligible. Untracked `.env`, local notes, temporary exports or accidentally created secret files are not indexed.

Generated state such as `.graphrag/`, `.execution/` and ContextPackages is excluded even if a path becomes tracked accidentally.

## Chunk identity

Chunks are deterministic and preserve repository provenance:

- repository-relative `sourcePath`;
- ordinal;
- start/end line;
- normalized text;
- SHA-256 content hash;
- stable chunk ID derived from repository/path/ordinal/content.

Default chunking is character-budget based (`1800` max, `200` overlap) to avoid tying the index schema to any one tokenizer SDK.

## Embedding providers

### Hashing provider

`hashing` is a deterministic zero-network retrieval surrogate. It tokenizes lexical features and feature-hashes them into an L2-normalized vector.

Its role is:

- CI mechanics;
- reproducibility testing;
- offline development;
- controlled retrieval fixtures.

It is **not** presented as equivalent to a learned semantic embedding model.

### HTTP provider

`http` connects V4 to a learned embedding endpoint without making a provider SDK mandatory. The endpoint receives JSON containing `model` and `input` and returns ordered embedding arrays.

Configuration uses environment/process state:

- `GRAPH_RAG_EMBEDDING_URL`
- `GRAPH_RAG_EMBEDDING_MODEL`
- `GRAPH_RAG_EMBEDDING_API_KEY`
- `GRAPH_RAG_DIMENSIONS`

Secrets are never persisted in the index manifest.

## Semantic index

Default location:

```text
engineering-graph/.graphrag/index.json
```

The manifest records:

- schema version;
- repository ID;
- source Git revision;
- provider/model identity;
- vector dimensions;
- chunk configuration;
- corpus filters;
- chunk count;
- semantic SHA-256;
- generation timestamp.

The semantic hash excludes generation timestamp. Rebuilding at the same revision/provider/model/config must produce the same semantic payload/hash.

Writes use a temporary sibling file plus fsync/atomic replace so an interrupted build does not publish a partial index.

## Freshness

Strict queries require:

- matching repository ID;
- matching Git HEAD;
- matching provider;
- matching model;
- matching vector dimensions;
- matching chunk/corpus configuration.

A stale or incompatible index fails closed. Rebuild instead of bypassing freshness for implementation decisions.

`--allow-stale` exists only for deliberate exploratory retrieval where revision mismatch is understood; it does not permit provider/model/config incompatibility.

## Search and ranking

The query vector is compared to each stored vector using cosine similarity. Results are deterministically ordered by:

1. score descending;
2. source path;
3. ordinal;
4. chunk ID.

`--top-k` and `--min-score` bound retrieval.

Architecture mode prioritizes repository architecture paths (`docs/adr/`, `docs/architecture/`, `specs/`) in presentation/selection while preserving the original semantic score. It does not fabricate a combined opaque relevance score.

## Graph anchor resolution

Semantic hits are not graph nodes by themselves. Hit paths are resolved to deterministic projected nodes using existing `sourcePath` and `path` properties.

One path may resolve to zero, one or multiple graph anchors. Ambiguity is retained in the result rather than silently selecting one entity.

## Graph expansion

Expansion starts from resolved anchors and traverses only relationships already present in the Engineering Graph. Query depth is clamped to a small bounded range and total returned unique nodes are budgeted.

Evidence preserves:

- canonical ID and label;
- distance from an anchor;
- repository path/title/status where available;
- originating semantic seed(s);
- originating graph anchor(s);
- relationship type and original direction along the chosen path.

Semantic score and graph distance stay separate. Similarity is discovery evidence; the traversed edge is deterministic architecture evidence.

## CLI

```bash
graph-engineering graphrag-build --provider hashing
graph-engineering graphrag-status --provider hashing
graph-engineering graphrag-validate --provider hashing --strict
graph-engineering graphrag-query \
  "where is execution isolation defined?" \
  --provider hashing \
  --mode architecture \
  --top-k 8 \
  --depth 2 \
  --max-nodes 80
```

For learned retrieval use `--provider http` with the HTTP environment configuration.

## Result layers

A `GraphRagResult` deliberately separates:

1. `semanticHits` — vector retrieval evidence;
2. `anchors` — deterministic graph nodes matched from hit paths;
3. `graphEvidence` — bounded traversal over already-projected relationships.

Agents must keep those evidence types distinct when reasoning about changes.

## CI invariants

Engineering Graph CI validates V4 with the offline hashing provider:

1. build index;
2. strict freshness validation;
3. rebuild and compare semantic payload/hash;
4. execute a controlled architecture query;
5. require Spec 012 / ADR-0020 semantic evidence;
6. require resolved deterministic anchors and graph evidence;
7. compare logical graph stats before and after GraphRAG query.

The before/after stats comparison is the operational guard that GraphRAG queries remain read-only with respect to the canonical graph projection.

## Failure model

- GraphRAG index missing/stale: rebuild it.
- learned embedding endpoint unavailable: use canonical files/graph directly or the hashing provider for mechanics; do not pretend hashing provides equivalent semantic quality.
- Neo4j unavailable: semantic retrieval can still be used independently, but graph expansion is unavailable.
- GraphRAG failure never breaks application runtime.

## Explicit non-goals

V4 does not provide:

- inferred canonical edges;
- LLM answer synthesis;
- autonomous requirement/ADR/task authoring;
- hosted vector database requirement;
- cross-repository organizational RAG;
- product/business runtime retrieval;
- autonomous commit/push/PR/merge;
- agent scheduler/supervisor behavior.

Any future promotion of semantic inference into graph authority requires a separate ADR defining review, provenance and validation semantics.
