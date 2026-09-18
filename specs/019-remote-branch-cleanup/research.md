# Research: Remote Branch Cleanup V11

## Problem

V9 intentionally excluded remote branch deletion because it adds destructive Git authority. V10 then added the missing read-only lifecycle projection so operators can see what is actually proven before advancing authority. With V10 merged, the next narrow post-lifecycle gap is stale remote feature branches left after a publication is merged and canonical completion is proven.

The design must add only the minimum authority required to remove one exact remote head and must fail closed under stale evidence or races.

## Decision 1 — V11 is a separate authority tier after V9 finalization

**Decision**: Remote branch cleanup requires matching terminal V8 publication evidence and finalized V9 post-publication evidence.

**Rationale**: V8 owns publication identity; V9 proves human merge, base reachability, canonical Task completion and local lease cleanup. Remote deletion must not re-infer those facts from weaker evidence.

**Alternatives considered**:

- Delete immediately after V8 PR merge: rejected because PR merge alone does not prove canonical Task completion or local cleanup.
- Fold deletion into V9: rejected because V9 deliberately froze with a smaller mutation boundary and is already converged.
- Let V10 delete: rejected because V10 is explicitly read-only.

## Decision 2 — Publication identity, not operator input, selects the branch

**Decision**: The deletion target comes from the V8 publication branch and exact publication commit SHA. Operator input can select the publication record but cannot substitute an arbitrary remote branch.

**Rationale**: This prevents a generic branch-deletion surface from emerging accidentally.

**Alternatives considered**:

- Accept `--branch`: rejected because typo or hostile input could widen mutation authority.
- Delete every merged branch: rejected because batching makes evidence isolation and recovery materially harder.

## Decision 3 — Guard deletion with expected-SHA compare-and-swap

**Decision**: The mutation must be conditional on the remote head still equaling the V8 publication commit SHA at mutation time.

**Rationale**: A separate read followed by an unconditional delete has a time-of-check/time-of-use race. Expected-SHA protection turns a concurrent branch update into a safe failure.

**Candidate mechanism**: an argv-only Git push using an exact deletion refspec plus `--force-with-lease=refs/heads/<branch>:<expected-sha>`, after read-only exact-ref inspection. This is a compare-and-swap guard, not permission to fall back to unconditional force.

**Alternatives considered**:

- `git push origin --delete <branch>` after `ls-remote`: rejected because the ref can change after inspection.
- GitHub ref DELETE API after inspection: rejected for the first implementation because the standard delete endpoint does not itself carry the expected-old-SHA precondition needed by this contract.
- Server-side protection bypass: rejected.

## Decision 4 — Status is separate and strictly read-only

**Decision**: Provide `remote-cleanup-status` before any mutation command.

**Rationale**: Destructive actions must not be required to discover blockers. Status can be consumed by humans, SIGA continuation and V10/V11 lifecycle projection.

## Decision 5 — Local ownership must be closed

**Decision**: A matching active lease blocks cleanup. A matching registered worktree/local execution ownership that would make remote deletion unsafe also blocks cleanup. V11 never removes the worktree or releases the lease itself.

**Rationale**: Remote deletion must not invalidate an active local execution context or broaden V11 into another local cleanup tier.

## Decision 6 — Already absent is idempotent success, conflicting recreation is not

**Decision**: If the exact branch is absent before any V11 deletion, report `already_absent` without mutation. After V11 records a successful deletion, a later recreation of the same branch is a conflict requiring human/operator review; the old receipt must not authorize deleting the recreated branch.

**Rationale**: Absence is harmless, but recreation is new state and may represent new work.

## Decision 7 — Receipts are derived audit/recovery evidence

**Decision**: Persist versioned receipts beneath `.execution/remote-cleanup/` only for mutation attempts/outcomes. Read-only status writes nothing.

**Rationale**: Idempotency and recovery need durable local evidence, but Git/Spec Kit remain canonical.

## Human Async Gate classification

No required Human Async Gate is planned for V11. Exact-ref targeting, race protection, read-only behavior and idempotency are synchronously testable. If implementation introduces a validation condition that depends on later human/external observation, that gate must be added explicitly rather than inferred from CI.
