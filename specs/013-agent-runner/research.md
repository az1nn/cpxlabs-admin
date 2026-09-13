# Research: Agent Runner V5

## Source seam

`ExecutionAllocation` from V3 already exposes the complete runner input boundary: task ID, repository/revision, agent, branch, worktree path, context path, handoff path and validation commands. V5 should consume this object rather than reimplement planning, worktree allocation, context generation or leases.

## Lifecycle choice

The runner is intentionally local and process-oriented. One active run maps to one active V3 task allocation. V5 records process lifecycle only; a later supervisor may coordinate multiple runs/waves.

## Command execution

Commands are argv arrays and are launched with `shell=False`. Agent-specific commands are configurable rather than baked into graph authority because Codex/Claude CLI flags can evolve independently. The runner can feed the generated handoff file to stdin so no shell redirection is required.

## Persistent derived state

Default state:

```text
engineering-graph/.execution/runs/
├── registry.json
└── <run-id>/
    ├── run.json
    ├── stdout.log
    └── stderr.log
```

This state is versioned and disposable. It never replaces Git, Spec Kit tasks, V3 leases or Git history.

## Process identity and PID reuse

A persisted PID alone is unsafe across independent CLI invocations because a dead PID may later be reused. On Linux, V5 records `/proc/<pid>/stat` start time together with the PID. Stop operations compare the current fingerprint and fail closed on mismatch. Where a safe identity cannot be verified, destructive signaling is refused rather than guessing.

## Process groups

Children start in a new session/process group. Graceful stop targets the group so agent subprocess trees do not outlive the recorded run. Force escalation remains explicit.

## State semantics

Proposed states:

- `running`: verified process identity is alive;
- `succeeded`: observed exit code `0`;
- `failed`: observed non-zero exit code;
- `stopped`: runner requested and observed termination;
- `orphaned`: persisted process disappeared and exit code is unavailable;

No state means Task completion. Canonical task status remains authored in `tasks.md` based on implementation/review evidence.

## Exit-code limitation

A detached process exit code cannot always be recovered after the launcher process has exited unless an intermediary records it. V5 therefore launches a tiny local wrapper process that executes the requested argv and atomically writes an exit-result file before terminating. The wrapper is engineering infrastructure, not an agent or authority source.

## Security boundary

The runner inherits the operator process environment so existing local agent authentication can work, but it never persists environment values. Secrets must not be passed in argv because argv is intentionally recorded for observability.

## Deferred

- wave scheduling/supervision;
- retries/backoff policies;
- automatic validation execution;
- commit/push/PR/merge;
- distributed runners;
- remote execution;
- canonical task mutation.
