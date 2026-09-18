# ADR-0027: Remote Branch Cleanup Authority Boundary

## Status

Proposed

## Context

V8 publishes an exact validated workspace and opens/reuses one pull request. V9 verifies human merge, base reachability and canonical Task completion, then performs only explicitly requested local lease/worktree cleanup. V10 is intentionally read-only and projects the lifecycle across those evidence tiers.

Remote feature branches can remain after that lifecycle is complete. Deleting them is useful repository hygiene, but it is a destructive Git mutation and was intentionally excluded from V9. Adding a generic branch-delete command would exceed the existing authority model and create race/identity hazards.

## Decision

Introduce V11 as a separate, narrow post-finalization authority tier.

V11 may:

- read one terminal V8 publication record;
- read one matching finalized V9 receipt;
- inspect current local lease/worktree ownership;
- inspect exactly one remote head derived from the publication branch;
- compare the remote head with the exact publication commit SHA;
- under explicit operator intent, delete that exact remote head only with expected-SHA compare-and-swap protection;
- persist derived cleanup receipts for idempotency/audit;
- expose derived status to the lifecycle coordinator.

V11 may not:

- accept arbitrary branch identity as deletion authority;
- delete the base/default branch;
- delete local branches, tags, sibling refs, worktrees or leases;
- approve/merge/close PRs;
- change branch protection/rulesets;
- fall back to an unconditional delete when the expected-SHA guard fails;
- edit Spec Kit Task state;
- turn cleanup receipts into Neo4j or canonical Task truth.

## Guarded deletion

A read-only exact-ref inspection precedes mutation. The mutation itself must still carry the expected old SHA so that a concurrent remote update fails instead of being deleted.

The first implementation will use Git's lease-style compare-and-swap semantics with an exact deletion refspec and argv-only process execution. The word "force" in `--force-with-lease` does not authorize unconditional force: the expected SHA is mandatory and failure must stop the operation.

## Idempotency

If the branch is already absent before V11 mutation, cleanup is terminal without issuing a delete. If V11 previously deleted the branch and a branch with the same name later reappears, the old receipt does not authorize deleting the recreated ref.

## Consequences

Positive:

- repository hygiene can be automated without widening to generic ref deletion;
- races fail closed;
- continuation agents can distinguish pending remote cleanup from completed lifecycle work;
- V8/V9 authority remains intact.

Costs:

- V11 adds another derived receipt and CLI surface;
- lifecycle projection may require a versioned extension;
- protected-branch/server-policy failures remain operator-visible blockers rather than being bypassed.

## Alternatives Rejected

- Add deletion to V9 after convergence: rejected because it changes a frozen authority boundary.
- Let V10 perform cleanup: rejected because V10 is explicitly read-only.
- Use unconditional `git push --delete` after inspection: rejected because of TOCTOU risk.
- Batch-delete all merged branches: rejected because evidence and recovery are harder to isolate.
