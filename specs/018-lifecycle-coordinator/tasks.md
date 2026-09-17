# Tasks: Lifecycle Coordinator V10

## Phase 1 — Specification and authority

- [x] T001 Create `SPEC-018-LIFECYCLE-COORDINATOR` before implementation.
- [x] T002 Record post-V9 boundary research.
- [x] T003 Add implementation plan.
- [x] T004 Add lifecycle evidence/assessment contract.
- [x] T005 Add quickstart.
- [x] T006 Add requirements checklist.
- [x] T007 Add ADR-0026 for lifecycle projection authority.

## Phase 2 — Lifecycle core

- [x] T008 Define versioned phase, blocker and next-action vocabulary.
- [x] T009 Define immutable lifecycle evidence input.
- [x] T010 Define versioned lifecycle assessment output.
- [x] T011 Validate repository/Spec/Task identity across evidence.
- [x] T012 Validate branch/worktree/run/publication identity when present.
- [x] T013 Preserve canonical-vs-derived evidence classification.
- [x] T014 Classify unallocated/allocated/running/executed phases.
- [x] T015 Classify validated/published/awaiting-human phases.
- [x] T016 Classify merged/reconciled/finalized phases without inferring canonical completion.
- [x] T017 Fail closed to blocked on contradictory identity/evidence.
- [x] T018 Select exactly one next action from closed vocabulary.

## Phase 3 — Human Async Gates / continuation

- [x] T019 Parse and validate Human Async Gate evidence without mutation.
- [x] T020 Make required PENDING gate block readiness.
- [x] T021 Make FAILED gate route to remediation/retest.
- [x] T022 Reject stale gate evidence as current proof.
- [x] T023 Accept only externally recorded fresh PASSED/WAIVED evidence.
- [x] T024 Generate structured continuation payload.
- [x] T025 Include freshness instruction and authority boundary in continuation output.

## Phase 4 — Read-only adapters / CLI

- [x] T026 Add read-only local evidence adapter for V3–V9 files/registries.
- [x] T027 Add `lifecycle_cli.py`.
- [x] T028 Add `lifecycle-status` JSON output.
- [x] T029 Add concise human output.
- [x] T030 Route V10 through `runner_entry.py` without changing V1–V9 command behavior.
- [x] T031 Ensure lifecycle status creates/modifies no Git/runtime/Neo4j state.

## Phase 5 — Tests

- [x] T032 Test schema and closed vocabularies.
- [x] T033 Test each lifecycle phase and next action.
- [x] T034 Test runner success does not imply validation/publication/merge/completion.
- [x] T035 Test validation/publication/merge evidence does not skip authority tiers.
- [x] T036 Test cross-artifact identity conflict fail-closed behavior.
- [x] T037 Test pending/failed/stale/fresh Human Async Gates.
- [x] T038 Test continuation payload contract.
- [x] T039 Test CLI routing/JSON/human output and read-only behavior.
- [ ] T040 Re-run complete V1–V9 Engineering Graph regression suite together with V10 tests.

## Phase 6 — Documentation / convergence

- [x] T041 Add V10 architecture documentation.
- [x] T042 Update Engineering Graph README/agent instructions for V10 status usage.
- [x] T043 Create `analysis.md` mapping FR/SC to evidence.
- [x] T044 Create `convergence.md` with authority and gate evidence.
- [x] T045 Reconcile task ledger against implementation evidence.
- [ ] T046 Run Spec Kit on closeout candidate.
- [ ] T047 Run Engineering Graph on closeout candidate.
- [ ] T048 Run Product CI on closeout candidate.
- [x] T049 Classify Human Async Gates for Spec 018: NONE; deterministic read-only behavior is fully automatable, and no separate human/manual acceptance observation is required by the spec.
- [ ] T050 Declare freeze only after all three automated gates are green on one final HEAD and no required Human Async Gate is PENDING.