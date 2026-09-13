---
graph:
  task_links:
    T020:
      implements:
        - engineering-graph/src/engineering_graph/runner.py
    T021:
      implements:
        - engineering-graph/src/engineering_graph/runner.py
    T025:
      implements:
        - engineering-graph/src/engineering_graph/runner_child.py
    T040:
      implements:
        - engineering-graph/src/engineering_graph/runner_cli.py
    T041:
      implements:
        - engineering-graph/src/engineering_graph/runner_entry.py
        - engineering-graph/pyproject.toml
    T056:
      validated_by:
        - engineering-graph/tests/test_runner.py
    T057:
      validated_by:
        - engineering-graph/tests/test_runner.py
    T062:
      validated_by:
        - engineering-graph/tests/test_runner_force_cli.py
---
# Tasks: Agent Runner V5

## Phase 1 — Spec/architecture

- [x] T001 Create `SPEC-013-AGENT-RUNNER` feature specification.
- [x] T002 Record process-lifecycle research and safety boundary.
- [x] T003 Define V5 implementation plan.
- [x] T004 Define run/registry/result data model.
- [x] T005 Add requirements checklist.
- [x] T006 Add quickstart/lifecycle documentation.
- [x] T007 Add ADR-0021 for runner authority/process boundary.

## Phase 2 — Runner model and persistence

- [x] T008 Add runner schema/version constants.
- [x] T009 Add `AgentRun` model/serialization/validation.
- [x] T010 Add `RunnerRegistry` model/serialization/validation.
- [x] T011 Add exit-result model/serialization/validation.
- [x] T012 Add atomic JSON persistence helper.
- [x] T013 Add default `.execution/runs/` path helper.
- [x] T014 Add deterministic per-run log/result paths.
- [x] T015 Add duplicate non-terminal task-run invariant.
- [x] T016 Add registry reconciliation helpers.

## Phase 3 — Allocation/process safety

- [x] T017 Load active V3 allocation from lease registry.
- [x] T018 Validate repository/source revision against current checkout.
- [x] T019 Validate expected registered worktree and handoff existence.
- [x] T020 Add command argv placeholder expansion with no shell.
- [x] T021 Add Linux process fingerprint helper with fail-closed fallback.
- [x] T022 Add process liveness + identity comparison.
- [x] T023 Add safe process-group signal helper.
- [x] T024 Ensure persisted metadata excludes environment values.

## Phase 4 — Child wrapper and lifecycle

- [x] T025 Add detached `runner_child` wrapper entry point.
- [x] T026 Execute target argv with `shell=False`.
- [x] T027 Force target cwd to allocation worktree.
- [x] T028 Support handoff-to-stdin delivery.
- [x] T029 Stream target stdout/stderr to runner-owned logs.
- [x] T030 Persist exit result atomically.
- [x] T031 Add `start_run` lifecycle operation.
- [x] T032 Add `refresh_run` lifecycle operation.
- [x] T033 Reconcile wrapper result into succeeded/failed status.
- [x] T034 Reconcile vanished process into orphaned status.
- [x] T035 Add graceful `stop_run` process-group termination.
- [x] T036 Add explicit force-kill escalation.
- [x] T037 Reject signaling on process fingerprint mismatch.
- [x] T038 Keep V3 lease/worktree untouched on terminal runner states.
- [x] T039 Add log-reading helper with bounded output.

## Phase 5 — CLI/docs

- [x] T040 Add `runner_cli.py` command handlers/rendering.
- [x] T041 Register runner commands through the composed console entrypoint.
- [x] T042 Register `runner-status` in the runner CLI.
- [x] T043 Register `runner-stop` in the runner CLI.
- [x] T044 Register `runner-logs` in the runner CLI.
- [x] T045 Support literal `--command` argv remainder.
- [x] T046 Support `--stdin-handoff`.
- [x] T047 Support JSON and human-readable output.
- [x] T048 Update `engineering-graph/README.md`.
- [x] T049 Add `docs/architecture/AGENT_RUNNER.md`.
- [x] T050 Update `docs/architecture/EXECUTION_GRAPH.md` future-extension state.
- [x] T051 Update `docs/development/engineering-graph.md`.
- [x] T052 Update `AGENTS.md` with runner authority/lifecycle rules.

## Phase 6 — Unit/integration validation

- [x] T053 Test run/registry/result roundtrip and malformed payload rejection.
- [x] T054 Test duplicate active-run prevention.
- [x] T055 Test argv placeholders and no-shell execution.
- [x] T056 Test process fingerprint/liveness mismatch safety.
- [x] T057 Test start/status/log lifecycle in a temporary real Git worktree.
- [x] T058 Test successful exit-code reconciliation.
- [x] T059 Test non-zero exit-code reconciliation.
- [x] T060 Test vanished process becomes orphaned.
- [x] T061 Test graceful stop of a harmless long-running fixture.
- [x] T062 Test force escalation path across detached CLI invocations.
- [x] T063 Test V3 lease remains active after runner exit/stop.
- [x] T064 Test CLI parser/routing and JSON surfaces.
- [x] T065 Re-run full V1–V4 Engineering Graph suite.

## Phase 7 — CI/convergence

- [x] T066 Add V5 harmless fixture lifecycle coverage to the Engineering Graph CI offline integration gate.
- [x] T067 Assert fixture cwd equals allocated worktree.
- [x] T068 Assert fixture receives handoff through stdin when requested.
- [x] T069 Assert stdout/stderr/result artifacts are produced.
- [x] T070 Assert duplicate running launch is rejected.
- [x] T071 Assert status observes terminal exit code without Task mutation.
- [x] T072 Assert graceful/force stop semantics on harmless long-running fixtures.
- [x] T073 Assert V3 lease remains unchanged after runner lifecycle.
- [x] T074 Preserve application runtime dependency isolation gate.
- [ ] T075 Run Spec Kit validation on final HEAD.
- [ ] T076 Run Engineering Graph workflow on final HEAD.
- [ ] T077 Run Product CI on final HEAD.
- [x] T078 Create `analysis.md` mapping FR/SC to evidence.
- [x] T079 Create `convergence.md` with lifecycle/authority validation.
- [x] T080 Reconcile all task statuses against actual evidence.
- [ ] T081 Freeze V5 only after Spec Kit + Engineering Graph + Product CI are green on the same final HEAD.
