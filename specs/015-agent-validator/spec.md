---
graph:
  id: SPEC-015-AGENT-VALIDATOR
  enforced: true
  constrained_by:
    - ADR-0023
  depends_on:
    - SPEC-011-EXECUTION-GRAPH
    - SPEC-013-AGENT-RUNNER
    - SPEC-014-AGENT-SUPERVISOR
---
# Feature Specification: Agent Validator V7

**Status**: Ready

## Problem

V3 prepares revision-bound allocations and freezes validation commands from deterministic task context. V5 executes one coding-agent process, and V6 coordinates a prepared wave. A successful process exit still does not prove that the implementation is valid. Operators must currently enter each worktree, recover the allocation's validation commands, execute them manually, and preserve the result outside a stable machine-readable contract.

V7 introduces a local deterministic validation layer for an already-active V3 allocation after execution has completed successfully. It executes only the validation commands already frozen into that allocation, records disposable evidence, and remains strictly outside canonical Task and Git publication authority.

## Goals

1. Validate exactly one active V3 allocation at a time.
2. Require the latest V5 run for the task to be terminal and `succeeded` before validation.
3. When the task belongs to a V6 job, require the latest supervisor-owned run id to match the latest V5 run id and the supervisor task observation to be `succeeded`.
4. Execute only `validationCommands` frozen into the allocation; V7 accepts no arbitrary validation command override.
5. Parse commands into argv with `shell=False` and execute from the allocation worktree.
6. Execute commands sequentially and fail closed on the first non-zero exit by default.
7. Persist a versioned, atomic, disposable validation record under `.execution/validation/` with command argv, exit code, timestamps and log paths.
8. Bind validation evidence to a deterministic workspace identity and require the workspace to remain unchanged while validation runs.
9. Provide status/inspection without re-executing validation.
10. Keep canonical Task mutation, lease release, commit/push/PR/merge and Neo4j projection outside V7 authority.
11. Preserve V1–V6 behavior and product-runtime isolation.

## Non-goals

- inferring or writing Spec Kit Task completion;
- accepting caller-supplied validation commands;
- changing allocation validation commands after preparation;
- committing, pushing, opening/reviewing/merging pull requests;
- releasing leases or removing worktrees;
- treating process success or validation success as review approval;
- projecting validation runtime state into Neo4j;
- remote/distributed validation execution.

## Functional Requirements

- **FR-001**: `validation-run` MUST target one task id with an active V3 allocation.
- **FR-002**: The allocation repository MUST match configured repository identity.
- **FR-003**: The allocation source revision MUST match the current repository HEAD, otherwise validation MUST fail as stale.
- **FR-004**: The allocation worktree MUST be registered, exist, and be on the allocation branch.
- **FR-005**: The allocation MUST contain at least one frozen `validationCommand`.
- **FR-006**: The latest V5 run for the task MUST exist, be terminal, and have status `succeeded`.
- **FR-007**: The latest V5 run MUST match allocation repository, source revision, branch and worktree identity.
- **FR-008**: If a V6 supervisor job owns the task, V7 MUST fail closed unless the latest supervisor-owned `runId` equals the latest V5 run id and its task observation is `succeeded`.
- **FR-009**: V7 MUST NOT accept arbitrary command overrides from CLI/API.
- **FR-010**: Every frozen command MUST be tokenized with `shlex.split` and executed with `shell=False`.
- **FR-011**: Empty/invalid command tokenization MUST fail closed before execution.
- **FR-012**: Commands MUST execute sequentially from the allocation `worktreePath`.
- **FR-013**: Default execution MUST stop after the first non-zero command exit.
- **FR-014**: Command stdout/stderr MUST be captured to per-command files rather than embedded unbounded in the registry.
- **FR-015**: A validation record MUST contain version, validation id, repository/task/spec/source revision, run id, branch/worktree identity, overall status, ordered command results and timestamps.
- **FR-016**: Validation records MUST use atomic JSON replacement.
- **FR-017**: Validation record status MUST be `passed` only when every frozen command exits 0 and all other V7 validity invariants hold; otherwise it MUST be `failed`.
- **FR-018**: Validation state MUST be stored only under `.execution/validation/` and remain disposable.
- **FR-019**: `validation-status` MUST inspect latest/all records without executing commands.
- **FR-020**: Validation success MUST NOT edit `tasks.md`, specs, ADRs, code or any other canonical artifact.
- **FR-021**: Validation success MUST NOT release leases or remove worktrees.
- **FR-022**: Validation success MUST NOT commit, push, open/review/merge PRs or otherwise publish Git state.
- **FR-023**: No application package may depend on V7 or its generated state.
- **FR-024**: V7 MUST preserve the V1–V6 Engineering Graph tests and Product CI.
- **FR-025**: V7 MUST record the worktree Git revision plus deterministic SHA-256 workspace fingerprints before and after command execution, covering the tracked diff and non-ignored untracked files.
- **FR-026**: A validation record MUST NOT be `passed` when the Git revision or workspace fingerprint changes while validation executes.

## Success Criteria

- **SC-001**: A successful latest V5 run plus two frozen successful commands produces one `passed` validation record with two ordered command results.
- **SC-002**: A first-command failure produces `failed`, does not execute later commands, and preserves stdout/stderr logs.
- **SC-003**: A stopped/failed/orphaned/running latest V5 run is rejected before any validation subprocess starts.
- **SC-004**: A supervisor ownership/run-id mismatch is rejected before any validation subprocess starts.
- **SC-005**: CLI offers no option for injecting or replacing validation commands.
- **SC-006**: Validation subprocesses use argv + `shell=False` in the allocation worktree.
- **SC-007**: Deleting `.execution/validation/` loses no canonical project knowledge.
- **SC-008**: No validation path mutates Task state, leases, worktrees or Git history.
- **SC-009**: Existing V1–V6 Engineering Graph tests remain green.
- **SC-010**: Spec Kit, Engineering Graph and Product CI are green on the same final freeze HEAD.
- **SC-011**: A validation command that mutates the publishable workspace cannot yield an overall `passed` record even if the command itself exits 0.
