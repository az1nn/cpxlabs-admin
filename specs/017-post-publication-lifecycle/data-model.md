# Data Model: Post-Publication Lifecycle V9

## PostPublicationReceipt

Versioned derived record persisted under `.execution/post-publication/receipts/<publication-id>.json`.

Fields:

- `receiptVersion`
- `receiptId`
- `repository`
- `publicationId`
- `validationId`
- `taskId`
- `specId`
- `branch`
- `baseBranch`
- `prUrl`
- `prNumber`
- `mergeCommitSha`
- `baseRevision`
- `canonicalTaskPath`
- `canonicalTaskCompleted`
- `leaseReleased`
- `worktreeRemoved`
- `status` = `reconciled | finalized | blocked`
- `blockReason`
- `createdAt`
- `updatedAt`
- `finishedAt`

Receipts are operational evidence only and never replace Spec Kit/Git truth.

## ReconciliationResult

Read-only transient result:

- publication identity;
- PR state/merge evidence;
- base branch/revision;
- merge reachability;
- canonical Task evidence;
- lease identity/state;
- worktree registered/dirty state;
- `finalizable: bool`;
- blocking reasons.

## HumanAsyncGate

Documentation/review contract rather than runtime canonical state:

- `gateId`
- `subject`
- `triggerEvidence`
- `expectedObservation`
- `approver`
- `status`: `PENDING | PASSED | FAILED | WAIVED`
- `rationale`
- `freshnessBoundary`
- `nextAction`

## ContinuationPrompt

Reusable operational prompt containing:

- repository;
- base branch;
- active branch;
- PR;
- HEAD;
- Spec Kit ID;
- current gate states;
- exact next action;
- freshness command/requirement;
- authority reminder.
