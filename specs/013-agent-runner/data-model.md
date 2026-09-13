# Data Model: Agent Runner V5

## AgentRun

```text
AgentRun
- runVersion: string
- runId: string
- repository: string
- taskId: string
- specId: string
- sourceRevision: string
- agent: string
- branch: string
- worktreePath: string
- handoffPath: string
- contextPath: string
- argv: string[]
- stdinHandoff: boolean
- pid: integer | null
- processFingerprint: string | null
- processGroupId: integer | null
- status: running | succeeded | failed | stopped | orphaned
- exitCode: integer | null
- stopRequested: boolean
- stdoutPath: string
- stderrPath: string
- resultPath: string
- createdAt: ISO-8601
- startedAt: ISO-8601 | null
- finishedAt: ISO-8601 | null
- updatedAt: ISO-8601
```

## RunnerRegistry

```text
RunnerRegistry
- registryVersion: string
- repository: string
- runs: AgentRun[]
```

The registry is local derived state. At most one non-terminal run may exist for one task.

## RunnerExitResult

Written by the child wrapper:

```text
RunnerExitResult
- resultVersion: string
- runId: string
- exitCode: integer
- finishedAt: ISO-8601
```

## Identity rules

- `runId` is unique and opaque; it does not become canonical project identity.
- task/repository/revision fields are copied from the active V3 allocation.
- `processFingerprint` is OS-observed process-start identity; on Linux it is derived from `/proc/<pid>/stat` start time.
- status is execution observation, not Task status.

## Persistence rules

- `registry.json`, `run.json`, and `result.json` are written via temp-file + replace.
- logs are append/write streams owned by the wrapper/child lifecycle.
- environment values are never serialized.
- deleting the entire `runs/` subtree does not delete worktrees, branches, leases, specs, code or tests.
