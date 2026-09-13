---
graph:
  task_links:
    T020:
      implements:
        - engineering-graph/src/engineering_graph/runner.py
    T021:
      implements:
        - engineering-graph/src/engineering_graph/runner_child.py
    T040:
      implements:
        - engineering-graph/src/engineering_graph/runner_cli.py
    T041:
      implements:
        - engineering-graph/src/engineering_graph/cli.py
    T056:
      validated_by:
        - engineering-graph/tests/test_runner.py
    T057:
      validated_by:
        - engineering-graph/tests/test_runner_cli.py
---
# Tasks: Agent Runner V5

## Phase 1 — Spec/architecture

- [x] T001 Create `SPEC-013-AGENT-RUNNER` feature specification.
- [x] T002 Record process-lifecycle research and safety boundary.
- [x] T003 Define V5 implementation plan.
- [x] T004 Define run/registry/result data model.
- [ ] T005 Add requirements checklist.
- [x] T006 Add quickstart/lifecycle documentation.
- [ ] T007 Add ADR-0021 for runner authority/process boundary.

## Phase 2 — Runner model and persistence

- [ ] T008 Add runner schema/version constants.
- [ ] T009 Add `AgentRun` model/serialization/validation.
- [ ] T010 Add `RunnerRegistry` model/serialization/validation.
- [ ] T011 Add exit-result model/serialization/validation.
- [ ] T012 Add atomic JSON persistence helper.
- [ ] T013 Add default `.execution/runs/` path helper.
- [ ] T014 Add deterministic per-run log/result paths.
- [ ] T015 Add duplicate non-terminal task-run invariant.
- [ ] T016 Add registry reconciliation helpers.

## Phase 3 — Allocation/process safety

- [ ] T017 Load active V3 allocation from lease registry.
- [ ] T018 Validate repository/source revision against current checkout.
- [ ] T019 Validate expected registered worktree and handoff existence.
- [ ] T020 Add command argv placeholder expansion with no shell.
- [ ] T021 Add Linux process fingerprint helper with fail-closed fallback.
- [ ] T022 Add process liveness + identity comparison.
- [ ] T023 Add safe process-group signal helper.
- [ ] T024 Ensure persisted metadata excludes environment values.

## Phase 4 — Child wrapper and lifecycle

- [ ] T025 Add detached `runner_child` wrapper entry point.
- [ ] T026 Execute target argv with `shell=False`.
- [ ] T027 Force target cwd to allocation worktree.
- [ ] T028 Support handoff-to-stdin delivery.
- [ ] T029 Stream target stdout/stderr to runner-owned logs.
- [ ] T030 Persist exit result atomically.
- [ ] T031 Add `start_run` lifecycle operation.
- [ ] T032 Add `refresh_run` lifecycle operation.
- [ ] T033 Reconcile wrapper result into succeeded/failed status.
- [ ] T034 Reconcile vanished process into orphaned status.
- [ ] T035 Add graceful `stop_run` process-group termination.
- [ ] T036 Add explicit force-kill escalation.
- [ ] T037 Reject signaling on process fingerprint mismatch.
- [ ] T038 Keep V3 lease/worktree untouched on terminal runner states.
- [ ] T039 Add log-reading helper with bounded output.

## Phase 5 — CLI/docs

- [ ] T040 Add `runner_cli.py` command handlers/rendering.
- [ ] T041 Register `runner-start` in main CLI.
- [ ] T042 Register `runner-status` in main CLI.
- [ ] T043 Register `runner-stop` in main CLI.
- [ ] T044 Register `runner-logs` in main CLI.
- [ ] T045 Support repeated `--command` argv tokens.
- [ ] T046 Support `--stdin-handoff`.
- [ ] T047 Support JSON and human-readable output.
- [ ] T048 Update `engineering-graph/README.md`.
- [ ] T049 Add `docs/architecture/AGENT_RUNNER.md`.
- [ ] T050 Update `docs/architecture/EXECUTION_GRAPH.md` future-extension state.
- [ ] T051 Update `docs/development/engineering-graph.md`.
- [ ] T052 Update `AGENTS.md` with runner authority/lifecycle rules.

## Phase 6 — Unit/integration validation

- [ ] T053 Test run/registry/result roundtrip and malformed payload rejection.
- [ ] T054 Test duplicate active-run prevention.
- [ ] T055 Test argv placeholders and no-shell execution.
- [ ] T056 Test process fingerprint/liveness mismatch safety.
- [ ] T057 Test start/status/log lifecycle in a temporary real Git worktree.
- [ ] T058 Test successful exit-code reconciliation.
- [ ] T059 Test non-zero exit-code reconciliation.
- [ ] T060 Test vanished process becomes orphaned.
- [ ] T061 Test graceful stop of a harmless long-running fixture.
- [ ] T062 Test force escalation path.
- [ ] T063 Test V3 lease remains active after runner exit/stop.
- [ ] T064 Test CLI parser surfaces and JSON output.
- [ ] T065 Re-run full V1–V4 Engineering Graph suite.

## Phase 7 — CI/convergence

- [ ] T066 Add V5 harmless fixture lifecycle smoke to Engineering Graph CI.
- [ ] T067 Assert fixture cwd equals allocated worktree.
- [ ] T068 Assert fixture receives handoff through stdin when requested.
- [ ] T069 Assert stdout/stderr/result artifacts are produced.
- [ ] T070 Assert duplicate running launch is rejected.
- [ ] T071 Assert status observes terminal exit code without Task mutation.
- [ ] T072 Assert stop semantics on a long-running fixture.
- [ ] T073 Assert V3 lease remains unchanged after runner lifecycle.
- [ ] T074 Preserve application runtime dependency isolation gate.
- [ ] T075 Run Spec Kit validation on final HEAD.
- [ ] T076 Run Engineering Graph workflow on final HEAD.
- [ ] T077 Run Product CI on final HEAD.
- [ ] T078 Create `analysis.md` mapping FR/SC to evidence.
- [ ] T079 Create `convergence.md` with final lifecycle/authority validation.
- [ ] T080 Reconcile all task statuses against actual evidence.
- [ ] T081 Freeze V5 only after Spec Kit + Engineering Graph + Product CI are green on the same final HEAD.
