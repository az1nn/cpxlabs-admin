# Feature Specification: Git Publisher V8

**Spec ID**: `SPEC-016-GIT-PUBLISHER`
**Status**: Active

## Problem

V7 can prove that an allocated task workspace passed its frozen validation commands without drifting, but publication is still manual. Commit, push and pull-request creation have materially greater authority than execution or validation and must not be inferred from a successful runner/supervisor/validator state.

## Goal

Add a narrow, recoverable GitHub publication layer that consumes one exact fresh V7 validation record and publishes that already-validated workspace as a non-force branch + pull request without gaining merge, Task-completion, lease-cleanup or graph-authoring authority.

## User stories

### US1 — Publish a validated task safely
As an operator, I can publish one task only when its current allocated workspace exactly matches a passed V7 validation record, so the resulting commit/branch/PR corresponds to reviewed validation evidence.

### US2 — Recover partial publication
As an operator, I can resume a publication that failed after a local commit or push without force-pushing, duplicating commits, or weakening evidence checks.

### US3 — Inspect publication evidence
As an operator, I can inspect versioned local publication records that identify the validation, commit, branch and PR URL without treating those records as canonical project truth.

## Functional requirements

- **FR-001**: V8 MUST operate on exactly one active V3 allocation/task at a time.
- **FR-002**: V8 MUST require an explicit V7 `validationId` whose record is `passed` and `workspaceStable=true`.
- **FR-003**: Validation repository/task/spec/branch/worktree/source revision MUST match the active allocation.
- **FR-004**: Before any Git mutation, current worktree HEAD and `workspace_identity()` fingerprint MUST exactly match V7 `workspaceRevision` and `workspaceFingerprintAfter`.
- **FR-005**: V8 MUST refuse an empty publishable diff.
- **FR-006**: V8 MUST stage the validated workspace with argv-based Git invocation and MUST NOT invoke a shell.
- **FR-007**: V8 MUST create exactly one local commit from the validated workspace using an operator-supplied commit message.
- **FR-008**: V8 MUST verify the resulting worktree is clean and the commit parent is the V7 workspace revision.
- **FR-009**: V8 MUST push only the allocation branch to `origin`, without `--force` or force-with-lease.
- **FR-010**: `origin` MUST resolve to the configured GitHub repository identity before publication.
- **FR-011**: V8 MUST open a GitHub pull request using argv-based `gh` invocation with explicit base/head/title/body/repository.
- **FR-012**: V8 MUST NOT merge, approve, enable auto-merge, close, or otherwise resolve the created PR.
- **FR-013**: V8 MUST NOT mutate Spec Kit Task completion state, ADR/spec content, leases, worktrees or Neo4j as a consequence of publication success.
- **FR-014**: V8 MUST persist versioned disposable publication records under `.execution/publication/`.
- **FR-015**: Publication records MUST distinguish at least `started`, `committed`, `pushed`, `pr_opened`, and `failed` states.
- **FR-016**: State MUST be persisted after each irreversible publication phase so recovery can identify the exact commit/branch already created.
- **FR-017**: A failure during local commit MUST make a best-effort attempt to restore the pre-commit staging state before returning failure.
- **FR-018**: Resume from a post-commit failure MUST require current HEAD to equal the recorded commit SHA and the worktree to be clean.
- **FR-019**: Resume MUST never create a second commit when a valid recorded commit already exists.
- **FR-020**: Resume after push MUST never force-push and MUST proceed only toward PR creation.
- **FR-021**: A successful `pr_opened` publication for a validation record MUST not be duplicated automatically.
- **FR-022**: Commit message, PR title/body and base branch are operator inputs but MUST be passed as literal argv/data, never shell text.
- **FR-023**: V8 MUST fail closed when required Git/GitHub CLI binaries, allocation evidence, validation evidence, branch identity, remote identity or workspace identity are not trustworthy.
- **FR-024**: Credentials/tokens MUST be inherited from the execution environment only and MUST NOT be serialized in publication records.
- **FR-025**: Publication records are derived evidence only and MUST NOT be projected into Neo4j or treated as canonical project state.

## Success criteria

- A V7-passed unchanged workspace can become one commit, one non-force push and one open PR.
- Workspace drift between V7 and V8 prevents any commit.
- A failed push/PR can be resumed from durable local evidence without creating a duplicate commit.
- No V8 path performs merge, Task completion, lease release, worktree removal or Neo4j mutation.
- Existing V1–V7 Engineering Graph and product CI remain green.

## Non-goals

- PR review/approval/merge or auto-merge.
- Canonical Task completion.
- Automatic lease release/worktree cleanup.
- Multi-repository publication.
- Remote agent execution.
- Release/tag/package publication.
- Provider abstraction beyond GitHub for V8.
