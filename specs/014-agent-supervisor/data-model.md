# Data Model: Agent Supervisor V6

## SupervisorJob

Versioned derived record persisted at `.execution/supervisor/jobs/<job-id>.json`.

Required fields:

- `supervisorVersion`
- `jobId`
- `repository`
- `sourceRevision`
- `specId`
- `agent`
- `manifestPath`
- `wave`
- `argv[]`
- `stdinHandoff`
- `maxParallel`
- `maxAttempts`
- `status` (`active | settled | stopped`)
- `tasks[]`
- `createdAt`
- `updatedAt`
- `finishedAt?`

## SupervisorTask

Per-task state owned by one job:

- `taskId`
- `status` (`pending | running | succeeded | exhausted | stopped`)
- `attempts`
- `runIds[]` in launch order
- `lastRunStatus?`

`runIds[]` is the ownership proof used by stop/reconciliation. The supervisor never infers ownership from task id alone.

## State transitions

```text
pending -> running
running -> succeeded
running -> pending      (failed/orphaned and attempts remain)
running -> exhausted    (failed/orphaned and attempts exhausted)
running -> stopped      (explicit V5 stop observed)

job active -> settled   (all task states terminal)
job active -> stopped   (explicit supervisor-stop)
```

`settled` and per-task `succeeded` remain derived orchestration observations, not canonical Spec Kit task state.
