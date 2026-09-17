# Quickstart: Post-Publication Lifecycle V9

## Read-only reconciliation

```bash
graph-engineering post-publication-status \
  --publication <PUBLICATION_ID> \
  --json
```

This must not release leases or remove worktrees.

## Explicit finalization

Release the matching lease after merge and canonical Task completion are proven:

```bash
graph-engineering post-publication-finalize \
  --publication <PUBLICATION_ID> \
  --release-lease \
  --json
```

Also remove the generated worktree only when it is clean:

```bash
graph-engineering post-publication-finalize \
  --publication <PUBLICATION_ID> \
  --release-lease \
  --remove-worktree \
  --json
```

V9 does not provide a force-delete path for dirty worktrees.

## Human Async Gate

When a required test depends on later human/external observation, document it explicitly:

```text
Gate ID: HAG-001
Subject: production smoke after propagation
Trigger / evidence: deployment <id/url>
Expected observation: login + core dashboard journey succeeds
Approver: human operator
Status: PENDING
Freshness boundary: build <sha>
Next action: after PASSED, proceed to final merge/release gate
```

A required `PENDING` gate blocks claims of final readiness/completion even when CI is green.

## Continuation Prompt

Whenever work pauses or waits on a gate, emit a ready-to-paste prompt containing current repository/branch/PR/HEAD/spec, unresolved gates, and one exact next action. Regenerate it after repository or gate state changes.
