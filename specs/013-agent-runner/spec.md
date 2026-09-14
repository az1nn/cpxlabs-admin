---
graph:
  id: SPEC-013-AGENT-RUNNER
  enforced: true
  constrained_by:
    - ADR-0021
  depends_on:
    - SPEC-011-EXECUTION-GRAPH
    - SPEC-012-GRAPHRAG
---
# Feature Specification: Agent Runner V5

**Status**: Ready

## Problem

V3 can safely plan and prepare work into revision-bound `ExecutionAllocation` objects, but execution still stops at the handoff boundary. An operator must manually enter the worktree, invoke the coding agent, track its process, collect logs, and decide when execution has ended.

V5 adds a local process-lifecycle runner that consumes an already-active V3 allocation. It must preserve the authority model: the runner may execute and observe an agent process, but it is not allowed to infer task completion, mutate canonical task state, commit, push, open/merge pull requests, or create graph truth.

## Goals

1. Start one coding-agent process only from an active, current V3 allocation.
2. Force execution inside the allocation worktree and bind the run to repository/task/revision/agent identity.
3. Deliver the generated handoff to the child process without requiring shell interpolation.
4. Persist versioned derived run metadata plus stdout/stderr logs under `.execution/runs/`.
5. Inspect running/completed/stale process state across CLI invocations.
6. Stop a verified child process safely, preferring graceful termination and refusing unsafe PID reuse cases.
7. Prevent duplicate active runs for the same allocation/task.
8. Keep all runner state disposable and outside canonical repository knowledge.
9. Preserve V1–V4 behavior and product-runtime isolation.

## Non-goals

- automatic commit or push;
- automatic PR creation/review/merge;
- canonical Task status mutation;
- distributed/multi-host scheduling;
- queue prioritization across repositories;
- agent decision making or LLM answer synthesis;
- automatic validation-command execution;
- automatic lease release;
- interpreting process exit code as task completion;
- replacing V3 leases/worktrees or V2 handoffs.

## Functional Requirements

- **FR-001**: The runner MUST consume an existing active V3 `ExecutionAllocation`/lease rather than creating its own worktree or task selection.
- **FR-002**: The runner MUST reject a task with no active lease.
- **FR-003**: The runner MUST reject repository identity mismatch.
- **FR-004**: The runner MUST reject allocation revision mismatch with current Git HEAD before launch.
- **FR-005**: The runner MUST require the allocation worktree to exist and be registered as the expected Git worktree.
- **FR-006**: The runner MUST require the allocation handoff file to exist before launch.
- **FR-007**: Child process cwd MUST be exactly the allocated worktree path.
- **FR-008**: Runner commands MUST be represented as argv and executed with `shell=False`.
- **FR-009**: Command templates MUST support deterministic placeholders for allocation fields without shell interpolation.
- **FR-010**: The runner MUST support delivering handoff content to child stdin.
- **FR-011**: The runner MUST support explicit command argv override for local/CI use.
- **FR-012**: The runner MUST not persist secret environment values in run metadata.
- **FR-013**: The runner MUST persist a versioned `AgentRun` record for each launch.
- **FR-014**: `AgentRun` MUST include repository, task, spec, source revision, agent, branch, worktree, handoff, argv, pid, process identity, timestamps and status.
- **FR-015**: Runner stdout and stderr MUST be redirected to deterministic per-run files.
- **FR-016**: Run-state writes MUST use atomic replacement.
- **FR-017**: Runner state MUST live under the ignored `.execution/runs/` derived-state root by default.
- **FR-018**: At most one non-terminal run MAY exist for a task within one runner registry.
- **FR-019**: Launch MUST fail closed when an active run already exists for the task.
- **FR-020**: `runner-status` MUST reconcile persisted state with observable OS process state.
- **FR-021**: A vanished process MUST become a terminal/orphaned observation rather than remaining silently `running`.
- **FR-022**: Process stop MUST validate a stored process identity/fingerprint before sending a signal when the platform exposes a verifiable identity.
- **FR-023**: A process identity mismatch MUST fail closed and MUST NOT signal the current PID owner.
- **FR-024**: Normal stop MUST request graceful process-group termination first.
- **FR-025**: Force stop MUST be explicit and MAY escalate to kill only after identity validation.
- **FR-026**: A child exit code MUST be recorded, but MUST NOT mutate canonical Task status.
- **FR-027**: Completing/stopping a run MUST NOT automatically release the V3 lease.
- **FR-028**: Runner commands MUST expose machine-readable JSON output.
- **FR-029**: Runner commands MUST expose concise human-readable output.
- **FR-030**: The CLI MUST provide `runner-start`, `runner-status`, `runner-stop`, and `runner-logs` surfaces.
- **FR-031**: `runner-logs` MUST read derived stdout/stderr only and MUST NOT execute repository code.
- **FR-032**: Run records/logs MUST be disposable without deleting worktrees or canonical files.
- **FR-033**: Application packages MUST remain unable to depend on `engineering_graph`/runner runtime.
- **FR-034**: V5 MUST preserve V1–V4 Engineering Graph tests and CI gates.
- **FR-035**: CI MUST exercise the runner using a harmless local fixture process, not a networked coding agent.
- **FR-036**: CI MUST prove duplicate-run prevention and safe stop semantics.
- **FR-037**: CI MUST prove runner completion leaves V3 lease state unchanged.
- **FR-038**: Runner-generated files MUST remain Git-ignored.

## Success Criteria

- **SC-001**: A prepared V3 allocation can launch a harmless agent fixture inside its exact worktree and produce a versioned run record plus separate stdout/stderr logs.
- **SC-002**: Re-launching the same task while its run is non-terminal fails deterministically.
- **SC-003**: Status transitions from running to a terminal observation without editing canonical Task state.
- **SC-004**: A graceful stop terminates the verified process group and records terminal state.
- **SC-005**: PID/process-identity mismatch prevents signaling.
- **SC-006**: Runner start/status/stop/logs support JSON output suitable for a future supervisor.
- **SC-007**: Deleting `.execution/runs/` loses no canonical knowledge and does not remove V3 worktrees.
- **SC-008**: Existing V1–V4 Engineering Graph CI remains green.
- **SC-009**: Product CI remains green with no runtime dependency on the runner.
- **SC-010**: Spec Kit, Engineering Graph and Product CI are green on the same final freeze HEAD.
