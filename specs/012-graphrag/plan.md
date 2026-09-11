# Implementation Plan: GraphRAG V4

## Scope

Implement a repository-local semantic retrieval layer for the Engineering Graph. Semantic vectors remain derived/disposable sidecar state; Neo4j remains the deterministic relationship projection.

## Architecture

### Components

1. `graphrag_corpus.py`
   - enumerate Git-tracked eligible files;
   - deterministic text normalization/chunking;
   - stable chunk IDs and content hashes.

2. `embeddings.py`
   - `EmbeddingProvider` protocol;
   - deterministic `HashingEmbeddingProvider` for CI/offline mechanics;
   - configurable `HttpEmbeddingProvider` for learned embeddings;
   - provider/model/dimension validation.

3. `graphrag_index.py`
   - versioned `SemanticIndex` / manifest;
   - atomic persistence;
   - semantic reproducibility payload;
   - strict freshness inspection.

4. `graphrag.py`
   - cosine retrieval;
   - deterministic ranking;
   - graph anchor resolution;
   - bounded graph expansion;
   - ADR/spec discovery filters;
   - versioned `GraphRagResult`.

5. CLI
   - `graphrag-build`
   - `graphrag-query`
   - `graphrag-validate`
   - `graphrag-status`

6. CI
   - offline deterministic build twice;
   - semantic payload reproducibility;
   - controlled retrieval assertion;
   - strict freshness;
   - ephemeral-Neo4j anchor/expansion smoke;
   - application-runtime isolation guard remains unchanged.

## Authority model

```text
Canonical Git files
      │
      ├─────────────► deterministic Engineering Graph (Neo4j)
      │
      └─────────────► derived semantic chunks/vectors (.graphrag/)
                              │
                              ▼
                     semantic seed retrieval
                              │
                              ▼
                 resolve seeds to existing graph nodes
                              │
                              ▼
                 traverse existing deterministic edges
```

No vector score changes canonical state. No semantic edge is written to Neo4j.

## Corpus defaults

Eligible extensions initially include:

- `.md`, `.txt`;
- `.py`;
- `.ts`, `.tsx`, `.js`, `.mjs`;
- `.json`;
- `.yaml`, `.yml`.

Always exclude generated/vendor/cache directories such as `.git`, `node_modules`, build/dist outputs, coverage, `.execution`, `.graphrag`, Playwright reports and generated context packages.

Only files returned by `git ls-files` can enter the corpus.

## Chunk defaults

- max characters: 1800;
- overlap characters: 200;
- preserve line provenance;
- deterministic path ordering;
- no tokenization SDK dependency.

Character budgets are intentional for provider neutrality. A later version may add token-aware provider-specific chunking behind the same schema.

## Provider strategy

### `hashing`

No network or credentials. Stable token hashing into a configurable fixed-dimensional vector, L2 normalized. Used for CI and deterministic local fallback. It validates retrieval plumbing but is not marketed as learned semantic quality.

### `http`

Environment/config driven. Standard JSON request containing `model` and `input`; response expects ordered embeddings. Authorization header is optional and credentials are never written to disk.

The index stores only non-secret provider/model identity and dimensions.

## Graph seed resolution

For the unique set of hit paths:

```cypher
MATCH (n {repository: $repository})
WHERE n.sourcePath IN $paths OR n.path IN $paths
RETURN labels(n), n.canonicalId, n.sourcePath, n.path, n.title, n.status
```

Expansion uses bounded path traversal and returns only existing relationship types. The implementation must never interpolate user input into labels/relationship patterns.

## Result semantics

`GraphRagResult` separates:

- `semanticHits`: ranked chunks + scores;
- `anchors`: deterministic graph nodes resolved from hit paths;
- `graphEvidence`: bounded existing graph neighborhood;
- `truncated`: budget signal;
- revision/provider/index metadata.

## Testing strategy

### Unit/offline

- tracked-file filtering;
- deterministic chunking;
- stable IDs/hashes;
- hashing provider reproducibility;
- cosine ranking/tie breaking;
- manifest semantic reproducibility;
- atomic load/write roundtrip;
- stale revision/provider/model detection;
- HTTP provider response validation using stubbed transport/server boundary.

### Ephemeral Neo4j

- full repository sync;
- build deterministic offline index;
- query phrase with expected `SPEC-012`/ADR path in top results;
- resolve semantic paths to existing nodes;
- bounded expansion contains only projected canonical IDs/relationships;
- architecture-only discovery mode;
- prove no new relationship types/nodes are persisted by GraphRAG query.

### Product regression

Existing application CI remains mandatory and unchanged in authority.

## Rollout phases

1. Spec Kit + ADR/design contract.
2. Corpus/chunking/provider boundary.
3. Index persistence/freshness.
4. Retrieval + graph expansion.
5. CLI/docs.
6. CI + analyze/converge/freeze.

## Non-goals

See `spec.md`; especially no answer-generation LLM, inferred canonical relationships, hosted vector DB requirement, or product-runtime integration.
