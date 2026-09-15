# Git Publisher V8

Git Publisher V8 is a post-validation engineering layer for one active V3 allocation. It consumes one explicit passed V7 validation record and is allowed to create a local commit, publish the allocation branch, and open a GitHub pull request. It stops at PR creation.

## Authority boundary

V8 requires the current allocated worktree revision and V7 workspace fingerprint to match before the first Git mutation. Repository, task, spec, source revision, branch, and worktree identity must also match the active allocation.

After publication begins, V8 records durable derived phase state under `.execution/publication/records/`. The states are `started`, `committed`, `pushed`, `pr_opened`, and `failed`.

The local commit SHA is recorded before remote publication. Resume requires the recorded commit to remain the current clean worktree HEAD with the expected validated parent revision; this prevents a retry from creating a second commit.

Publication uses the allocation branch and verified `origin` repository. Remote history rewriting is not part of V8. PR creation first checks whether the same head/base pair already has an open PR so recovery does not duplicate provider state.

## Non-goals

V8 does not merge or approve pull requests, mark Spec Kit tasks complete, release execution leases, remove worktrees, alter Neo4j, publish releases/tags, or infer canonical project state from publication records.

See ADR-0024 and `specs/016-git-publisher/`.
