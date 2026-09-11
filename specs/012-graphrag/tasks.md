# Tasks: GraphRAG V4

## Phase 1 — Spec/architecture

- [x] T001 Create `SPEC-012-GRAPHRAG` feature specification.
- [x] T002 Record GraphRAG research and authority boundary.
- [x] T003 Define GraphRAG implementation plan.
- [x] T004 Define semantic/index/result data model.
- [x] T005 Add requirements checklist.
- [x] T006 Add quickstart/lifecycle documentation.
- [x] T007 Add ADR-0020 for derived semantic index boundary.

## Phase 2 — Corpus and embedding boundary

- [x] T008 Add GraphRAG configuration model/defaults.
- [x] T009 Enumerate eligible Git-tracked files only.
- [x] T010 Add deterministic text normalization.
- [x] T011 Add deterministic line-aware chunking.
- [x] T012 Add stable chunk IDs/content hashes.
- [x] T013 Add corpus include/exclude extension/path controls.
- [x] T014 Add `EmbeddingProvider` protocol.
- [x] T015 Add deterministic hashing provider for CI/offline validation.
- [x] T016 Add configurable HTTP learned-embedding provider.
- [x] T017 Validate provider/model/dimension contracts.

## Phase 3 — Semantic index

- [x] T018 Add versioned `SemanticIndexManifest`.
- [x] T019 Add versioned `SemanticIndex` serialization.
- [x] T020 Normalize vectors before persistence/search.
- [x] T021 Add semantic payload/hash reproducibility.
- [x] T022 Add atomic index write/load.
- [x] T023 Add strict repository/revision freshness inspection.
- [x] T024 Add provider/model/config compatibility validation.
- [x] T025 Add disposable default `.graphrag/` location.
- [x] T026 Ignore generated GraphRAG state in Git.

## Phase 4 — Retrieval and graph expansion

- [x] T027 Add cosine similarity retrieval.
- [x] T028 Add deterministic top-k/min-score ranking.
- [x] T029 Resolve semantic hit paths to deterministic Neo4j anchors.
- [x] T030 Preserve zero/one/many anchor ambiguity.
- [x] T031 Add bounded graph expansion by depth/node budget.
- [x] T032 Preserve existing relationship type/direction provenance.
- [x] T033 Keep semantic scores distinct from graph distance/evidence.
- [x] T034 Add architecture discovery mode for ADR/Spec/Requirement evidence.
- [x] T035 Add versioned `GraphRagResult` schema.
- [x] T036 Surface truncation/budget metadata.
- [x] T037 Prove GraphRAG query performs no Neo4j writes.

## Phase 5 — CLI and docs

- [x] T038 Add `graphrag-build` CLI.
- [x] T039 Add `graphrag-query` CLI.
- [x] T040 Add `graphrag-validate` CLI.
- [x] T041 Add `graphrag-status` CLI.
- [x] T042 Support JSON query output.
- [x] T043 Support human-readable query output.
- [x] T044 Update `engineering-graph/README.md`.
- [x] T045 Add `docs/architecture/GRAPHRAG.md`.
- [x] T046 Update `docs/development/engineering-graph.md`.
- [x] T047 Update `AGENTS.md` with GraphRAG retrieval workflow and authority rules.
- [x] T048 Update `docs/architecture/ENGINEERING_GRAPH.md` roadmap/state.

## Phase 6 — Unit/integration validation

- [x] T049 Test tracked-file filtering and excluded/untracked data.
- [x] T050 Test deterministic chunking/IDs/hashes.
- [x] T051 Test hashing-provider reproducibility.
- [x] T052 Test HTTP provider validation using a local/stubbed transport boundary.
- [x] T053 Test index roundtrip/atomic persistence.
- [x] T054 Test semantic index reproducibility.
- [x] T055 Test stale revision rejection.
- [x] T056 Test provider/model/config mismatch rejection.
- [x] T057 Test cosine ranking and deterministic tie breaks.
- [x] T058 Test graph anchor resolution.
- [x] T059 Test bounded graph expansion/truncation.
- [x] T060 Test architecture discovery mode.
- [x] T061 Test CLI build/query/validate/status surfaces.
- [x] T062 Re-run full existing Engineering Graph unit suite.

## Phase 7 — CI/convergence

- [x] T063 Add V4 offline GraphRAG build smoke to Engineering Graph CI.
- [x] T064 Build the same index twice and assert semantic reproducibility.
- [x] T065 Assert strict freshness on the CI index.
- [x] T066 Assert controlled ranked retrieval from repository fixtures/content.
- [x] T067 Assert Neo4j seed resolution and bounded expansion.
- [x] T068 Assert GraphRAG did not introduce new canonical node/relationship vocabulary.
- [x] T069 Preserve application runtime dependency isolation gate.
- [x] T070 Run Spec Kit validation on final closeout candidate HEAD.
- [x] T071 Run Engineering Graph workflow on final closeout candidate HEAD.
- [x] T072 Run Product CI on final closeout candidate HEAD.
- [x] T073 Create `analysis.md` mapping FR/SC to implementation evidence.
- [x] T074 Create `convergence.md` with final authority/freshness validation.
- [x] T075 Reconcile all task statuses against actual implementation evidence.
- [x] T076 Freeze V4 after Spec Kit + Engineering Graph + Product CI are green on the same closeout candidate; repeat all gates on this documentation-only freeze HEAD before PR readiness.
