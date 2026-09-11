# Research: Execution Graph

**Feature**: `SPEC-011-EXECUTION-GRAPH`  
**Date**: 2026-09-11

## Existing foundations

The repository already owns most static planning primitives required by V3:

- `planner.py` models task dependencies, detects cycles, finds shared-artifact conflicts and calculates conflict-free waves;
- `ready-tasks.cypher` and `conflicts.cypher` expose graph-side readiness/conflict evidence;
- V2 generates deterministic `ContextPackage` artifacts with strict Git revision freshness;
- Codex/Claude adapters render from the same portable package;
- Engineering Graph CI already validates Neo4j projection, package reproducibility and runtime isolation.

V3 should compose these contracts rather than invent a second planner or retrieval stack.

## Git worktree semantics

`git worktree` is the correct isolation primitive because each concurrent task receives a real Git working tree sharing repository object storage while keeping index/working-directory state isolated.

Relevant operational rules:

1. `git worktree add <path> -b <branch> <start-point>` creates a new branch and worktree atomically enough for local orchestration.
2. A branch already checked out in another worktree cannot normally be checked out again; V3 should treat that as an allocation collision.
3. Worktree removal must not destroy dirty/untracked user work silently.
4. `git worktree list --porcelain` provides machine-readable existing allocation evidence.
5. Worktrees are local operational state and must not become canonical Spec/Task status.

## Branch naming

Canonical task IDs can contain `:` and other separators. V3 should normalize them into a stable branch suffix.

Proposed default:

```text
exec/<lowercase-safe-task-id>
```

Example:

```text
SPEC-011-EXECUTION-GRAPH:T021
→ exec/spec-011-execution-graph-t021
```

The allocator must detect an existing branch and fail closed instead of silently resetting/reusing it. A future explicit resume flow can attach to an existing allocation.

## Worktree placement

Default derived root:

```text
engineering-graph/.execution/worktrees/
```

Lease/manifest state:

```text
engineering-graph/.execution/
├── leases.json
├── manifests/
└── worktrees/
```

This root must be Git-ignored. The path is engineering-only and disposable except that dirty content inside a worktree is user data and cannot be treated as disposable.

## Lease model

A local lease prevents duplicate allocation within one repository checkout/orchestrator domain. It is intentionally not a distributed lock.

Lease identity:

- repository;
- task canonical ID;
- source revision;
- agent;
- branch;
- worktree path;
- context/handoff path;
- status;
- created/updated timestamps.

The registry should be written via temporary-file replacement to reduce partial-write risk. Malformed registry JSON must fail closed.

## Planning vs mutation boundary

V3 should separate a pure planning command from worktree mutation:

```text
execution-plan   → no Git mutation
execution-prepare → branch/worktree + context/handoff + lease
execution-release → lease release + optional safe worktree removal
execution-status  → inspect local derived allocations
```

This keeps reviewable deterministic evidence before any filesystem/Git mutation.

## Source revision race

An execution manifest is valid only for the Git revision from which it was generated. Preparation must compare current `git rev-parse HEAD` with `manifest.sourceRevision` before allocating worktrees.

After worktree creation, V2 context is generated and strict freshness checked against the same repository revision. If HEAD changes during preparation, the operation should fail and clean up only newly created derived state when safe.

## Agent boundary

The worktree allocator is vendor-neutral. `agent=codex|claude` selects only which V2 handoff is associated with the allocation.

V3 does not need to supervise a long-running agent process. It may emit an operator-facing launch suggestion in the allocation metadata, but automated process spawning is deliberately left behind a clean `ExecutionAllocation` seam.

## Failure modes

### Dependency cycle

No wave preparation. Planner returns cycle evidence and non-zero CLI status.

### Shared artifact conflict

Planner serializes conflicting tasks into separate waves.

### Existing active lease

Preparation fails with the existing allocation metadata. No duplicate worktree.

### Existing branch/worktree without lease

Preparation fails closed as externally managed state; it does not guess ownership.

### Dirty worktree on release

Normal removal refused. `--force` is required for destructive cleanup.

### Neo4j unavailable

Planning/context preparation fails as engineering tooling only. Product runtime remains unaffected.

### Stale context or manifest

Preparation fails before reporting allocation ready.

## Decision

Implement V3 as a deterministic local execution orchestration layer over the V1 planner and V2 context package. Use Git worktrees for isolation, a local JSON lease registry for collision protection, and explicit plan/prepare/release CLI commands. Keep agent execution, commits, pushes, merges and GraphRAG out of scope.