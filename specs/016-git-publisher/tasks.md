---
graph:
  task_links:
    T010:
      implements:
        - engineering-graph/src/engineering_graph/publisher.py
    T020:
      implements:
        - engineering-graph/src/engineering_graph/publisher.py
    T030:
      implements:
        - engineering-graph/src/engineering_graph/publisher.py
    T040:
      implements:
        - engineering-graph/src/engineering_graph/publisher_cli.py
        - engineering-graph/src/engineering_graph/runner_entry.py
    T050:
      validated_by:
        - engineering-graph/tests/test_publisher.py
    T051:
      validated_by:
        - engineering-graph/tests/test_publisher_cli.py
---
# Tasks: Git Publisher V8

## Phase 1 — Spec/architecture

- [x] T001 Create `SPEC-016-GIT-PUBLISHER` feature specification.
- [x] T002 Record publication/recovery research.
- [x] T003 Define V8 implementation plan.
- [x] T004 Define publication record/state model.
- [x] T005 Add requirements checklist and quickstart.
- [x] T006 Add ADR-0024 for Git publication authority boundary.

## Phase 2 — Evidence and persistence

- [ ] T010 Add publication schema/version/status constants and errors.
- [ ] T011 Add atomic publication-record persistence under `.execution/publication/records/`.
- [ ] T012 Validate active V3 allocation + exact passed V7 validation identity.
- [ ] T013 Reject stale current workspace revision/fingerprint before mutation.
- [ ] T014 Reject duplicate successful publication for one validation id.

## Phase 3 — Git commit/push

- [ ] T020 Validate `origin` repository identity and allocation branch.
- [ ] T021 Stage the exact current validated workspace with argv Git execution.
- [ ] T022 Reject empty staged publication.
- [ ] T023 Commit once and persist the exact commit SHA.
- [ ] T024 Verify commit parent/worktree cleanliness.
- [ ] T025 Push allocation branch to origin without force and persist pushed state.

## Phase 4 — Pull request and recovery

- [ ] T030 Open GitHub PR with explicit base/head/title/body using `gh` argv.
- [ ] T031 Persist PR URL and `pr_opened` terminal publication state.
- [ ] T032 Add failure phase/error persistence.
- [ ] T033 Add resume from commit/push/PR partial states without duplicate commit.
- [ ] T034 Refuse resume when recorded commit/branch/worktree identity drifted.

## Phase 5 — CLI/docs

- [ ] T040 Add `publication-run` command.
- [ ] T041 Add `publication-resume` command.
- [ ] T042 Add `publication-status` command.
- [ ] T043 Route V8 commands through local composed entrypoint.
- [ ] T044 Add `docs/architecture/GIT_PUBLISHER.md`.
- [ ] T045 Update scoped Engineering Graph agent instructions.

## Phase 6 — Validation/convergence

- [ ] T050 Test record/evidence/remote/branch invariants.
- [ ] T051 Test CLI parser/routing.
- [ ] T052 Test no-shell/no-force command construction.
- [ ] T053 Test commit -> push -> PR state transitions.
- [ ] T054 Test stale workspace rejection before mutation.
- [ ] T055 Test resume does not create duplicate commit.
- [ ] T056 Re-run full V1–V7 Engineering Graph suite.
- [ ] T057 Run Spec Kit validation on implementation candidate HEAD.
- [ ] T058 Run Engineering Graph workflow on implementation candidate HEAD.
- [ ] T059 Run Product CI on implementation candidate HEAD.
- [ ] T060 Create analysis/convergence evidence and declare final V8 freeze candidate.
