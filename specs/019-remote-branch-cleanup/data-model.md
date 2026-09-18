# Data Model: Remote Branch Cleanup V11

All models are derived control-plane evidence. None is canonical Task truth.

## RemoteBranchIdentity

Represents the only remote ref V11 is allowed to inspect/delete.

Fields:

- `repository`
- `remote`
- `branch`
- `fullRef` = exact `refs/heads/<branch>`
- `expectedSha` = exact V8 publication commit SHA
- `baseBranch`
- `defaultBranch` when available
- `publicationId`
- `specId`
- `taskId`

Validation:

- repository/publication/spec/task/branch must match V8/V9 evidence;
- target branch differs from base/default branch;
- expected SHA is present and well-formed;
- full ref is constructed from validated publication branch identity, never arbitrary shell text.

## RemoteCleanupAssessment

Read-only result.

Fields:

- `assessmentVersion`
- `identity: RemoteBranchIdentity`
- `v9Finalized`
- `activeLease`
- `matchingWorktreeState`
- `remoteState`: `present | absent | unavailable | conflict`
- `observedSha`
- `ready`
- `terminalWithoutMutation`
- `blockers[]`
- `nextAction`
- `observedAt`

Invariants:

- `ready=true` only when current remote SHA equals expected SHA and all prerequisite/local-ownership guards pass;
- `remoteState=absent` yields an idempotent terminal assessment, not `ready=true`;
- mismatch never becomes ready.

## RemoteCleanupReceipt

Persisted only after explicit finalization/mutation handling.

Fields:

- `receiptVersion`
- `receiptId`
- repository/publication/spec/task identity
- `remote`
- `branch`
- `expectedSha`
- `observedShaBefore`
- `outcome`: `deleted | already_absent | blocked | failed`
- `blockReason` / `error` when applicable
- `createdAt`
- `updatedAt`
- `finishedAt`

Invariants:

- `deleted` requires proof that the guarded mutation completed successfully;
- `already_absent` contains no successful delete invocation;
- a receipt never authorizes deletion of a later branch recreation;
- receipts remain disposable/derived and can be rebuilt only from stronger Git evidence where possible.

## State transitions

```text
status only:
unknown -> ready
unknown -> already_absent
unknown -> blocked

explicit finalize:
ready -> deleted
ready -> failed
ready -> blocked (freshness changed before mutation)

retry:
deleted -> deleted (no mutation)
already_absent -> already_absent (no mutation)
blocked/failed -> re-assess fresh evidence before any new mutation
```
