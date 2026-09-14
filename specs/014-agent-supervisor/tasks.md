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

- [ ] T010 Add supervisor schema/version constants and errors.
- [ ] T011 Add `SupervisorTask` model/validation.
- [ ] T012 Add `SupervisorJob` model/validation.
- [ ] T013 Add atomic job persistence under `.execution/supervisor/jobs/`.
- [ ] T014 Add job listing/loading and overlapping active-task ownership checks.

## Phase 3 — Manifest/allocation safety

- [ ] T020 Validate manifest repository/revision/cycles and selected wave.
- [ ] T021 Require active matching V3 allocation for every wave task.
- [ ] T022 Persist ordered manifest-wave task identity and supervisor policy.

## Phase 4 — Tick/retry/stop lifecycle

- [ ] T023 Reconcile job-owned V5 run ids against the runner registry.
- [ ] T024 Add deterministic `maxParallel` slot calculation.
- [ ] T025 Launch pending tasks in manifest-wave order.
- [ ] T026 Retry failed/orphaned tasks only while attempts remain.
- [ ] T027 Never automatically retry explicit stopped runs.
- [ ] T028 Set `settled` only after every task reaches a supervisor terminal state.
- [ ] T029 Add fail-closed supervisor stop using job-owned latest run ids.

## Phase 5 — CLI/docs

- [ ] T030 Add supervisor CLI module and composed entrypoint routing.
- [ ] T031 Add `supervisor-start`.
- [ ] T032 Add `supervisor-tick`.
- [ ] T033 Add `supervisor-status`.
- [ ] T034 Add `supervisor-stop`.
- [ ] T035 Support JSON/human output and literal child argv remainder.
- [ ] T036 Add `docs/architecture/AGENT_SUPERVISOR.md`.
- [ ] T037 Update Engineering Graph documentation surfaces.

## Phase 6 — Validation/convergence

- [ ] T040 Test model/persistence/overlap invariants.
- [ ] T041 Test CLI parser/routing.
- [ ] T042 Test bounded concurrency and deterministic launch ordering.
- [ ] T043 Test bounded failed/orphaned retries.
- [ ] T044 Test stopped-run no-retry behavior.
- [ ] T045 Test job-owned fail-closed stop semantics.
- [ ] T046 Re-run full V1–V5 Engineering Graph suite.
- [ ] T047 Run Spec Kit validation on freeze candidate HEAD.
- [ ] T048 Run Engineering Graph workflow on freeze candidate HEAD.
- [ ] T049 Run Product CI on freeze candidate HEAD.
- [ ] T050 Create analysis/convergence evidence and freeze V6 only when all three domains are green on one HEAD.
