# Tasks: Post-Publication Lifecycle V9

## Phase 1 — Specification and authority

- [x] T001 Create `SPEC-017-POST-PUBLICATION-LIFECYCLE`.
- [x] T002 Record V9 research and authority boundaries.
- [x] T003 Add implementation plan.
- [x] T004 Define lifecycle receipt / human-gate / continuation-prompt model.
- [x] T005 Add quickstart.
- [ ] T006 Add requirements checklist.
- [ ] T007 Add ADR-0025 for post-publication + human-gate authority.

## Phase 2 — Project memory / human gates

- [ ] T008 Add `docs/ai/human-async-gates.md`.
- [ ] T009 Require Continuation Prompt in ChatGPT Project Instructions.
- [ ] T010 Require Human Async Gate handling in ChatGPT Project Instructions.
- [ ] T011 Update context handoff policy with gate-aware continuation prompts.
- [ ] T012 Update session handoff template with Human Async Gates and Continuation Prompt sections.
- [ ] T013 Update `AGENTS.md` with the same operational contract.

## Phase 3 — Lifecycle core

- [ ] T014 Add versioned `PostPublicationReceipt` contract.
- [ ] T015 Add atomic receipt persistence below `.execution/post-publication/`.
- [ ] T016 Load/validate V8 publication record and matching active V3 lease.
- [ ] T017 Add safe GitHub PR inspection through `gh` argv + `shell=False`.
- [ ] T018 Require merged PR evidence and merge commit SHA.
- [ ] T019 Refresh configured base branch without mutating allocation worktree.
- [ ] T020 Verify merge commit is reachable from refreshed base.
- [ ] T021 Resolve canonical Spec Kit Task path from Spec ID.
- [ ] T022 Read canonical `tasks.md` from base revision.
- [ ] T023 Require one unambiguous checked Task entry.
- [ ] T024 Produce read-only reconciliation result with blocking reasons.
- [ ] T025 Add explicit finalize operation.
- [ ] T026 Release only the matching active lease when requested.
- [ ] T027 Optionally remove only the matching clean worktree when requested.
- [ ] T028 Make repeated finalization idempotent.

## Phase 4 — CLI

- [ ] T029 Add `post_publication_cli.py`.
- [ ] T030 Add `post-publication-status`.
- [ ] T031 Add `post-publication-finalize`.
- [ ] T032 Add JSON/human rendering.
- [ ] T033 Route V9 commands through `runner_entry.py` without changing legacy command behavior.

## Phase 5 — Tests

- [ ] T034 Test receipt roundtrip / malformed payload fail-closed.
- [ ] T035 Test open PR blocks cleanup.
- [ ] T036 Test merged PR without base reachability blocks cleanup.
- [ ] T037 Test incomplete/ambiguous canonical Task blocks cleanup.
- [ ] T038 Test merged + reachable + canonical-complete reconciliation.
- [ ] T039 Test explicit lease release.
- [ ] T040 Test clean worktree removal.
- [ ] T041 Test dirty worktree removal refusal.
- [ ] T042 Test repeated finalize idempotency.
- [ ] T043 Test unrelated lease/worktree preservation.
- [ ] T044 Test CLI routing / JSON output.
- [ ] T045 Re-run complete V1–V8 Engineering Graph regression suite.

## Phase 6 — Documentation / convergence

- [ ] T046 Add V9 architecture documentation.
- [ ] T047 Update Engineering Graph development guide/README.
- [ ] T048 Create `analysis.md` mapping FR/SC to evidence.
- [ ] T049 Create `convergence.md` with authority and gate evidence.
- [ ] T050 Reconcile task ledger against implementation evidence.
- [ ] T051 Run Spec Kit on final HEAD.
- [ ] T052 Run Engineering Graph workflow on final HEAD.
- [ ] T053 Run Product CI on final HEAD.
- [ ] T054 Freeze only when all three gates are green on the same HEAD and all required Human Async Gates are non-PENDING.
