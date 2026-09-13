# ADR-0021: Agent Runner Process Authority Boundary

**Status**: Accepted

## Context

V3 prepares revision-bound `ExecutionAllocation` objects with isolated Git worktrees, derived context/handoff files and local leases. V4 adds retrieval assistance. A remaining manual gap is starting and observing the actual coding-agent process.

A naïve runner could accidentally invert project authority by treating process completion as Task completion, mutating Git, automatically releasing leases, or persisting unsafe process identifiers that later signal unrelated processes.

## Decision

Introduce V5 Agent Runner as local engineering-only process lifecycle infrastructure with these boundaries:

1. V5 may consume only an already-active V3 allocation.
2. V5 does not select tasks, create worktrees, acquire/release task leases, or change canonical task state.
3. Child commands are argv arrays launched with `shell=False`; no shell interpolation is part of the runner contract.
4. Child cwd is forced to the allocation worktree.
5. Generated handoff content may be delivered to stdin without shell redirection.
6. Runner registry, run records and logs are derived/disposable state under `.execution/runs/`.
7. Environment values are never serialized into run metadata.
8. Runner state records PID plus a process-start fingerprint when available. Stop operations fail closed if identity cannot be proven or has changed.
9. Agent subprocesses execute in a dedicated process group/session so lifecycle operations target the spawned tree.
10. Exit code is execution evidence only. It never means a Spec Kit Task is complete.
11. Runner exit/stop never automatically commits, pushes, opens/merges PRs, releases V3 leases or mutates Neo4j/project truth.

## Consequences

### Positive

- local agent invocation becomes reproducible and observable;
- detached process results can be recovered through a wrapper-owned exit-result file;
- task/worktree authority remains in V3 and canonical Git files;
- PID reuse is treated as a safety problem rather than ignored;
- a later wave supervisor can consume machine-readable run state without changing this authority contract.

### Trade-offs

- operators must still explicitly release leases;
- successful process exit still requires human/agent review and canonical evidence updates;
- agent CLI argv stays configurable because vendor CLI syntax is not architectural authority;
- process identity support is strongest on Linux; unsupported platforms fail closed for destructive stop operations when identity cannot be verified.

## Rejected alternatives

### Treat exit code 0 as Task completion

Rejected. Process success is not equivalent to correct implementation, tests, review or canonical task evidence.

### Use `shell=True` command strings

Rejected. Shell interpolation adds quoting/injection ambiguity and hides the exact executed argv.

### Store only PID

Rejected. PID reuse can cause a later stop request to signal an unrelated process.

### Put runner state into Neo4j

Rejected. Runtime process observations are local ephemeral orchestration state, not deterministic repository knowledge.

### Automatically commit/push/open PR after agent exit

Rejected for V5. Publication requires separate provenance/review policy and a future ADR/spec.
