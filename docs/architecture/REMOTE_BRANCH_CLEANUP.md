# Remote Branch Cleanup V11

V11 is the first post-V10 mutation tier. Its authority is deliberately narrow: after V8 publication and finalized V9 post-publication evidence, it may inspect and—only under explicit operator intent—delete the exact publication-owned remote feature branch if the remote head still equals the exact V8 publication commit SHA.

## Position in the control plane

```text
V8 PublicationRecord
        |
        v
human review / merge
        |
        v
V9 finalized receipt
  |- merge proven on refreshed base
  |- canonical Task already complete
  |- lease release explicit/completed
  |- optional local worktree cleanup
        |
        v
V10 lifecycle projection                       read-only
        |
        v
V11 remote-cleanup status                      read-only
  |- exact repository/publication/spec/task identity
  |- exact publication branch + expected SHA
  |- base/default branch exclusion
  |- active lease/worktree safety
  |- exact remote-ref inspection
        |
explicit operator intent
        |
        v
V11 guarded remote delete
  |- expected-SHA compare-and-swap
  |- exact one remote head only
  `- derived cleanup receipt
```

Git/Spec Kit remains canonical Task truth throughout. V11 evidence is repository-hygiene evidence only.

## Required evidence

A V11 assessment is scoped to one publication identity and requires:

1. a terminal V8 `PublicationRecord` with the exact feature branch and publication commit SHA;
2. a matching V9 receipt with `status=finalized`;
3. matching repository, Spec, Task, publication, PR, branch and base identities;
4. no matching active lease;
5. no local execution/worktree ownership that makes remote deletion unsafe;
6. a target branch distinct from the configured base/default branch;
7. current exact-ref remote state.

Later evidence never repairs an identity mismatch. Contradiction fails closed.

## Read-only status

`remote-cleanup-status` performs no local or remote mutation and writes no receipt.

```bash
graph-engineering remote-cleanup-status \
  --publication <PUBLICATION-ID> \
  --json
```

The target branch is derived from the V8 publication record. There is intentionally no arbitrary `--branch` deletion authority.

Status reports the remote, exact ref, expected/observed SHA, remote state, blockers, readiness and exactly one next action. An already-absent branch is terminal without mutation.

## Guarded finalization

```bash
graph-engineering remote-cleanup-finalize \
  --publication <PUBLICATION-ID> \
  --delete-remote-branch \
  --json
```

Explicit intent is mandatory. Finalize re-runs readiness immediately before mutation.

The planned Git primitive uses an exact deletion refspec plus expected-old-SHA lease semantics, equivalent in safety semantics to:

```text
git push --porcelain \
  --force-with-lease=refs/heads/<branch>:<expectedSha> \
  origin \
  :refs/heads/<branch>
```

The expected SHA is mandatory. This is compare-and-swap protection, not generic force authority. A concurrent remote change must fail without unconditional fallback.

## Explicit non-authority

V11 cannot delete arbitrary branches, base/default branches, local branches, tags or sibling refs; release leases or remove worktrees; mutate PRs; change branch policy; edit Spec Kit Task state; or write cleanup truth into Neo4j.

Remote/server policy remains authoritative. A protection/ruleset denial is a blocker, not something V11 bypasses.

## Derived receipts

Mutation outcomes live under:

```text
engineering-graph/.execution/remote-cleanup/
```

Receipts are versioned derived evidence for idempotency and recovery. Read-only status writes nothing. A successful receipt is valid only for the exact repository/remote/branch/expected-SHA identity it records.

A branch recreated after successful cleanup is new state; the old receipt does not authorize deleting it.

## Lifecycle integration

V10 remains read-only. V11 may extend lifecycle evidence/continuation output only through an explicitly versioned compatible contract. Remote cleanup never becomes canonical Task completion.

## Validation

Tests must prove exact-ref targeting, argv-only execution, zero mutation from status, expected-SHA race protection, base/default rejection, active-local-ownership blocking, unrelated-ref preservation, idempotency, recreation safety, and V1–V10 regression compatibility.

Final freeze requires Spec Kit + Engineering Graph + Product CI green on the same HEAD and no required Human Async Gate left `PENDING`.

See ADR-0027 and `specs/019-remote-branch-cleanup/`.
