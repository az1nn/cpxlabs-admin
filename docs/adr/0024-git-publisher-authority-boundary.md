# ADR-0024: Git Publisher Authority Boundary

**Status**: Accepted

## Context

V7 produces stable-workspace validation evidence but deliberately cannot publish Git state. Commit, push and pull-request creation mutate shared collaboration history and therefore require a distinct authority tier with explicit recovery semantics.

## Decision

Introduce V8 Git Publisher with these boundaries:

1. V8 consumes one explicit passed V7 validation record for one active V3 allocation.
2. Current worktree revision/fingerprint must exactly equal V7 evidence before any Git mutation.
3. V8 may stage the validated workspace and create one local commit.
4. V8 may push only the allocation branch to verified `origin` without force.
5. V8 may create one GitHub PR using authenticated `gh` argv with explicit base/head/title/body.
6. V8 persists derived phase state so post-commit failures can be resumed without duplicate commits.
7. Resume after commit requires exact recorded commit HEAD plus clean worktree; it never rewinds or force-pushes history.
8. V8 never merges, approves, enables auto-merge or closes the PR.
9. V8 never marks a Spec Kit Task complete, releases leases, removes worktrees, edits canonical specs/ADRs as a consequence of runtime state, or projects publication records into Neo4j.
10. Credentials are inherited from environment only and are never serialized.

## Consequences

### Positive

- validated workspace evidence is connected to publication without implicit authority escalation;
- stale workspaces cannot be published through V8;
- partial network/provider failures are recoverable without duplicate commits;
- shared history cannot be overwritten by V8 force-push behavior;
- human review/merge remains a clear authority boundary.

### Trade-offs

- GitHub CLI authentication is an external prerequisite;
- publication may stop after local commit or remote push and require explicit resume;
- V8 does not automate final Task/lease cleanup after merge;
- V8 is GitHub-specific rather than a provider abstraction.

## Rejected alternatives

### Add commit/push/PR to V7
Rejected because validation evidence and shared-history mutation have different authority and recovery semantics.

### Force-push on retry
Rejected because recovery must not overwrite remote history.

### Merge after PR creation
Rejected because publication evidence does not equal review approval or merge authority.

### Mark Task complete when PR opens
Rejected because PR existence does not prove review, merge or canonical completion.
