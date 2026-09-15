# Research: Git Publisher V8

## Why publication is a new authority tier

V5 process success, V6 orchestration settlement and V7 validation are derived observations. Commit/push/PR creation mutates shared canonical collaboration state. V8 therefore requires an explicit authority boundary rather than extending V7.

## Evidence choice

The strongest existing V7 contract is its exact `workspaceRevision` + `workspaceFingerprintAfter` for a `passed`, stable record. V8 should consume that record by id and recalculate the current fingerprint immediately before mutation. A stale validation is rejected rather than refreshed implicitly.

## Commit atomicity and recovery

Commit is local but changes HEAD, so post-commit retries cannot use the original V7 fingerprint directly. V8 therefore persists the commit SHA immediately after commit and treats it as the recovery anchor. Before resume, HEAD must equal that SHA and the worktree must be clean.

If commit itself fails after staging, V8 makes a best-effort `git reset --mixed HEAD` so the original pre-publication workspace representation can be validated/retried.

## Push policy

V8 uses `git push --set-upstream origin HEAD:refs/heads/<allocation-branch>` without force. Force and force-with-lease are excluded because retry safety should not overwrite remote history.

## GitHub PR provider

V8 is GitHub-specific and uses the authenticated `gh` CLI with literal argv. Tokens are inherited from the environment and never copied into records. The PR operation is create-only: no approve, merge, auto-merge, close or review mutation is part of the interface.

## Recovery states

Durable states are `started`, `committed`, `pushed`, `pr_opened`, `failed`. Failure records include a phase. Resume uses the last durable irreversible state/commit SHA and never silently rewinds shared Git history.
