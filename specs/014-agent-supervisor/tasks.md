---
graph:
  task_links:
    T010:
      implements:
        - engineering-graph/src/engineering_graph/supervisor.py
    T020:
      implements:
        - engineering-graph/src/engineering_graph/supervisor.py
    T030:
      implements:
        - engineering-graph/src/engineering_graph/supervisor_cli.py
        - engineering-graph/src/engineering_graph/runner_entry.py
    T040:
      validated_by:
        - engineering-graph/tests/test_supervisor.py
    T041:
      validated_by:
        - engineering-graph/tests/test_supervisor_cli.py
---
# Tasks: Agent Supervisor V6

## Phase 1 — Spec/architecture

- [x] T001 Create `SPEC-014-AGENT-SUPERVISOR` feature specification.
- [x] T002 Record supervisor/retry/authority research.
- [x] T003 Define V6 implementation plan.
- [x] T004 Define supervisor job/task data model.
- [x] T005 Add requirements checklist and quickstart.
- [x] T006 Add ADR-0022 for supervisor authority boundary.

## Phase 2 — Model/persistence

- [x] T010 Add supervisor schema/version constants and errors.
- [x] T011 Add `SupervisorTask` model/validation.
- [x] T012 Add `SupervisorJob` model/validation.
- [x] T013 Add atomic job persistence under `.execution/supervisor/jobs/`.
- [x] T014 Add job listing/loading and overlapping active-task ownership checks.

## Phase 3 — Manifest/allocation safety

- [x] T020 Validate manifest repository/revision/cycles and selected wave.
- [x] T021 Require active matching V3 allocation for every wave task.
- [x] T022 Persist ordered manifest-wave task identity and supervisor policy.

## Phase 4 — Tick/retry/stop lifecycle

- [x] T023 Reconcile job-owned V5 run ids against the runner registry.
- [x] T024 Add deterministic `maxParallel` slot calculation.
- [x] T025 Launch pending tasks in manifest-wave order.
- [x] T026 Retry failed/orphaned tasks only while attempts remain.
- [x] T027 Never automatically retry explicit stopped runs.
- [x] T028 Set `settled` only after every task reaches a supervisor terminal state.
- [x] T029 Add fail-closed supervisor stop using job-owned latest run ids.

## Phase 5 — CLI/docs

- [x] T030 Add supervisor CLI module and composed entrypoint routing.
- [x] T031 Add `supervisor-start`.
- [x] T032 Add `supervisor-tick`.
- [x] T033 Add `supervisor-status`.
- [x] T034 Add `supervisor-stop`.
- [x] T035 Support JSON/human output and literal child argv remainder.
- [x] T036 Add `docs/architecture/AGENT_SUPERVISOR.md`.
- [x] T037 Document operator workflow and authority boundary in Spec Kit quickstart + architecture docs.

## Phase 6 — Validation/convergence

- [x] T040 Test model/persistence/overlap invariants.
- [x] T041 Test CLI parser/routing.
- [x] T042 Test bounded concurrency, idempotent occupied ticks and deterministic launch ordering.
- [x] T043 Test bounded failed/orphaned retries.
- [x] T044 Test stopped-run no-retry behavior.
- [x] T045 Test job-owned fail-closed stop semantics.
- [x] T046 Re-run full V1–V5 Engineering Graph suite.
- [x] T047 Run Spec Kit validation on implementation candidate HEAD.
- [x] T048 Run Engineering Graph workflow on implementation candidate HEAD.
- [x] T049 Run Product CI on implementation candidate HEAD.
- [x] T050 Create analysis/convergence evidence and declare the resulting commit the V6 freeze candidate; PR readiness still requires Spec Kit + Engineering Graph + Product CI green on that exact final HEAD with no subsequent changes.
