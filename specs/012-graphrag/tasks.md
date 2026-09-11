# Tasks: GraphRAG V4

## Phase 1 — Spec/architecture

- [x] T001 Create `SPEC-012-GRAPHRAG` feature specification.
- [x] T002 Record GraphRAG research and authority boundary.
- [x] T003 Define GraphRAG implementation plan.
- [x] T004 Define semantic/index/result data model.
- [ ] T005 Add requirements checklist.
- [ ] T006 Add quickstart/lifecycle documentation.
- [ ] T007 Add ADR-0020 for derived semantic index boundary.

## Phase 2 — Corpus and embedding boundary

- [ ] T008 Add GraphRAG configuration model/defaults.
- [ ] T009 Enumerate eligible Git-tracked files only.
- [ ] T010 Add deterministic text normalization.
- [ ] T011 Add deterministic line-aware chunking.
- [ ] T012 Add stable chunk IDs/content hashes.
- [ ] T013 Add corpus include/exclude extension/path controls.
- [ ] T014 Add `EmbeddingProvider` protocol.
- [ ] T015 Add deterministic hashing provider for CI/offline validation.
- [ ] T016 Add configurable HTTP learned-embedding provider.
- [ ] T017 Validate provider/model/dimension contracts.

## Phase 3 — Semantic index

- [ ] T018 Add versioned `SemanticIndexManifest`.
- [ ] T019 Add versioned `SemanticIndex` serialization.
- [ ] T020 Normalize vectors before persistence/search.
- [ ] T021 Add semantic payload/hash reproducibility.
- [ ] T022 Add atomic index write/load.
- [ ] T023 Add strict repository/revision freshness inspection.
- [ ] T024 Add provider/model/config compatibility validation.
- [ ] T025 Add disposable default `.graphrag/` location.
- [ ] T026 Ignore generated GraphRAG state in Git.

## Phase 4 — Retrieval and graph expansion

- [ ] T027 Add cosine similarity retrieval.
- [ ] T028 Add deterministic top-k/min-score ranking.
- [ ] T029 Resolve semantic hit paths to deterministic Neo4j anchors.
- [ ] T030 Preserve zero/one/many anchor ambiguity.
- [ ] T031 Add bounded graph expansion by depth/node budget.
- [ ] T032 Preserve existing relationship type/direction provenance.
- [ ] T033 Keep semantic scores distinct from graph distance/evidence.
- [ ] T034 Add architecture discovery mode for ADR/Spec/Requirement evidence.
- [ ] T035 Add versioned `GraphRagResult` schema.
- [ ] T036 Surface truncation/budget metadata.
- [ ] T037 Prove GraphRAG query performs no Neo4j writes.

## Phase 5 — CLI and docs

- [ ] T038 Add `graphrag-build` CLI.
- [ ] T039 Add `graphrag-query` CLI.
- [ ] T040 Add `graphrag-validate` CLI.
- [ ] T041 Add `graphrag-status` CLI.
- [ ] T042 Support JSON query output.
- [ ] T043 Support human-readable query output.
- [ ] T044 Update `engineering-graph/README.md`.
- [ ] T045 Add `docs/architecture/GRAPHRAG.md`.
- [ ] T046 Update `docs/development/engineering-graph.md`.
- [ ] T047 Update `AGENTS.md` with GraphRAG retrieval workflow and authority rules.
- [ ] T048 Update `docs/architecture/ENGINEERING_GRAPH.md` roadmap/state.

## Phase 6 — Unit/integration validation

- [ ] T049 Test tracked-file filtering and excluded/untracked data.
- [ ] T050 Test deterministic chunking/IDs/hashes.
- [ ] T051 Test hashing-provider reproducibility.
- [ ] T052 Test HTTP provider validation using a local/stubbed transport boundary.
- [ ] T053 Test index roundtrip/atomic persistence.
- [ ] T054 Test semantic index reproducibility.
- [ ] T055 Test stale revision rejection.
- [ ] T056 Test provider/model/config mismatch rejection.
- [ ] T057 Test cosine ranking and deterministic tie breaks.
- [ ] T058 Test graph anchor resolution.
- [ ] T059 Test bounded graph expansion/truncation.
- [ ] T060 Test architecture discovery mode.
- [ ] T061 Test CLI build/query/validate/status surfaces.
- [ ] T062 Re-run full existing Engineering Graph unit suite.

## Phase 7 — CI/convergence

- [ ] T063 Add V4 offline GraphRAG build smoke to Engineering Graph CI.
- [ ] T064 Build the same index twice and assert semantic reproducibility.
- [ ] T065 Assert strict freshness on the CI index.
- [ ] T066 Assert controlled ranked retrieval from repository fixtures/content.
- [ ] T067 Assert Neo4j seed resolution and bounded expansion.
- [ ] T068 Assert GraphRAG did not introduce new canonical node/relationship vocabulary.
- [ ] T069 Preserve application runtime dependency isolation gate.
- [ ] T070 Run Spec Kit validation on final HEAD.
- [ ] T071 Run Engineering Graph workflow on final HEAD.
- [ ] T072 Run Product CI on final HEAD.
- [ ] T073 Create `analysis.md` mapping FR/SC to implementation evidence.
- [ ] T074 Create `convergence.md` with final authority/freshness validation.
- [ ] T075 Reconcile all task statuses against actual implementation evidence.
- [ ] T076 Freeze V4 only after Spec Kit + Engineering Graph + Product CI are green on the same final HEAD.
