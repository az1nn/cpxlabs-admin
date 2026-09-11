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

1. `git worktree add <path> -b <branch> <start-point>` creates a new branch and worktree for a fresh allocation.
2. A branch already checked out in another worktree cannot normally be checked out again; V3 treats that as an allocation collision.
3. Worktree removal must not destroy dirty/untracked user work silently.
4. `git worktree list --porcelain` provides machine-readable existing allocation evidence.
5. Worktrees are local operational state and must not become canonical Spec/Task status.

## Branch naming

Canonical task IDs can contain `:` and other separators. V3 normalizes them into a stable branch suffix.

Default:

```text
exec/<lowercase-safe-task-id>
```

Example:

```text
SPEC-011-EXECUTION-GRAPH:T021
→ exec/spec-011-execution-graph-t021
```

The allocator never silently resets an existing task branch. Existing deterministic task state follows explicit resume/collision rules:

- if the exact expected worktree path is already registered on the exact expected task branch, it can be resumed without reset;
- if the expected branch is checked out at a different path, preparation fails closed;
- if the expected path exists outside Git's worktree registry, preparation fails closed;
- if the deterministic branch exists but is not checked out, Git may attach it to the expected worktree path without rewriting its history.

This supports intentional continuation of prior task work while refusing to claim unrelated filesystem/worktree state.

## Worktree placement

Default derived root:

```text
engineering-graph/.execution/worktrees/
```

Lease/manifest/context state:

```text
engineering-graph/.execution/
├── leases.json
├── manifests/
├── contexts/
└── worktrees/
```

This root must be Git-ignored. The metadata is engineering-only and disposable except that dirty/uncommitted content inside a worktree is user data and cannot be treated as disposable.

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

The registry is written via temporary-file replacement to reduce partial-write risk. Malformed registry JSON fails closed.

Dry-run allocations use `planned` in returned metadata but do not become active persisted leases. Persisted execution ownership uses `active`; release records `released` history.

## Planning vs mutation boundary

V3 separates a pure planning command from worktree mutation:

```text
execution-plan    → no Git worktree/lease mutation
execution-prepare → branch/worktree + context/handoff + lease
execution-release → lease release + optional safe worktree removal
execution-status  → inspect local derived allocations
```

This keeps reviewable deterministic evidence before any filesystem/Git mutation.

## Source revision race

An execution manifest is valid only for the Git revision from which it was generated. Preparation compares current `git rev-parse HEAD` with `manifest.sourceRevision` before allocating worktrees.

Before worktree mutation, V2 context is regenerated and strict freshness checked against the same repository revision. The revision is checked again before each allocation mutation. If HEAD changes, preparation fails; rollback is limited to newly created clean derived state.

## Agent boundary

The worktree allocator is vendor-neutral. `agent=codex|claude` is bound in the manifest and selects only which V2 handoff is associated with the allocation.

V3 does not supervise a long-running agent process. `ExecutionAllocation` is the clean seam a later runner can consume without changing planning/context contracts.

## Failure modes

### Dependency cycle

No wave preparation. Planner returns cycle evidence and non-zero CLI status.

### Shared artifact conflict

Planner serializes conflicting tasks into separate waves.

### Existing active lease

Preparation fails with the existing allocation metadata. No duplicate worktree ownership.

### Existing deterministic task worktree

The exact expected path/branch can be resumed without reset when no active lease exists. Foreign path/branch ownership remains a hard collision.

### Dirty worktree on release

Normal removal refused. `--force` is required for destructive cleanup.

### Neo4j unavailable

Planning/context preparation fails as engineering tooling only. Product runtime remains unaffected.

### Stale context or manifest

Preparation fails before reporting allocation ready.

## Decision

Implement V3 as a deterministic local execution orchestration layer over the V1 planner and V2 context package. Use Git worktrees for isolation, a local JSON lease registry for collision protection, and explicit plan/prepare/status/release CLI commands. Keep agent supervision, commits, pushes, PR/merge automation and GraphRAG out of scope.