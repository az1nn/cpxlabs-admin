---
graph:
  id: SPEC-014-AGENT-SUPERVISOR
  enforced: true
  constrained_by:
    - ADR-0022
  depends_on:
    - SPEC-011-EXECUTION-GRAPH
    - SPEC-013-AGENT-RUNNER
---
# Feature Specification: Agent Supervisor V6

**Status**: Ready

## Problem

V3 can plan dependency-safe execution waves and prepare isolated `ExecutionAllocation` leases. V5 can start, observe and stop one coding-agent process for one active allocation. Coordinating a complete wave is still manual: an operator has to start each run, respect a concurrency bound, inspect terminal states and decide whether a failed execution should be retried.

V6 introduces a local deterministic supervisor over already-prepared V3 allocations and V5 runs. It coordinates process execution only; it does not become project authority.

## Goals

1. Create a revision-bound supervisor job for exactly one V3 execution wave.
2. Require every supervised task to have an active allocation matching repository, revision, agent and wave identity.
3. Start V5 runs deterministically up to an explicit concurrency limit.
4. Reconcile supervisor task state from V5 run evidence across CLI invocations.
5. Support bounded automatic retries for failed/orphaned executions only.
6. Never retry an explicitly stopped run automatically.
7. Persist versioned disposable supervisor state under `.execution/supervisor/`.
8. Stop active runs for one supervisor job safely through V5 stop semantics.
9. Keep Task completion, Git publication, lease release and Neo4j projection outside supervisor authority.
10. Preserve V1–V5 behavior and product-runtime isolation.

## Non-goals

- marking Spec Kit tasks complete;
- editing `tasks.md` or any canonical project file;
- automatic validation-command execution;
- automatic commit, push, PR creation, review or merge;
- automatic V3 lease release or worktree removal;
- selecting work outside the supplied manifest wave;
- distributed/multi-host scheduling;
- priority queues across repositories;
- remote process execution;
- projecting supervisor/process state into Neo4j.

## Functional Requirements

- **FR-001**: A supervisor job MUST consume a valid V3 `ExecutionManifest` and exactly one wave index.
- **FR-002**: Job creation MUST reject manifest repository mismatch.
- **FR-003**: Job creation MUST reject manifest/source revision mismatch with current Git HEAD.
- **FR-004**: Job creation MUST reject manifests with dependency cycles.
- **FR-005**: Every wave task MUST have an active V3 allocation before the supervisor job can be created.
- **FR-006**: Every allocation MUST match the manifest repository, source revision and agent.
- **FR-007**: A non-terminal supervisor job MUST prevent another non-terminal supervisor job from claiming the same task under the same execution root.
- **FR-008**: Supervisor jobs MUST persist a versioned identity, manifest path, wave, ordered tasks, argv, retry/concurrency policy and timestamps.
- **FR-009**: Supervisor per-task state MUST persist ordered V5 `runId` history and attempt count.
- **FR-010**: `maxParallel` MUST be at least 1.
- **FR-011**: `maxAttempts` MUST be at least 1.
- **FR-012**: One tick MUST first reconcile V5 runner state before deciding whether to launch work.
- **FR-013**: A tick MUST never exceed `maxParallel` non-terminal runs owned by that job.
- **FR-014**: Pending tasks MUST be launched in manifest-wave order.
- **FR-015**: A task whose latest owned run is `succeeded` MUST become supervisor `succeeded` and MUST NOT be relaunched.
- **FR-016**: A task whose latest owned run is `failed` or `orphaned` MAY be relaunched only while attempts remain.
- **FR-017**: A task whose latest owned run is `stopped` MUST NOT be automatically retried.
- **FR-018**: A failed/orphaned task with no attempts remaining MUST become `exhausted`.
- **FR-019**: `succeeded` means only V5 process exit code 0; it MUST NOT imply canonical Task completion.
- **FR-020**: A job MUST become `settled` only when none of its tasks are pending/running/retryable.
- **FR-021**: `settled` MUST NOT mutate Task status, leases, worktrees, Git history or Neo4j.
- **FR-022**: `supervisor-status` MUST inspect one or all jobs without launching new runs.
- **FR-023**: `supervisor-tick` MUST be the only command that advances an existing active job by launching retry/new work.
- **FR-024**: `supervisor-start` MUST create the job and perform exactly one tick.
- **FR-025**: `supervisor-stop` MUST stop only the current V5 runs owned by the target job.
- **FR-026**: Stop MUST fail closed if the latest task run no longer matches the job-owned run id.
- **FR-027**: Stopping a supervisor job MUST NOT release V3 leases.
- **FR-028**: Supervisor state writes MUST use atomic replacement.
- **FR-029**: Supervisor state MUST be disposable without deleting V3/V5 state or canonical files.
- **FR-030**: CLI surfaces MUST provide JSON output suitable for later automation.
- **FR-031**: Application packages MUST remain unable to depend on supervisor/Engineering Graph runtime.
- **FR-032**: V6 MUST preserve the V1–V5 Engineering Graph test suite and product CI.

## Success Criteria

- **SC-001**: A prepared two-task wave can be supervised with `maxParallel=1`, launching exactly one task per available slot in wave order.
- **SC-002**: With `maxParallel=2`, no tick creates more than two owned non-terminal runs.
- **SC-003**: Failed/orphaned runs retry only up to `maxAttempts`; stopped runs are never retried automatically.
- **SC-004**: Repeated ticks are idempotent while all available slots are occupied by owned running processes.
- **SC-005**: A completed job is observable as `settled` while V3 leases and canonical Task state remain unchanged.
- **SC-006**: Overlapping active supervisor jobs are rejected deterministically.
- **SC-007**: Stop targets only job-owned latest runs and delegates process identity safety to V5.
- **SC-008**: Deleting `.execution/supervisor/` loses no canonical project knowledge.
- **SC-009**: Existing V1–V5 Engineering Graph tests remain green.
- **SC-010**: Spec Kit, Engineering Graph and Product CI are green on the same final freeze HEAD.
