# Execution Graph Architecture

## Purpose

The Execution Graph is V3 of the repository Engineering Graph roadmap. V1 models dependency/readiness/conflict relationships; V2 packages task context reproducibly; V3 composes those capabilities into revision-bound execution waves and isolated Git worktree allocations.

The product runtime is unchanged. Neo4j, manifests, context packages, leases and worktree metadata remain engineering-only tooling.

## Authority model

```text
Canonical
Git / Specs / ADRs / Code / Tests / Git history
                 │
                 ▼
Derived
Engineering Graph (Neo4j)
                 │
          ┌──────┴──────┐
          ▼             ▼
   V1 planner       V2 ContextPackage
          │             │
          └──────┬──────┘
                 ▼
        ExecutionManifest
                 │
                 ▼
      worktree + local lease
                 │
                 ▼
       ExecutionAllocation
                 │
                 ▼
          agent handoff
```

Authority always points upward. An active lease is not task completion.

## Planning

`execution-plan` loads projected Tasks using the existing V1 planner. It does not implement a second DAG/conflict engine.

The manifest contains:

- repository/source revision;
- selected Spec;
- agent adapter metadata;
- READY tasks;
- BLOCKED tasks + blockers;
- dependency cycles;
- shared-artifact conflicts;
- ordered conflict-free waves.

Wave calculation inherits V1 rules: dependencies must be satisfied and tasks sharing implementation/test artifacts are serialized.

## Revision binding

Before planning, V3 compares projected Task `sourceRevision` values with current Git HEAD when projection revision evidence is available. Preparation always requires:

```text
manifest.sourceRevision == git HEAD
context.sourceRevision  == manifest.sourceRevision
context freshness       == current
```

Any mismatch requires graph sync/replanning.

## Worktree allocation

Deterministic defaults:

```text
Task:   SPEC-011-EXECUTION-GRAPH:T021
Branch: exec/spec-011-execution-graph-t021
Path:   engineering-graph/.execution/worktrees/spec-011-execution-graph-t021
```

Creation uses Git worktree primitives. Existing expected worktrees can be resumed when no active lease exists. A branch checked out elsewhere or a foreign path collision fails closed.

## Lease registry

Default:

```text
engineering-graph/.execution/leases.json
```

The registry is:

- versioned;
- repository-scoped;
- local to one checkout/orchestrator domain;
- written via temporary-file replacement;
- validated for unique active task/branch/path ownership.

It is not a distributed lock and is not synchronized into Neo4j as canonical state.

## Context/handoff preparation

Preparation reads each selected task through the existing V2 Context Builder, strictly validates freshness, and writes:

```text
engineering-graph/.execution/contexts/<task-safe>/
├── context.json
├── context.md
└── codex.md | claude.md
```

The agent adapter does not change worktree paths, branch names, wave composition or task selection.

## Mutation order

```text
validate manifest/revision
        ↓
validate wave/task selection
        ↓
check active leases
        ↓
build + strictly validate V2 packages
        ↓
write derived context/handoff
        ↓
create/resume Git worktree
        ↓
acquire active lease
        ↓
return ExecutionAllocation
```

If preparation fails after creating new derived worktrees, V3 rolls back only worktrees it created and only when they remain clean. Existing/resumed user work is not deleted.

## Dry run

`execution-prepare --dry-run` performs graph/context reads and freshness checks, computes deterministic allocation metadata, but does not create worktrees or active leases.

## Release

`execution-release` defaults to lease release only. Worktree removal is explicit. A dirty worktree fails closed unless `--force` is supplied.

Branches are preserved by worktree removal, allowing history/resume semantics without destructive branch deletion.

## Failure modes

### Dependency cycle

Manifest can be inspected but preparation is rejected.

### Cross-wave explicit selection

Rejected so callers cannot bypass dependency/conflict safety.

### Stale manifest/context

Rejected before active allocation.

### Active lease collision

Rejected with existing task/branch/path ownership evidence.

### Foreign worktree/path collision

Rejected rather than overwritten.

### Dirty worktree cleanup

Rejected unless explicit force.

### Neo4j unavailable

Execution planning/context preparation degrades; product runtime remains unaffected.

## Agent runner seam

`ExecutionAllocation` exposes everything a future runner needs:

- task ID;
- source revision;
- branch;
- worktree path;
- context path;
- handoff path;
- validation commands.

V3 deliberately stops before long-running agent supervision, commit, push, PR or merge automation.

## Future extension

V4 GraphRAG may enrich V2 retrieval before ContextPackage assembly. A later runner may consume V3 allocations for process lifecycle. Neither future layer may invert the authority model or make Neo4j/generated state canonical.