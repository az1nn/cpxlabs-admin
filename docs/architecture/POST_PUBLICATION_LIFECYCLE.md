# Post-Publication Lifecycle V9

V9 closes derived execution state only after the repository proves that human merge and canonical Task completion already happened.

## Position in the control plane

```text
V3 ExecutionAllocation + lease
        |
V5 Runner
        |
V6 Supervisor
        |
V7 Validator
        |
V8 Git Publisher -> PR opened
        |
        +---- human review / merge ----+
                                      |
                                      v
                         V9 post-publication reconcile
                         |  PR merged?
                         |  merge in refreshed base?
                         |  canonical Task checked done?
                         |  publication/lease identity valid?
                         v
                    explicit finalize
                    | release matching lease
                    + optional clean worktree removal
```

V9 is not a Task-status engine. A merged PR is integration evidence, not permission for derived runtime state to rewrite `tasks.md`.

## Read-only reconciliation

`post-publication-status` performs no lease/worktree mutation. It:

1. loads one terminal V8 `PublicationRecord`;
2. verifies repository/publication identity;
3. inspects the exact GitHub PR with `gh pr view` using argv and `shell=False`;
4. requires merged state and merge commit SHA;
5. refreshes the configured base branch from `origin`;
6. proves the merge SHA is an ancestor of the refreshed base;
7. reads the canonical Spec Kit `tasks.md` from that base revision via `git show`;
8. requires exactly one matching checked Task ID;
9. verifies the active lease matches repository/spec/branch/worktree unless a prior V9 receipt proves that lease release already happened;
10. reports worktree registration/dirty state and blockers.

## Explicit finalization

`post-publication-finalize` requires `--release-lease`.

Worktree removal additionally requires `--remove-worktree`. There is intentionally no force flag in V9.

```bash
graph-engineering post-publication-finalize \
  --publication <ID> \
  --release-lease \
  --remove-worktree
```

If the worktree is dirty, V9 may have already released the lease but persists a `blocked` receipt and refuses destructive removal. A later retry may continue cleanup after the worktree becomes safe. That retry is idempotent: prior lease release authorizes only the already-completed lease phase; merge reachability and canonical Task evidence are still revalidated.

## Derived receipt

Receipts live under:

```text
engineering-graph/.execution/post-publication/receipts/<publication-id>.json
```

They record merge/canonical evidence and which cleanup phases have already executed. They are disposable orchestration evidence, not canonical project knowledge and not Neo4j truth.

## Human Async Gates

Human review/acceptance that cannot be synchronously asserted is modeled separately through `docs/ai/human-async-gates.md`.

A required `PENDING` Human Async Gate blocks final readiness/completion claims even when automated CI is green. Automated async CI that is simply still running is an automated pending gate, not automatically a Human Async Gate.

V9 itself does not create or approve human gates. It preserves the authority boundary so PR merge, Task completion evidence and cleanup intent stay explicit.

## Continuation Prompt

Every material pause/handoff emits a fresh Continuation Prompt using `docs/ai/continuation-prompt-template.md`. The prompt is derived context and must be regenerated after HEAD/PR/CI/gate state changes.
