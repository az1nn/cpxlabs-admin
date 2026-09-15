---
graph:
  task_links:
    T010:
      implements:
        - engineering-graph/src/engineering_graph/validation.py
    T020:
      implements:
        - engineering-graph/src/engineering_graph/validation.py
    T030:
      implements:
        - engineering-graph/src/engineering_graph/validation_cli.py
        - engineering-graph/src/engineering_graph/runner_entry.py
    T040:
      validated_by:
        - engineering-graph/tests/test_validation.py
    T041:
      validated_by:
        - engineering-graph/tests/test_validation_cli.py
---
# Tasks: Agent Validator V7

## Phase 1 — Spec/architecture

- [x] T001 Create `SPEC-015-AGENT-VALIDATOR` feature specification.
- [x] T002 Define V7 implementation plan and least-authority split from future publication.
- [x] T003 Add ADR-0023 for validation authority and command provenance.

## Phase 2 — Model/persistence

- [ ] T010 Add versioned validation record/command-result models and invariants.
- [ ] T011 Add atomic persistence under `.execution/validation/records/`.
- [ ] T012 Add latest/all validation record inspection.

## Phase 3 — Preconditions and ownership

- [ ] T020 Require one active matching V3 allocation and registered worktree/branch.
- [ ] T021 Reconcile and require latest V5 run to be `succeeded` with matching allocation identity.
- [ ] T022 When V6 owns the task, require exact latest supervisor `runId` ownership and `succeeded` observation.
- [ ] T023 Reject missing/empty frozen validation command sets.

## Phase 4 — Validation execution

- [ ] T024 Tokenize frozen commands with `shlex.split` only.
- [ ] T025 Execute sequentially with `shell=False` in allocation worktree.
- [ ] T026 Capture bounded metadata plus stdout/stderr file paths per command.
- [ ] T027 Stop on first non-zero exit and persist overall `failed`; persist `passed` only when all commands pass.

## Phase 5 — CLI/docs

- [ ] T030 Add `validation-run <TASK-ID>` and `validation-status` local CLI commands.
- [ ] T031 Route validator commands through the composed entrypoint without changing legacy command semantics.
- [ ] T032 Add `docs/architecture/AGENT_VALIDATOR.md` and operator workflow.
- [ ] T033 Update `AGENTS.md` with V7 boundaries/commands.

## Phase 6 — Validation/convergence

- [ ] T040 Test success and first-failure stop behavior.
- [ ] T041 Test CLI parser/routing and absence of arbitrary command override.
- [ ] T042 Test stale/allocation/worktree/latest-run preconditions.
- [ ] T043 Test V6 exact-run ownership mismatch fail-closed behavior.
- [ ] T044 Test disposable state and no lease/canonical/Git mutation.
- [ ] T045 Re-run full V1–V6 Engineering Graph suite.
- [ ] T046 Run Spec Kit validation on implementation candidate HEAD.
- [ ] T047 Run Engineering Graph workflow on implementation candidate HEAD.
- [ ] T048 Run Product CI on implementation candidate HEAD.
- [ ] T049 Create analysis/convergence evidence and freeze only after all three gates pass on the exact final HEAD.
