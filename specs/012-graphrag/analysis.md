# Analyze: GraphRAG V4

**Feature**: `SPEC-012-GRAPHRAG`  
**Implementation anchor**: `68db3aab09a1317bbd8628564dccbcdcde5f7f45`  
**Status**: Implementation-complete; final documentation/freeze gates pending

## Authority analysis

PASS.

V4 preserves the established source-of-truth hierarchy:

```text
Git / Markdown / code / tests / Git history
                  │
          ┌───────┴──────────┐
          ▼                  ▼
 deterministic Neo4j    derived semantic index
      projection          (.graphrag/)
          │                  │
          │            semantic retrieval
          │                  │
          └────────┬─────────┘
                   ▼
          deterministic path anchor
                   │
                   ▼
        existing-edge graph expansion
```

No implementation path writes semantic similarity into Neo4j. `GraphRagResult` deliberately separates vector retrieval evidence from deterministic graph anchors/evidence.

## Functional requirement traceability

| Requirement | Result | Implementation / evidence |
|---|---|---|
| FR-001 tracked-files-only corpus | PASS | `graphrag_corpus.git_tracked_paths`, `eligible_tracked_paths`, `test_graphrag_corpus` |
| FR-002 deterministic chunking | PASS | `normalize_text`, `chunk_text`, deterministic corpus tests |
| FR-003 stable chunk provenance | PASS | `CorpusChunk`/`IndexedChunk`: ID, path, ordinal, line range, content hash, text |
| FR-004 semantic state outside canonical Neo4j vocabulary | PASS | ADR-0020, `.graphrag/` sidecar, read-only GraphRAG queries |
| FR-005 versioned manifest identity | PASS | `SemanticIndexManifest` records repo/revision/provider/model/dims/config/count/hash |
| FR-006 provider abstraction/batching | PASS | `EmbeddingProvider`, `_embed_chunks`, configurable batch size |
| FR-007 deterministic offline provider | PASS | `HashingEmbeddingProvider`, tests/docs explicitly label it a surrogate |
| FR-008 configurable HTTP learned provider | PASS | `HttpEmbeddingProvider`, stdlib HTTP, env-driven endpoint/model/key |
| FR-009 cosine search under same provider/model/dim contract | PASS | `cosine_similarity`, provider/model/dim guards in `search_semantic_index` |
| FR-010 top-k/min-score | PASS | `search_semantic_index`, CLI `--top-k` / `--min-score` |
| FR-011 hit score/provenance/anchors | PASS | `SemanticHit`, `GraphAnchor`, JSON/human CLI output |
| FR-012 source path → deterministic anchors | PASS | `resolve_graph_anchors` queries existing `sourcePath`/`path`; CI smoke resolves Spec 012/ADR-0020 |
| FR-013 existing-edge expansion only | PASS | `expand_graph` traverses existing relationships; no create/merge write path |
| FR-014 depth/node budgets + truncation | PASS | depth clamp, unique-node limit, `truncated` result |
| FR-015 ADR/spec discovery | PASS | `mode=architecture` prioritizes architecture paths while preserving graph-connected evidence |
| FR-016 semantic vs graph evidence distinction | PASS | separate `semanticHits`, `anchors`, `graphEvidence` result collections |
| FR-017 revision/index identity in results | PASS | `GraphRagResult.source_revision`, `index_semantic_sha256`, provider/model |
| FR-018 strict stale-index rejection | PASS | `inspect_index_freshness`, strict query gate, stale-revision test + CI validation |
| FR-019 provider/model/config drift requires rebuild | PASS | compatibility checks return `incompatible`; tests cover model mismatch |
| FR-020 atomic index writes | PASS | temp sibling + flush/fsync + `os.replace`; load validates hash/count/dims |
| FR-021 same-state semantic reproducibility | PASS | semantic payload/hash excludes timestamp; unit test + CI double-build comparison |
| FR-022 generated state disposable/gitignored | PASS | `.gitignore`, default `.graphrag/index.json`, architecture/docs |
| FR-023 product runtime independence | PASS | existing CI import/Neo4j guard still green with V4 |
| FR-024 no canonical/task/PR/lease mutation | PASS | GraphRAG modules expose retrieval/read-only graph access only; ADR/AGENTS enforce boundary |
| FR-025 build/query/validate/status CLI | PASS | four `graphrag-*` subcommands registered in `cli.py` |
| FR-026 JSON + human output | PASS | GraphRAG CLI handlers provide structured JSON and text rendering |
| FR-027 CI retrieval/freshness/Neo4j expansion gates | PASS | Engineering Graph #240 includes five V4 smokes after full sync |
| FR-028 credentials not persisted | PASS | API key read only by HTTP provider; manifest stores provider/model identity but no secret/URL/key |
| FR-029 untracked/sensitive local files excluded | PASS | corpus begins with `git ls-files`; unit test verifies untracked `secret.md` omission |
| FR-030 V1–V3 backward compatibility | PASS | full prior Engineering Graph suite/smokes green on implementation anchor |

## Success criteria traceability

| Criterion | Result | Evidence |
|---|---|---|
| SC-001 identical chunks/index semantics at same state | PASS | chunk tests + unit index `semantic_json` + CI double-build hash comparison |
| SC-002 controlled relevant retrieval in top-k | PASS | unit ranking fixtures + live CI controlled GraphRAG query |
| SC-003 stale strict query rejected | PASS | `test_strict_freshness_rejects_new_git_revision` + strict CI validation |
| SC-004 graph evidence traces to projected entities/edges | PASS | anchor/expansion tests + ephemeral Neo4j V4 query smoke |
| SC-005 no canonical semantic relationship writes | PASS | read-only implementation + fake-store write assertion + before/after Neo4j stats equality |
| SC-006 ADR/spec discovery with provenance | PASS | architecture mode + CI requires Spec 012/ADR-0020 hit/anchor evidence |
| SC-007 bounded expansion/truncation | PASS | explicit depth/node budgets and tests |
| SC-008 learned HTTP embeddings without runtime/SDK coupling | PASS | stdlib `HttpEmbeddingProvider`; product isolation gate green |
| SC-009 `.graphrag/` disposable/rebuildable | PASS | Git ignore + build lifecycle docs; source corpus remains Git-backed |
| SC-010 all independent validation domains green | PASS on implementation anchor | Spec Kit #326, Engineering Graph #240, Product CI #638 |

## Implementation anchor validation

`68db3aab09a1317bbd8628564dccbcdcde5f7f45` passed:

### Spec Kit #326 — PASS

- integration/status validation;
- historical spec artifact shape checks.

### Engineering Graph #240 — PASS

- full Python offline/unit/integration suite;
- real V3 temporary Git worktree tests;
- V4 tracked-corpus/provider/index/retrieval/CLI tests;
- application runtime dependency isolation;
- ephemeral Neo4j schema/full sync/idempotency/validation;
- V1 fundamental queries;
- V2 context freshness/adapters/reproducibility/disposal;
- V3 execution planning/reproducibility/conflict/completed-state smokes;
- V4 offline semantic index build;
- V4 strict freshness;
- V4 semantic index double-build reproducibility;
- V4 natural-language query with semantic hit → Spec 012/ADR-0020 anchor → deterministic graph evidence;
- V4 before/after graph stats equality proving query did not mutate projected graph state/vocabulary.

### Product CI #638 — PASS

- PostgreSQL migrations + seed;
- typecheck;
- tests;
- production build;
- Storybook component/accessibility tests;
- Playwright E2E.

## Analyze findings

### 1. Provider semantics are intentionally asymmetric

`hashing` and `http` share the provider/index contract but not retrieval quality expectations. This is intentional and documented. CI proves deterministic mechanics with `hashing`; real learned semantic quality belongs to `http` or future providers.

### 2. Semantic score is not architecture authority

Architecture mode prioritizes architecture source paths for discovery, but it preserves raw similarity scores and does not manufacture an opaque combined score. Relationship claims still require existing graph evidence or canonical-file inspection.

### 3. Anchor ambiguity is valid

A source path may map to zero, one or many deterministic graph nodes. V4 retains all matches. It does not silently invent a unique semantic-to-graph identity.

### 4. Sidecar JSON is intentionally V4-scale

The repository-local JSON index keeps persistence inspectable and service-free. A future vector backend may be justified by corpus scale, but changing storage must not change the current authority/result contracts.

### 5. No answer-generation layer is present

V4 returns evidence packages. It does not ask an LLM to synthesize an authoritative answer, requirement, ADR or graph edge. This keeps retrieval independently inspectable and prevents accidental scope expansion.

## Risks and controls

| Risk | Control |
|---|---|
| stale semantic index | revision-bound manifest + strict freshness fail-closed |
| provider/model drift | compatibility validation + rebuild requirement |
| accidental local-secret indexing | corpus originates from `git ls-files` and excludes generated prefixes |
| semantic similarity mistaken for dependency | evidence layers separated; no semantic relationship writes |
| partial/corrupt index | atomic replace + semantic hash/count/dimension validation |
| hidden graph mutation during retrieval | read-only code path + CI logical stats equality before/after query |
| GraphRAG leaking into product runtime | existing `apps/packages` dependency isolation gate |
| hashing provider overstated as semantic model | explicit surrogate labeling in code/docs/CLI |

## Deferred items are not convergence gaps

The following remain intentionally outside V4:

- semantic similarity as canonical Neo4j edges;
- LLM answer synthesis/reranking;
- AI-authored canonical requirements/ADRs/tasks;
- hosted/local vector database requirement;
- cross-repository organizational corpus;
- distributed scheduler/agent supervision;
- automatic task mutation, commit, push, PR creation or merge;
- product/business runtime RAG.

## Analyze conclusion

No implementation gap remains against FR-001…FR-030 or SC-001…SC-010 on the implementation anchor. The remaining lifecycle work is documentary reconciliation/freeze: publish `convergence.md`, reconcile task status, and repeat Spec Kit + Engineering Graph + Product CI on the resulting closeout HEAD before final freeze.
