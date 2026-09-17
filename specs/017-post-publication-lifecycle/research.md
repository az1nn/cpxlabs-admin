# Research: Post-Publication Lifecycle V9

## Problem

V8 deliberately stops at PR creation. After human review/merge, derived execution state can remain active: leases, worktrees and publication records. Cleaning those objects is safe only when the repository proves that the work is truly represented in the merged base.

A second operational gap exists in AI-assisted work: asynchronous checks and human observations are easy to lose between sessions. Generic “continue” language is insufficient because it can omit the exact HEAD, PR, pending gate and next action.

## Key decisions

### 1. Reconcile, do not infer completion

PR merge is necessary but not sufficient for Task completion. V9 verifies that the merged base already contains the Task checkbox as complete. If not, finalization stops. This preserves Git-backed Spec Kit state as authority.

### 2. Human merge remains external

V9 reads GitHub PR state through `gh`; it never merges, approves, closes, or enables auto-merge.

### 3. Base reachability is required

A PR API saying “merged” is not enough. The merge commit must be an ancestor of the refreshed configured base. This prevents cleanup against stale/local base state.

### 4. Cleanup is explicit

Read-only reconciliation is separate from cleanup. Lease release requires an explicit finalize command. Worktree removal requires an additional flag and fails on dirty state.

### 5. Receipts are derived

Lifecycle receipts live beneath `.execution/`. They are useful for idempotency and audit of local orchestration actions but never become canonical Task/Neo4j truth.

### 6. Continuation prompt is a contract

Every pause/handoff/external wait produces a prompt that can be pasted into a new turn/chat without reconstructing narrative history. It must be refreshed when HEAD/PR/gate state changes.

### 7. Human Async Gates are first-class review evidence

A Human Async Gate represents a required result that cannot be synchronously asserted by the current automation, such as a later manual smoke, external propagation check, or human acceptance observation. CI and Human Async Gates are independent dimensions.

## Human Async Gate schema

```text
Gate ID: HAG-###
Subject: what is being validated
Trigger / evidence: run, URL, deployment, artifact, timestamp
Expected observation: concrete pass condition
Approver: human role/person
Status: PENDING | PASSED | FAILED | WAIVED
Rationale: required for WAIVED, useful otherwise
Freshness boundary: HEAD/build/deploy the observation applies to
Next action: exact action after this gate resolves
```

## Failure modes considered

- PR is still open -> no cleanup.
- PR claims merged but merge commit is not in refreshed base -> no cleanup.
- publication/lease identity mismatch -> no cleanup.
- Task is not checked complete in merged base -> no cleanup; generate continuation path.
- worktree dirty -> lease may be released only if explicitly requested without removal; removal fails closed.
- receipt already finalized -> return existing state without duplicate mutation.
- async/human test pending -> readiness/completion claim is blocked if that gate is required.
