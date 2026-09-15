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

- [x] T010 Add publication schema/version/status constants and errors.
- [x] T011 Add atomic publication-record persistence under `.execution/publication/records/`.
- [x] T012 Validate active V3 allocation + exact passed V7 validation identity.
- [x] T013 Reject stale current workspace revision/fingerprint before mutation.
- [x] T014 Reject duplicate successful publication for one validation id.

## Phase 3 — Git commit/push

- [x] T020 Validate `origin` repository identity and allocation branch.
- [x] T021 Stage the exact current validated workspace with argv Git execution.
- [x] T022 Reject empty staged publication.
- [x] T023 Commit once and persist the exact commit SHA.
- [x] T024 Verify commit parent/worktree cleanliness.
- [x] T025 Push allocation branch to origin without force and persist pushed state.

## Phase 4 — Pull request and recovery

- [x] T030 Open GitHub PR with explicit base/head/title/body using `gh` argv.
- [x] T031 Persist PR URL and `pr_opened` terminal publication state.
- [x] T032 Add failure phase/error persistence.
- [x] T033 Add resume from commit/push/PR partial states without duplicate commit.
- [x] T034 Refuse resume when recorded commit/branch/worktree identity drifted.

## Phase 5 — CLI/docs

- [x] T040 Add `publication-run` command.
- [x] T041 Add `publication-resume` command.
- [x] T042 Add `publication-status` command.
- [x] T043 Route V8 commands through local composed entrypoint.
- [x] T044 Add `docs/architecture/GIT_PUBLISHER.md`.
- [x] T045 Update scoped Engineering Graph agent instructions.

## Phase 6 — Validation/convergence

- [x] T050 Test record/evidence/remote/branch invariants.
- [x] T051 Test CLI parser/routing.
- [x] T052 Test no-shell/no-force command construction.
- [x] T053 Test commit -> push -> PR state transitions.
- [x] T054 Test stale workspace rejection before mutation.
- [x] T055 Test resume does not create duplicate commit.
- [x] T056 Re-run full V1–V7 Engineering Graph suite.
- [x] T057 Run Spec Kit validation on implementation candidate HEAD.
- [x] T058 Run Engineering Graph workflow on implementation candidate HEAD.
- [x] T059 Run Product CI on implementation candidate HEAD.
- [x] T060 Create analysis/convergence evidence and declare final V8 freeze candidate.
