# Convergence: GraphRAG V4

**Feature**: `SPEC-012-GRAPHRAG`  
**Implementation anchor**: `68db3aab09a1317bbd8628564dccbcdcde5f7f45`  
**Closeout candidate**: `2b61bcd8f5ef70ada75c2ece34ed368c9e91d35e`  
**Status**: Converged

## Conclusion

GraphRAG V4 is converged against `SPEC-012-GRAPHRAG`. It adds revision-bound semantic repository discovery while preserving the deterministic Engineering Graph as the only graph relationship projection.

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

Existing V1–V3 unit/integration/smoke gates remained green throughout V4 implementation and closeout.

## Semantic-index convergence

PASS.

Index identity includes repository, Git source revision, provider/model, dimensions, chunk size/overlap, include extensions, excluded prefixes, chunk count and semantic SHA-256.

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

`68db3aab09a1317bbd8628564dccbcdcde5f7f45` passed all three independent domains before analyze/converge documentation:

- **Spec Kit #326 — PASS**
- **Engineering Graph #240 — PASS**
- **Product CI #638 — PASS**

Engineering Graph #240 covered the full offline suite, V1–V3 regression smokes, V4 build/freshness/reproducibility, real ephemeral-Neo4j semantic seed resolution/expansion and before/after graph stats equality. Product CI #638 covered migrations/seed, typecheck, tests, production build, Storybook/a11y and Playwright E2E.

## Closeout candidate validation

After `analysis.md`, `convergence.md`, permanent GraphRAG docs and the reconciled ledger were present, closeout candidate `2b61bcd8f5ef70ada75c2ece34ed368c9e91d35e` passed:

### Spec Kit #332 — PASS

- integration/status validation;
- historical artifact-shape validation.

### Engineering Graph #246 — PASS

- full offline Python/unit/integration suite;
- product-runtime dependency isolation;
- ephemeral Neo4j schema/full sync/idempotency/architecture validation;
- all V1 query smokes;
- all V2 context/freshness/adapter/reproducibility/disposal smokes;
- all V3 execution/reproducibility/conflict/completed-state smokes;
- V4 GraphRAG index build and strict freshness;
- V4 double-build semantic reproducibility;
- V4 controlled architecture retrieval with Spec 012 / ADR-0020 evidence;
- deterministic anchor resolution and bounded existing-edge expansion;
- logical graph stats unchanged after GraphRAG query.

### Product CI #644 — PASS

- migrations + seed;
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

## Freeze state

`SPEC-012-GRAPHRAG` is converged and T001–T076 are complete. The current branch contains only the documentation-only freeze transition after the fully green closeout candidate.

Before PR #20 is marked Ready for Review, this freeze HEAD must repeat **Spec Kit + Engineering Graph + Product CI** successfully. No V5 or post-V4 scope may be added to this PR; future work starts in a new Spec Kit feature branch and a new PR.
