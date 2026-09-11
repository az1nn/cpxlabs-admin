# ADR-0020: Keep GraphRAG semantic state outside canonical graph authority

## Status

Accepted

## Context

The Engineering Graph currently derives deterministic nodes and relationships from explicit Git-backed evidence. V4 adds semantic retrieval so engineers and coding agents can discover relevant repository material without knowing exact canonical IDs or paths.

Embedding vectors and similarity scores are provider/model dependent, probabilistic in utility, and rebuildable. Treating them as canonical Neo4j relationships would blur the existing authority model and make model/provider lifecycle changes look like architecture changes.

## Decision

GraphRAG semantic chunks, vectors, index manifests, scores and result packages are derived/disposable sidecar state outside the canonical Neo4j graph vocabulary.

Semantic retrieval may identify seed paths. Those paths may then be resolved to existing Engineering Graph nodes through deterministic `sourcePath`/`path` evidence. Graph expansion traverses only relationships that already exist in the deterministic graph projection.

GraphRAG MUST NOT create semantic relationship types such as `SIMILAR_TO`, `RELATED_TO` or inferred `DEPENDS_ON` in the canonical graph.

The default V4 index is repository-local under `engineering-graph/.graphrag/` and is ignored by Git. It is revision/provider/model/config bound and rebuildable.

Embedding providers are pluggable. A deterministic offline hashing provider exists only for CI/offline mechanics; learned semantic quality is provided through a configurable HTTP embedding endpoint without adding a mandatory SDK or product-runtime dependency.

## Consequences

### Positive

- preserves Git and deterministic graph authority;
- semantic model/provider changes do not rewrite architecture truth;
- GraphRAG can be removed/rebuilt without data migration risk;
- CI can validate retrieval mechanics without network credentials;
- a future vector backend can replace the V4 JSON sidecar without changing canonical graph semantics.

### Negative

- semantic index lifecycle is separate from Neo4j sync lifecycle;
- operators must rebuild after relevant Git/provider/config drift;
- large repositories may eventually outgrow in-process JSON/cosine search.

## Rejected alternatives

### Store embeddings directly on canonical Neo4j nodes

Rejected for V4 because it couples retrieval-provider lifecycle to deterministic projection state and encourages semantic evidence to look authoritative.

### Create semantic relationships in Neo4j

Rejected because similarity is retrieval assistance, not explicit repository evidence.

### Require a hosted vector database

Rejected because current repository scale and CI needs do not justify another mandatory service.

### Require an embedding SDK/model package

Rejected because it increases toolchain weight and makes CI/network behavior provider-specific. V4 uses a provider protocol plus stdlib HTTP boundary instead.

## Governance

Any future proposal to promote inferred semantic relationships into canonical graph authority requires a new ADR and must define review, provenance, validation and conflict semantics explicitly.
