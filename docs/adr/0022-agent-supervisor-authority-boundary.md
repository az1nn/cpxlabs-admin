# ADR-0022: Agent Supervisor Authority Boundary

**Status**: Accepted

## Context

V3 owns dependency-safe execution planning, worktree allocation and local leases. V5 owns one local coding-agent process lifecycle for an already-active allocation. Coordinating multiple V5 runs introduces scheduling policy, retry policy and ownership state that must not silently become canonical project truth.

## Decision

Introduce V6 Agent Supervisor as local engineering-only orchestration with these boundaries:

1. V6 consumes one valid V3 manifest wave and already-active V3 allocations.
2. V6 may start/reconcile/stop V5 runs but does not implement its own process signaling semantics.
3. V6 persists only disposable state under `.execution/supervisor/`.
4. Job ownership is explicit through ordered job-owned V5 `runId` history.
5. Concurrency and attempts are explicitly bounded per job.
6. Automatic retry is allowed only for `failed`/`orphaned` execution observations while attempts remain.
7. Explicitly `stopped` runs are never automatically retried.
8. `succeeded` means V5 process exit code 0 only. `settled` means supervisor scheduling has no more runnable/retryable work only.
9. Neither state marks a Spec Kit Task complete or proves implementation correctness.
10. V6 never edits canonical task/spec/code files, commits/pushes, opens/reviews/merges PRs, releases V3 leases, removes worktrees or projects runtime state into Neo4j.
11. Validation execution and publication automation require separate future policy/spec decisions.

## Consequences

### Positive

- execution waves can be coordinated without a resident daemon;
- bounded concurrency/retry behavior is deterministic and inspectable;
- V3 allocation and V5 process safety remain single-owner responsibilities;
- supervisor state can be deleted without losing project truth.

### Trade-offs

- operators still decide when canonical work is complete;
- leases still require explicit release;
- validation/publication remain separate manual or future automated stages;
- a tick must be invoked again after runner state changes unless a future daemon invokes it.

## Rejected alternatives

### Make the supervisor the canonical task scheduler

Rejected. Canonical task state remains in Git-backed Spec Kit artifacts.

### Retry stopped runs

Rejected. Stop is explicit operator/process lifecycle intent and must not be undone automatically.

### Release leases after a successful run

Rejected. Process success does not prove task completion or safe cleanup.

### Run as a mandatory background daemon

Rejected for V6. A tick primitive is simpler to recover, test and later embed in a daemon without changing policy semantics.
