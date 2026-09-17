# Quickstart: Git Publisher V8

## Prerequisites

A task must still have its active V3 allocation and a passed V7 validation record whose workspace fingerprint still matches the allocated worktree.

```bash
graph-engineering validation-status --validation <VALIDATION-ID> --json
```

## Publish

```bash
graph-engineering publication-run <TASK-ID> \
  --validation <VALIDATION-ID> \
  --commit-message "feat: implement task" \
  --pr-title "feat: implement task" \
  --pr-body "Implements the validated task." \
  --base master \
  --json
```

V8 stages the validated workspace, creates one commit, pushes the allocation branch without force and opens a GitHub PR. It does not merge it.

## Inspect

```bash
graph-engineering publication-status --task <TASK-ID> --json
graph-engineering publication-status --publication <PUBLICATION-ID> --json
```

## Resume

If push or PR creation fails after commit:

```bash
graph-engineering publication-resume <PUBLICATION-ID> --json
```

Resume requires the recorded branch/commit/worktree identity to remain intact and never creates a duplicate commit.

## Boundary

A successful V8 publication does not mark the Task complete, release the execution lease, remove the worktree, approve/merge the PR or mutate Neo4j. Those remain explicit human/future-policy actions.
