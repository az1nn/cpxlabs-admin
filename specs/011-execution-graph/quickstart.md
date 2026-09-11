# Quickstart: Execution Graph

## Prerequisites

- repository checkout on the intended source revision;
- Engineering Graph Python package installed;
- Neo4j available and synchronized;
- `graph-engineering validate` passing.

## 1. Plan execution

```bash
graph-engineering execution-plan \
  --spec SPEC-011-EXECUTION-GRAPH \
  --agent codex \
  --output engineering-graph/.execution/manifests/spec-011.json
```

Inspect the manifest before mutation. It records the source revision, READY/BLOCKED state, conflicts and dependency-safe waves.

## 2. Dry-run one wave

```bash
graph-engineering execution-prepare \
  engineering-graph/.execution/manifests/spec-011.json \
  --wave 1 \
  --dry-run \
  --json
```

Dry-run reads graph/context data but does not create worktrees or active leases.

## 3. Prepare the wave

```bash
graph-engineering execution-prepare \
  engineering-graph/.execution/manifests/spec-011.json \
  --wave 1
```

For every selected task, V3:

1. verifies manifest revision equals current Git HEAD;
2. rebuilds the V2 `ContextPackage`;
3. strictly validates context freshness;
4. creates/resumes the deterministic task worktree;
5. writes the selected agent handoff;
6. acquires a local active lease.

Default derived state:

```text
engineering-graph/.execution/
├── leases.json
├── manifests/
├── contexts/
└── worktrees/
```

## 4. Inspect active allocations

```bash
graph-engineering execution-status
```

JSON mode:

```bash
graph-engineering execution-status --json
```

## 5. Work from the allocated worktree

Open the `worktreePath` and read the generated `handoffPath` / `contextPath`. The generated artifacts are navigation aids only; canonical repository files remain authoritative.

The allocation does not mark the Task complete. Task status changes belong in canonical `tasks.md`, then Graph Sync projects them.

## 6. Release

Release the lease but preserve worktree:

```bash
graph-engineering execution-release SPEC-011-EXECUTION-GRAPH:T001
```

Release and remove a clean worktree:

```bash
graph-engineering execution-release SPEC-011-EXECUTION-GRAPH:T001 --remove-worktree
```

Dirty worktrees fail closed. Destructive cleanup requires explicit force:

```bash
graph-engineering execution-release SPEC-011-EXECUTION-GRAPH:T001 \
  --remove-worktree \
  --force
```

## Revision drift

If Git HEAD changes after planning, `execution-prepare` fails. Re-sync the graph and regenerate the manifest instead of bypassing freshness.

## Boundary

V3 controls planning/worktree isolation/leases. It does not automatically commit, push, create PRs, merge, modify canonical task status, or perform GraphRAG.