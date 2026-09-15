# Data Model: Git Publisher V8

## PublicationRecord

Derived local record persisted under `.execution/publication/records/<publication-id>.json`.

Fields:

- `publicationVersion`
- `publicationId`
- `repository`
- `taskId`
- `specId`
- `validationId`
- `runId`
- `sourceRevision`
- `workspaceRevision`
- `workspaceFingerprint`
- `branch`
- `baseBranch`
- `worktreePath`
- `commitMessage`
- `prTitle`
- `prBody`
- `status`: `started | committed | pushed | pr_opened | failed`
- `lastSuccessfulPhase`: optional `preflight | commit | push | pr`
- `commitSha`: optional until commit succeeds
- `prUrl`: optional until PR creation succeeds
- `failedPhase`: optional
- `error`: optional sanitized process error
- `createdAt`
- `updatedAt`
- `finishedAt`: optional

## Invariants

1. `committed`, `pushed`, `pr_opened` require `commitSha`.
2. `pr_opened` requires `prUrl` and no failure fields.
3. `failed` requires `failedPhase` + error.
4. Validation identity fields are immutable across resume.
5. Credentials/environment values are never serialized.
6. Records are disposable derived evidence, not canonical state.
