# Agent Supervisor V6

## Purpose

Agent Supervisor V6 closes the coordination gap between V3 execution waves and V5 single-process lifecycle management. It supervises exactly one already-planned, already-prepared wave and starts V5 runs within explicit concurrency and retry bounds.

V6 is engineering tooling only. It is not canonical task state, a Git publisher, a validation authority, a lease owner or a product-runtime dependency.

## Authority chain

```text
Git / Spec Kit / code / tests / Git history
                    |
                    v
          deterministic Engineering Graph
                    |
                    v
         V3 ExecutionManifest + leases
                    |
                    v
            V6 SupervisorJob
                    |
                    v
              V5 Agent Runner
                    |
                    v
             processes + logs
                 derived only
```

Authority never flows upward from supervisor or runner state. A supervisor task marked `succeeded` means only that its latest owned V5 run exited with code `0`. A supervisor job marked `settled` means only that no task remains pending, running or retryable under that job policy.

## Preconditions

A job can be created only when:

1. the manifest is valid and cycle-free;
2. manifest repository matches the configured repository;
3. manifest `sourceRevision` equals current Git HEAD;
4. the requested wave exists;
5. every wave task has an active V3 allocation;
6. allocation repository/revision/agent match the manifest;
7. no active supervisor already claims any selected task;
8. no selected task already has a non-terminal V5 run outside the new job.

V6 does not create or repair V3 allocations. Re-plan/re-prepare when those contracts are stale.

## Derived state

Default:

```text
engineering-graph/.execution/supervisor/
└── jobs/
    └── <job-id>.json
```

Each job records manifest identity, wave, argv, policy, ordered task state and exact owned V5 `runId` history. Writes use atomic replacement. The subtree is disposable and contains no canonical project knowledge.

## Tick semantics

`supervisor-tick` is the scheduling primitive:

1. reconcile V5 runner state;
2. map each task only through its exact job-owned latest `runId`;
3. convert V5 states into supervisor observations;
4. calculate available slots from `maxParallel`;
5. launch pending/retryable tasks in manifest-wave order;
6. persist job ownership immediately after every successful launch.

Repeated ticks while all slots are occupied do not launch duplicate work.

## Retry semantics

Retries are bounded by `maxAttempts`:

- `succeeded` -> supervisor `succeeded`, never relaunched;
- `failed` or `orphaned` -> `pending` while attempts remain, otherwise `exhausted`;
- `stopped` -> supervisor `stopped`, never automatically retried;
- `running` -> remains `running` and consumes one concurrency slot.

A retry is another V5 run and therefore receives a new exact `runId` appended to the task's ownership history.

## Stop semantics

`supervisor-stop` does not signal processes directly. For every job task currently observed as running it:

1. reconciles the V5 registry;
2. verifies the latest V5 run for that task has the exact job-owned `runId`;
3. fails closed on ownership mismatch;
4. delegates termination to V5 `stop_run`, including PID/fingerprint/process-group safety;
5. marks remaining non-terminal supervisor tasks stopped;
6. persists the job as `stopped`.

No lease is released and no worktree is removed.

## CLI

```bash
graph-engineering supervisor-start .execution/manifest.json \
  --wave 1 \
  --max-parallel 2 \
  --max-attempts 2 \
  --stdin-handoff \
  --json \
  --command <agent-executable> <agent-argv...>

graph-engineering supervisor-tick <JOB-ID> --json
graph-engineering supervisor-status --job <JOB-ID> --json
graph-engineering supervisor-stop <JOB-ID> --json
```

Every token after `--command` belongs literally to the V5 child argv template.

## Explicit non-goals

V6 does not:

- infer or write Spec Kit Task completion;
- execute allocation validation commands automatically;
- release V3 leases or remove worktrees;
- commit, push, open/review/merge pull requests;
- schedule across hosts or repositories;
- execute agents remotely;
- project supervisor/process state into Neo4j.

These require separate policy and authority decisions rather than being inferred from process success.