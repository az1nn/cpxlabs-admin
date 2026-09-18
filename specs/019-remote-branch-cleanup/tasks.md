# Tasks: Remote Branch Cleanup V11

**Input**: Design documents from `specs/019-remote-branch-cleanup/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/remote-cleanup.md`

**Tests**: Required. This feature adds destructive Git authority and must be developed with explicit unit/integration regression coverage.

## Phase 1 — Setup and authority boundary

- [x] T001 Add ADR-0027 at `docs/adr/0027-remote-branch-cleanup-authority-boundary.md`
- [x] T002 Add V11 architecture document at `docs/architecture/REMOTE_BRANCH_CLEANUP.md`
- [x] T003 Update `engineering-graph/AGENTS.md` with V11 authority/non-authority rules (depends: T001)
- [x] T004 Update `engineering-graph/README.md` with V11 CLI/operator positioning (depends: T002)

## Phase 2 — Foundational contracts

- [ ] T005 Define versioned V11 assessment/receipt contracts in `engineering-graph/src/engineering_graph/remote_cleanup.py`
- [ ] T006 Define closed blocker/state/next-action vocabularies in `engineering-graph/src/engineering_graph/remote_cleanup.py`
- [ ] T007 Implement strict cross-artifact identity validation for V8 publication + finalized V9 receipt in `engineering-graph/src/engineering_graph/remote_cleanup.py` (depends: T005)
- [ ] T008 Implement target/base/default branch safety validation in `engineering-graph/src/engineering_graph/remote_cleanup.py` (depends: T005)
- [ ] T009 Implement matching active-lease/worktree safety checks in `engineering-graph/src/engineering_graph/remote_cleanup.py` (depends: T005)
- [ ] T010 Implement exact-ref remote inspection with argv-only `shell=False` execution in `engineering-graph/src/engineering_graph/remote_cleanup.py` (depends: T005)
- [ ] T011 Implement read-only assessment reducer in `engineering-graph/src/engineering_graph/remote_cleanup.py` (depends: T007,T008,T009,T010)

## Phase 3 — User Story 1: Assess remote cleanup readiness (P1)

**Goal**: Provide a deterministic read-only answer before any remote mutation.

**Independent Test**: Status distinguishes ready, absent, identity conflict, unsafe local ownership, default/base branch and remote-unavailable states without writing receipts or refs.

- [ ] T012 [P] [US1] Add contract/invariant tests for V11 models/vocabularies in `engineering-graph/tests/test_remote_cleanup.py`
- [ ] T013 [P] [US1] Add exact-ref/no-shell inspection tests in `engineering-graph/tests/test_remote_cleanup.py`
- [ ] T014 [P] [US1] Add read-only mutation-sentinel tests for status in `engineering-graph/tests/test_remote_cleanup.py`
- [ ] T015 [US1] Implement `remote-cleanup-status` service path in `engineering-graph/src/engineering_graph/remote_cleanup.py` (depends: T011,T012,T013,T014)
- [ ] T016 [US1] Add status CLI parser/rendering in `engineering-graph/src/engineering_graph/remote_cleanup_cli.py` (depends: T015)
- [ ] T017 [US1] Add JSON/human CLI tests in `engineering-graph/tests/test_remote_cleanup_cli.py` (depends: T016)

## Phase 4 — User Story 2: Guarded exact remote deletion (P2)

**Goal**: Delete only the publication-owned remote head when its current SHA still equals the expected publication SHA.

**Independent Test**: A disposable bare remote proves exact deletion, expected-SHA race rejection and preservation of unrelated refs.

- [ ] T018 [P] [US2] Add real disposable-remote success/isolation test in `engineering-graph/tests/test_remote_cleanup.py`
- [ ] T019 [P] [US2] Add remote-SHA race/recreation rejection test in `engineering-graph/tests/test_remote_cleanup.py`
- [ ] T020 [P] [US2] Add no-explicit-intent/no-mutation test in `engineering-graph/tests/test_remote_cleanup_cli.py`
- [ ] T021 [US2] Implement expected-SHA guarded delete primitive in `engineering-graph/src/engineering_graph/remote_cleanup.py` (depends: T010,T018,T019)
- [ ] T022 [US2] Implement versioned receipt persistence/idempotent load in `engineering-graph/src/engineering_graph/remote_cleanup.py` (depends: T005)
- [ ] T023 [US2] Implement finalize orchestration with mandatory explicit intent and fresh re-assessment in `engineering-graph/src/engineering_graph/remote_cleanup.py` (depends: T021,T022)
- [ ] T024 [US2] Add `remote-cleanup-finalize` CLI in `engineering-graph/src/engineering_graph/remote_cleanup_cli.py` (depends: T023)
- [ ] T025 [US2] Add finalize/retry/error CLI coverage in `engineering-graph/tests/test_remote_cleanup_cli.py` (depends: T024)

## Phase 5 — User Story 3: Lifecycle and continuation integration (P3)

**Goal**: Make pending/completed V11 cleanup visible without changing canonical Task truth.

**Independent Test**: Lifecycle output reflects V11 derived evidence with a versioned contract and remains read-only/backward-compatible.

- [ ] T026 [P] [US3] Define lifecycle compatibility cases for pre-V11 and V11 evidence in `engineering-graph/tests/test_lifecycle.py`
- [ ] T027 [US3] Extend lifecycle evidence/assessment versioning in `engineering-graph/src/engineering_graph/lifecycle.py` only as required by Spec 019 (depends: T026)
- [ ] T028 [US3] Extend lifecycle CLI rendering/continuation payload in `engineering-graph/src/engineering_graph/lifecycle_cli.py` (depends: T027)
- [ ] T029 [US3] Add lifecycle CLI compatibility/read-only regression tests in `engineering-graph/tests/test_lifecycle_cli.py` (depends: T028)
- [ ] T030 [US3] Register V11 commands in `engineering-graph/src/engineering_graph/runner_entry.py` without changing V1–V10 command behavior (depends: T016,T024)

## Phase 6 — Regression and convergence

- [ ] T031 Run targeted V11 unit/integration tests for status, guarded deletion, race protection and idempotency
- [ ] T032 Run complete V1–V10 Engineering Graph regression suite with V11 tests
- [ ] T033 Run `quickstart.md` scenarios against a disposable Git remote
- [ ] T034 Create `specs/019-remote-branch-cleanup/analysis.md` mapping FR/SC requirements to implementation/test evidence
- [ ] T035 Create `specs/019-remote-branch-cleanup/convergence.md` with authority, compatibility and gate evidence
- [ ] T036 Reconcile this task ledger against implementation evidence
- [ ] T037 Run Spec Kit on the closeout candidate
- [ ] T038 Run Engineering Graph on the exact same closeout candidate
- [ ] T039 Run Product CI on the exact same closeout candidate
- [ ] T040 Classify Human Async Gates for Spec 019 and record any required gate explicitly
- [ ] T041 Declare final freeze only after T037–T040 are satisfied on one exact HEAD with no content mutation afterward

## Dependencies & Execution Order

- Phase 1 establishes the durable authority boundary.
- Phase 2 blocks all user-story implementation.
- US1 must complete before US2 because destructive mutation depends on the read-only readiness contract.
- US3 depends on stable V11 status/finalize contracts but does not authorize mutation.
- Convergence begins only after all desired user stories and regression work are complete.

## Parallel Opportunities

- T012–T014 can be developed independently against the Phase 2 contract.
- T018–T020 cover distinct destructive-safety scenarios.
- T026 can proceed once the V11 evidence contract is stable.
- Documentation updates that touch different files may run in parallel after ADR-0027 establishes the boundary.

## Implementation Strategy

1. Land the read-only assessment and prove zero mutation.
2. Add guarded exact-ref deletion with real Git race tests.
3. Add derived receipt/idempotency.
4. Integrate V11 evidence into lifecycle/continuation only after mutation semantics are stable.
5. Freeze only on same-HEAD Spec Kit + Engineering Graph + Product CI evidence.
