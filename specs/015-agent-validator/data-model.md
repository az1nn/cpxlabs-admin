# Data Model: Agent Validator V7

## ValidationCommandResult

One executed frozen validation command.

| Field | Meaning |
| --- | --- |
| `index` | 1-based command order |
| `command` | Original frozen allocation command |
| `argv` | Parsed argv actually executed |
| `status` | `passed` or `failed` |
| `exitCode` | Child exit code, or null when process launch fails |
| `stdoutPath` | Derived stdout log path |
| `stderrPath` | Derived stderr log path |
| `startedAt` / `finishedAt` | Observation timestamps |
| `error` | Bounded process-launch error text when applicable |

## ValidationRecord

One complete V7 validation observation.

| Field | Meaning |
| --- | --- |
| `validationVersion` | Schema version |
| `validationId` | Unique disposable record id |
| `repository` / `taskId` / `specId` | Canonical identity references |
| `sourceRevision` | V3 allocation source revision |
| `runId` | Exact latest successful V5 run validated |
| `branch` / `worktreePath` | V3 allocation workspace identity |
| `workspaceRevision` | Git HEAD observed after validation |
| `workspaceFingerprintBefore` | SHA-256 publishable workspace fingerprint before commands |
| `workspaceFingerprintAfter` | SHA-256 publishable workspace fingerprint after commands |
| `workspaceStable` | Revision/fingerprint equality across validation |
| `status` | `passed` or `failed` |
| `commands` | Ordered `ValidationCommandResult` values actually executed |
| `createdAt` / `finishedAt` | Validation timestamps |

## State rules

`passed` requires every frozen command to have executed successfully and `workspaceStable=true`. A command failure stops the sequence. Records never mutate V3 leases, V5/V6 state, canonical task state or Git history.
