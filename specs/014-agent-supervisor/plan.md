# Implementation Plan: Agent Supervisor V6

## Summary

Build a local, versioned supervisor above V3 `ExecutionManifest`/allocations and V5 Agent Runner. The supervisor owns only disposable orchestration policy/state. It never becomes authority for task completion, Git publication, lease release or graph truth.

## Architecture

```text
Git / Spec Kit / code / tests
          |
          v
Engineering Graph projection
          |
          v
V3 ExecutionManifest + active allocations
          |
          v
V6 SupervisorJob (derived policy/state)
          |
          +---- tick ----> V5 start_run / reconcile_registry / stop_run
                              |
                              v
                         processes + logs
```

## Implementation slices

1. Add supervisor versioned models, validation and atomic persistence under `.execution/supervisor/jobs/`.
2. Validate manifest/wave identity and active V3 allocation compatibility before creating a job.
3. Add deterministic reconciliation from job-owned V5 run history.
4. Add bounded concurrency and retry scheduling in `supervisor_tick`.
5. Add fail-closed job stop semantics delegated to V5 process safety.
6. Add `supervisor-start`, `supervisor-tick`, `supervisor-status`, `supervisor-stop` CLI surfaces.
7. Route supervisor commands through the composed `graph-engineering` entrypoint.
8. Add unit/CLI tests and architecture documentation.
9. Run convergence and freeze only after Spec Kit + Engineering Graph + Product CI are green on one final HEAD.

## Safety invariants

- No task is supervised without an active V3 allocation.
- No task is claimed by two active supervisor jobs under one execution root.
- No tick launches work from another wave.
- No tick launches beyond `maxParallel`.
- Retry count is bounded by `maxAttempts`.
- Explicitly stopped runs are not automatically retried.
- Job stop targets only the latest run id recorded by the job.
- Supervisor terminal states never release leases or edit canonical task state.

## Compatibility

No product package imports `engineering_graph`. Existing runner APIs remain unchanged; V6 composes them. No Neo4j schema change is required because supervisor state is intentionally not projected.

## Complexity tracking

The new abstraction is justified because V3 and V5 deliberately stop on opposite sides of multi-run coordination. Keeping supervision in a separate module preserves those established authority boundaries instead of expanding either subsystem implicitly.
