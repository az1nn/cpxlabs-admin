# Convergence: GraphRAG V4

**Feature**: `SPEC-012-GRAPHRAG`  
**Implementation anchor**: `68db3aab09a1317bbd8628564dccbcdcde5f7f45`  
**Status**: Converging — implementation complete, final closeout gates pending

## Conclusion

GraphRAG V4 is implementation-complete and functionally converged against its specification. It adds revision-bound semantic repository discovery while preserving the deterministic Engineering Graph as the only graph relationship projection.

The implementation delivers:

- Git-tracked-only semantic corpus;
- deterministic normalized chunking with stable IDs/line provenance/content hashes;
- pluggable embedding provider contract;
- deterministic zero-network hashing provider for CI/offline mechanics;
- configurable learned HTTP embedding provider without mandatory SDK dependency;
- versioned revision/provider/model/config-bound semantic index;
- semantic payload/hash reproducibility independent of timestamps;
- atomic index replacement and corruption validation;
- strict stale/incompatible index detection;
- deterministic cosine top-k/min-score retrieval;
- architecture-oriented ADR/spec discovery;
- semantic-hit path resolution to existing Neo4j nodes;
- bounded traversal over existing deterministic relationships only;
- separate semantic, anchor and graph evidence layers;
- build/query/validate/status CLI surfaces;
- disposable `.graphrag/` state;
- V4 Engineering Graph CI with real ephemeral-Neo4j retrieval/expansion;
- before/after graph stats equality proving GraphRAG query is read-only.

No semantic similarity edge, canonical project mutation, product runtime dependency or autonomous agent/PR behavior was introduced.

## Source-of-truth convergence

PASS.

```text
Canonical Git-backed knowledge
          │
          ├─────────────────────► deterministic Neo4j projection
          │                                │
          │                                │ existing edges
          │                                │
          └──► derived semantic index      │
                     │                     │
                     ▼                     │
              semantic retrieval           │
                     │                     │
                     ▼                     │
                 source paths              │
                     │                     │
                     └──── resolve ─────────┘
                               │
                               ▼
                    bounded graph evidence
```

The semantic sidecar can be deleted and rebuilt. Its scores never become canonical graph truth.

## V1–V4 compatibility

PASS.

V4 composes with prior layers rather than replacing them:

- **V1** owns deterministic extraction, schema, traceability, validation and task planning evidence;
- **V2** owns portable revision-aware ContextPackages and agent handoffs;
- **V3** owns revision-bound execution manifests, isolated worktrees and derived local leases;
- **V4** owns semantic discovery/indexing and read-only expansion through V1 graph evidence.

Existing V1–V3 unit/integration/smoke gates remained green on the V4 implementation anchor.

## Semantic-index convergence

PASS.

Index identity includes:

- repository;
- Git source revision;
- provider/model;
- dimensions;
- chunk size/overlap;
- include extensions;
- excluded prefixes;
- chunk count;
- semantic SHA-256.

`generatedAt` is excluded from semantic equality. Two builds at the same state produce the same semantic JSON/hash.

Strict validation rejects stale Git revision and provider/model/dimension/config mismatch. Index writes use a temporary sibling, fsync and atomic replace; load validates schema, chunk count, dimensions and semantic hash.

## Corpus/security convergence

PASS.

The corpus starts with `git ls-files`, then applies explicit allow/exclude rules. This prevents untracked local files from entering retrieval state merely by existing on disk.

Learned-provider credentials remain environment/process-local and are not persisted in the index manifest. Generated `.graphrag/` state is Git-ignored.

## Retrieval/graph convergence

PASS.

Retrieval and graph evidence stay distinct:

```text
SemanticHit(score, chunk/path/lines)
        │
        ▼
GraphAnchor(existing canonicalId matched by sourcePath/path)
        │
        ▼
GraphEvidence(existing relationships, direction, distance, provenance)
```

One hit may resolve to zero, one or multiple anchors. Expansion is depth/node bounded and reports truncation. It traverses relationships already stored in Neo4j and has no mutation operation.

Architecture mode prioritizes architecture paths for discovery while preserving raw semantic scores and supporting graph-connected code/test/task evidence.

## Provider convergence

PASS.

### Hashing provider

Purpose: deterministic offline/CI retrieval mechanics. It is explicitly documented as a surrogate and is not represented as equivalent to a learned semantic model.

### HTTP provider

Purpose: learned semantic embeddings through a configurable endpoint using stdlib HTTP. Provider URL/key/model are not coupled into product runtime and no provider SDK is mandatory.

## Implementation anchor validation

`68db3aab09a1317bbd8628564dccbcdcde5f7f45` passed all three independent domains before closeout documentation:

### Spec Kit #326 — PASS

Spec Kit integration/status and historical artifact-shape gates passed.

### Engineering Graph #240 — PASS

- full offline Python suite including V4 corpus/provider/index/retrieval/CLI tests;
- V3 real temporary Git worktree tests;
- application-runtime dependency isolation;
- ephemeral Neo4j schema, full sync, stats, repeated-sync idempotency and graph validation;
- V1 query smokes;
- V2 ContextPackage generation/freshness/adapters/reproducibility/disposal;
- V3 ExecutionManifest reproducibility/conflict/completed-state checks;
- V4 semantic index build;
- strict V4 freshness validation;
- second V4 build with semantic JSON/hash reproducibility equality;
- controlled V4 architecture query retrieving Spec 012 / ADR-0020 evidence;
- semantic paths resolving to deterministic graph anchors;
- bounded graph expansion returning existing relationship evidence;
- graph stats before/after GraphRAG query exactly equal.

### Product CI #638 — PASS

- PostgreSQL migrations + seed;
- typecheck;
- tests;
- production build;
- Storybook component/accessibility tests;
- Playwright E2E.

## Analyze findings resolved

### Semantic evidence cannot silently become graph authority

Resolved structurally. Sidecar vector state is separate from Neo4j, result schemas separate semantic and graph layers, and CI proves graph stats are unchanged by query.

### Offline CI must not overstate retrieval quality

Resolved in code/docs/CLI. The hashing provider is consistently described as a deterministic retrieval surrogate. Learned semantic retrieval uses the HTTP provider contract.

### Index freshness must cover more than Git SHA

Resolved. Strict compatibility includes repository, source revision, provider, model, dimensions and corpus/chunk configuration.

### Local secret indexing risk

Resolved. The corpus originates only from tracked paths and tests explicitly prove an untracked `secret.md` is omitted.

### Storage backend must not become semantic authority

Resolved. V4 uses transparent JSON sidecar persistence, but contracts are defined in terms of `SemanticIndex`/`GraphRagResult`; a future backend may replace storage without changing authority semantics.

## Deferred by design

The following are intentionally not convergence gaps:

- `SIMILAR_TO`/`RELATED_TO` or other inferred canonical relationships;
- LLM answer synthesis or learned reranking;
- automatic promotion of retrieval output into Spec/ADR/Task state;
- hosted vector database requirement;
- cross-repository/global corpus;
- distributed scheduler or coding-agent supervision;
- automatic commit/push/PR/merge;
- product runtime GraphRAG.

A future change that promotes semantic inference into canonical graph authority requires a separate ADR with explicit provenance/review/validation semantics.

## Closeout state

Implementation evidence and the initial three-domain validation are complete. `analysis.md` is complete and T001–T069 can be reconciled as implemented/validated.

Before V4 is frozen and PR #20 becomes Ready for Review:

1. reconcile the Spec 012 task ledger;
2. run Spec Kit, Engineering Graph and Product CI on the resulting closeout HEAD;
3. record those final run IDs/HEAD;
4. mark T076 complete only after all three are green on the same final HEAD;
5. repeat the gates if the final freeze checkbox/metadata changes the HEAD, preserving the same completed-spec-safe principle established in V3.
