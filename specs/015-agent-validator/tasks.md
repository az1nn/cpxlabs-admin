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
- [x] T004 Add research, data model, quickstart and requirements checklist artifacts.

## Phase 2 — Model/persistence

- [x] T010 Add versioned validation record/command-result models and invariants.
- [x] T011 Add atomic persistence under `.execution/validation/records/`.
- [x] T012 Add latest/all validation record inspection.

## Phase 3 — Preconditions and ownership

- [x] T020 Require one active matching V3 allocation and registered worktree/branch.
- [x] T021 Reconcile and require latest V5 run to be `succeeded` with matching allocation identity.
- [x] T022 When V6 owns the task, require exact latest supervisor `runId` ownership and `succeeded` observation.
- [x] T023 Reject missing/empty frozen validation command sets.

## Phase 4 — Validation execution

- [x] T024 Tokenize all frozen commands with `shlex.split` before execution.
- [x] T025 Execute sequentially with `shell=False` in allocation worktree.
- [x] T026 Capture bounded metadata plus stdout/stderr file paths per command.
- [x] T027 Stop on first non-zero exit and persist overall `failed`; persist `passed` only when all commands pass.
- [x] T028 Bind evidence to pre/post workspace fingerprint and fail overall validation on workspace mutation.

## Phase 5 — CLI/docs

- [x] T030 Add `validation-run <TASK-ID>` and `validation-status` local CLI commands.
- [x] T031 Route validator commands through the composed entrypoint without changing legacy command semantics.
- [x] T032 Add `docs/architecture/AGENT_VALIDATOR.md` and operator workflow.
- [x] T033 Add scoped `engineering-graph/AGENTS.md` with V7 boundaries/commands.

## Phase 6 — Validation/convergence

- [x] T040 Test success and first-failure stop behavior.
- [x] T041 Test CLI parser/routing and absence of arbitrary command override.
- [x] T042 Test allocation/worktree/latest-run preconditions.
- [x] T043 Test V6 exact-run ownership mismatch fail-closed behavior.
- [x] T044 Test workspace mutation, disposable state and no lease/canonical/Git mutation.
- [x] T045 Re-run full V1–V6 Engineering Graph suite on implementation candidate.
- [x] T046 Run Spec Kit validation on implementation candidate HEAD.
- [x] T047 Run Engineering Graph workflow on implementation candidate HEAD.
- [x] T048 Run Product CI on implementation candidate HEAD.
- [x] T049 Create analysis/convergence evidence and declare the resulting commit the V7 freeze candidate; PR readiness still requires Spec Kit + Engineering Graph + Product CI green on that exact final HEAD with no subsequent content changes.
