# ADR-0025: Post-Publication and Human Async Gate Boundary

**Status**: Accepted

## Context

V8 can publish validated work and open a pull request, but intentionally stops before review/merge. After a human merge, local execution state may still contain an active lease and generated worktree. Separately, AI-assisted sessions need a durable way to represent required asynchronous/manual validation that cannot be asserted synchronously by CI.

## Decision

1. Introduce V9 as a post-publication reconciliation/finalization layer.
2. V9 consumes one terminal V8 publication record and matching active V3 allocation.
3. V9 may inspect GitHub PR state but may not approve, merge, close, or enable auto-merge.
4. V9 requires the PR to be merged and its merge commit to be reachable from a refreshed configured base branch.
5. V9 does not infer canonical Task completion. It reads the merged base Spec Kit `tasks.md` and requires the matching Task to already be checked complete.
6. If canonical completion is absent or ambiguous, finalization stops; V9 must not edit the checkbox on behalf of runtime/publication evidence.
7. Lease release requires explicit operator intent. Worktree removal requires additional explicit intent and a clean matching worktree.
8. V9 persists only derived local receipts under `.execution/`; those receipts are not canonical project state and are not projected into Neo4j truth.
9. Required asynchronous/manual acceptance checks are modeled as Human Async Gates with explicit status and freshness boundary.
10. A required Human Async Gate in `PENDING` state blocks claims of final readiness/completion even when automated CI is green.
11. CI and Human Async Gates are independent evidence classes; neither silently satisfies the other.
12. Whenever work pauses, hands off, or waits for external/human evidence, the agent emits a current Continuation Prompt containing repository, branch/PR/HEAD/spec, gate state, one exact next action, and freshness instructions.

## Consequences

### Positive

- post-merge cleanup cannot erase work before canonical completion is visible in Git;
- human merge authority remains explicit;
- dirty worktree contents remain protected;
- lifecycle finalization is auditable and idempotent;
- asynchronous human validation is visible rather than hidden in prose;
- a new chat/turn can continue from an exact prompt without reconstructing stale narrative context.

### Trade-offs

- canonical Task completion must already be merged before cleanup can finish;
- some workflows may require a follow-up canonical change before lease/worktree cleanup;
- human gate status must be maintained explicitly;
- V9 remains GitHub-specific because it consumes V8 GitHub publication evidence.

## Rejected alternatives

### Mark the Task complete automatically after PR merge
Rejected because merge proves integration, not that runtime evidence is authorized to mutate Spec Kit truth.

### Release leases immediately when a PR merges
Rejected because the merged base may still lack canonical Task completion or may not yet contain the expected merge commit locally.

### Force-remove dirty worktrees
Rejected because dirty contents are user/work data and cleanup must fail closed.

### Treat green CI as satisfying manual/async acceptance
Rejected because automated and human evidence can validate different properties and have different freshness boundaries.

### Emit only a generic “continue” message
Rejected because it does not preserve the exact repository/gate/next-action state required for safe continuation.
