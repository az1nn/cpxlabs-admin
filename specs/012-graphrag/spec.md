---
graph:
  id: SPEC-012-GRAPHRAG
  status: active
  enforced: true
  constrained_by:
    - ADR-0020
---

# Feature Specification: GraphRAG V4

## Objective

Add semantic discovery to the repository-local Engineering Graph without changing the repository authority model. Natural-language queries should find relevant repository content, then expand from those semantic seeds through deterministic Neo4j relationships to surface nearby Specs, ADRs, Requirements, Tasks, code/test artifacts and PR evidence.

Git-backed files remain canonical. Embeddings, semantic chunks, vector indexes, scores and GraphRAG result packages are derived/disposable retrieval state. Semantic similarity MUST NOT create or mutate canonical graph edges.

## User stories

### US1 — Natural-language repository discovery

As an engineer or coding agent, I can search for a concept without knowing an exact canonical ID or path and receive ranked repository evidence with source paths, chunk provenance and semantic scores.

### US2 — Graph expansion around semantic seeds

As an engineer or coding agent, I can expand top semantic hits through the existing deterministic Engineering Graph with explicit depth/node budgets, preserving relationship provenance and direction.

### US3 — ADR/spec discovery

As an architect, I can ask a conceptual question and preferentially discover relevant ADRs, Specs and Requirements while still seeing supporting code/test/task evidence when graph-connected.

### US4 — Fresh, rebuildable semantic state

As a maintainer, I can rebuild the semantic index from tracked repository files, detect source-revision/provider/model drift, and reject stale indexes in strict mode.

### US5 — Offline validation

As CI, I can validate chunking, indexing, ranking, freshness and graph-expansion mechanics deterministically without requiring external embedding credentials or network access.

## Functional requirements

- **FR-001** The system MUST build a semantic index only from Git-tracked repository files selected by explicit include/exclude rules.
- **FR-002** Chunking MUST be deterministic for the same repository revision and configuration.
- **FR-003** Every chunk MUST expose a stable chunk ID, source path, ordinal/range metadata, content hash and text.
- **FR-004** The semantic index MUST be derived state outside the canonical Neo4j node/relationship vocabulary.
- **FR-005** The index manifest MUST record repository ID, source revision, provider ID, model ID, vector dimensions, chunking configuration, chunk count and semantic content hash.
- **FR-006** Embedding generation MUST be behind a provider interface with deterministic batching and explicit provider/model identity.
- **FR-007** A built-in deterministic offline provider MUST exist for tests and zero-network validation and MUST be labeled as a retrieval surrogate rather than equivalent to a learned semantic model.
- **FR-008** A configurable HTTP embedding provider MUST support real learned embeddings without adding a mandatory SDK dependency.
- **FR-009** Search MUST use cosine similarity over vectors produced by the same provider/model/dimension contract as the index.
- **FR-010** Search MUST support top-k and minimum-score bounds.
- **FR-011** Search results MUST include score, chunk provenance, source path and any resolved graph anchor IDs.
- **FR-012** The system MUST resolve semantic seed paths to existing deterministic graph nodes using `sourcePath` and `path` evidence.
- **FR-013** Graph expansion MUST traverse only relationships already present in the Engineering Graph projection.
- **FR-014** Graph expansion MUST enforce depth and node budgets and surface truncation.
- **FR-015** GraphRAG MUST support ADR/spec-oriented discovery that boosts/filter-selects architecture artifacts without inventing relationships.
- **FR-016** Result packages MUST distinguish semantic evidence from deterministic graph evidence.
- **FR-017** Result packages MUST record the repository revision and semantic-index revision used to answer the query.
- **FR-018** Strict query mode MUST fail closed when the semantic index revision does not match current Git HEAD.
- **FR-019** Provider/model/config drift MUST require index rebuild before strict querying.
- **FR-020** Index writes MUST be atomic enough that an interrupted build cannot replace the last valid manifest/index with partial content.
- **FR-021** Rebuilding an index at the same revision/config/provider/model MUST produce semantically reproducible index content independent of generation timestamps.
- **FR-022** Generated semantic state MUST be disposable and ignored by Git.
- **FR-023** Application packages MUST NOT depend on the GraphRAG implementation, embedding provider, Neo4j driver or generated semantic state.
- **FR-024** GraphRAG MUST NOT mutate Spec Kit task status, ADR status, source files, Git branches, PRs or Execution Graph leases.
- **FR-025** The CLI MUST expose explicit build, query, validate and status operations.
- **FR-026** Query output MUST support machine-readable JSON and human-readable Markdown/text rendering.
- **FR-027** CI MUST exercise index reproducibility, stale-index detection, ranked retrieval, deterministic seed resolution and bounded graph expansion against ephemeral Neo4j.
- **FR-028** Learned embedding credentials/URLs MUST be supplied through environment/config and MUST never be persisted in the generated index manifest.
- **FR-029** Sensitive or ignored/untracked files MUST not be indexed merely because they exist on disk.
- **FR-030** Existing V1–V3 behavior and authority boundaries MUST remain backward compatible.

## Success criteria

- **SC-001** Same revision/config/provider produces identical semantic chunk IDs and semantic index payload/hash.
- **SC-002** Offline CI retrieves a known relevant document in the expected top-k set for controlled fixtures.
- **SC-003** Strict querying rejects an index whose source revision differs from current Git HEAD.
- **SC-004** Every graph-expanded entity can be traced to an existing deterministic Neo4j node/relationship.
- **SC-005** No GraphRAG operation creates canonical graph relationships or writes canonical project knowledge.
- **SC-006** ADR/spec discovery returns architecture artifacts with explicit semantic and/or graph provenance.
- **SC-007** Graph expansion obeys configured depth/node budgets and reports truncation.
- **SC-008** HTTP embedding configuration can be used without adding a product-runtime dependency or mandatory embedding SDK.
- **SC-009** Generated `.graphrag/` state can be deleted and rebuilt without information loss to canonical repository state.
- **SC-010** Engineering Graph, Spec Kit and Product CI remain green at convergence.

## Explicitly out of scope

- semantic similarity as authoritative graph edges;
- LLM-generated requirements/ADRs/tasks becoming canonical automatically;
- autonomous commit/push/PR/merge;
- agent process supervision or distributed scheduling;
- production/business-runtime RAG;
- cross-repository/global organizational knowledge graph;
- hosted vector database requirement;
- replacing deterministic ContextPackage or ExecutionManifest semantics.
