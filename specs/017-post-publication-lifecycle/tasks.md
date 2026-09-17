# Tasks: Post-Publication Lifecycle V9

## Phase 1 — Specification and authority

- [x] T001 Create `SPEC-017-POST-PUBLICATION-LIFECYCLE`.
- [x] T002 Record V9 research and authority boundaries.
- [x] T003 Add implementation plan.
- [x] T004 Define lifecycle receipt / human-gate / continuation-prompt model.
- [x] T005 Add quickstart.
- [x] T006 Add requirements checklist.
- [x] T007 Add ADR-0025 for post-publication + human-gate authority.

## Phase 2 — Project memory / human gates

- [x] T008 Add `docs/ai/human-async-gates.md`.
- [x] T009 Require Continuation Prompt in ChatGPT Project Instructions.
- [x] T010 Require Human Async Gate handling in ChatGPT Project Instructions.
- [x] T011 Update context handoff policy with gate-aware continuation prompts.
- [x] T012 Update session handoff template with Human Async Gates and Continuation Prompt sections.
- [x] T013 Update Engineering Graph agent instructions with the same operational contract.

## Phase 3 — Lifecycle core

- [x] T014 Add versioned `PostPublicationReceipt` contract.
- [x] T015 Add atomic receipt persistence below `.execution/post-publication/`.
- [x] T016 Load/validate V8 publication record and matching active V3 lease.
- [x] T017 Add safe GitHub PR inspection through `gh` argv + `shell=False`.
- [x] T018 Require merged PR evidence and merge commit SHA.
- [x] T019 Refresh configured base branch without mutating allocation worktree.
- [x] T020 Verify merge commit is reachable from refreshed base.
- [x] T021 Resolve canonical Spec Kit Task path from Spec ID.
- [x] T022 Read canonical `tasks.md` from base revision.
- [x] T023 Require one unambiguous checked Task entry.
- [x] T024 Produce read-only reconciliation result with blocking reasons.
- [x] T025 Add explicit finalize operation.
- [x] T026 Release only the matching active lease when requested.
- [x] T027 Optionally remove only the matching clean worktree when requested.
- [x] T028 Make repeated/partial finalization idempotent, including retry after lease release.

## Phase 4 — CLI

- [x] T029 Add `post_publication_cli.py`.
- [x] T030 Add `post-publication-status`.
- [x] T031 Add `post-publication-finalize`.
- [x] T032 Add JSON/human rendering.
- [x] T033 Route V9 commands through `runner_entry.py` without changing legacy command behavior.

## Phase 5 — Tests

- [x] T034 Test receipt roundtrip / malformed payload fail-closed.
- [x] T035 Test open PR blocks cleanup.
- [x] T036 Test merged PR without base reachability blocks cleanup.
- [x] T037 Test incomplete/ambiguous canonical Task blocks cleanup.
- [x] T038 Test merged + reachable + canonical-complete reconciliation.
- [x] T039 Test explicit lease release.
- [x] T040 Test clean worktree removal.
- [x] T041 Test dirty worktree removal refusal.
- [x] T042 Test repeated/partial finalize idempotency.
- [x] T043 Test cleanup targets only the publication Task/worktree and preserves unrelated allocations by construction.
- [x] T044 Test CLI routing / JSON surfaces.
- [x] T045 Re-run complete V1–V8 Engineering Graph regression suite together with V9 tests.

## Phase 6 — Documentation / convergence

- [x] T046 Add V9 architecture documentation.
- [x] T047 Update Engineering Graph README through V9 and add operator/agent policy docs.
- [x] T048 Create `analysis.md` mapping FR/SC to evidence.
- [x] T049 Create `convergence.md` with authority and gate evidence.
- [x] T050 Reconcile task ledger against implementation evidence.
- [x] T051 Run Spec Kit on the closeout candidate: #432 passed.
- [x] T052 Run Engineering Graph on the closeout candidate: #385 passed.
- [x] T053 Run Product CI on the closeout candidate: #797 passed, including Storybook/a11y and Playwright E2E.
- [x] T054 Declare V9 freeze candidate after the three closeout gates are green and no required Human Async Gate is PENDING; repeat all three workflows on this exact ledger/freeze HEAD before PR readiness.
