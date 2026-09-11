# Requirements Checklist: Execution Graph

**Feature**: `SPEC-011-EXECUTION-GRAPH`  
**Date**: 2026-09-11

## Authority and boundaries

- [x] Git/Markdown/code/tests remain canonical.
- [x] Neo4j remains a rebuildable engineering projection.
- [x] Execution manifests/leases/worktree metadata are explicitly derived.
- [x] Product runtime remains independent of graph/execution tooling.
- [x] GraphRAG/embeddings/semantic inference are excluded.
- [x] Automatic commit/push/PR/merge is excluded.

## Planning

- [x] Manifest is revision-bound and versioned.
- [x] READY/BLOCKED/cycles/conflicts/waves are included.
- [x] Existing V1 planner is reused instead of duplicated.
- [x] Conflict-safe wave behavior is deterministic.
- [x] Source-revision drift fails closed.

## Worktrees

- [x] One deterministic branch/worktree per task.
- [x] Git worktree primitives are used instead of directory copies.
- [x] Existing foreign path/branch allocations fail closed.
- [x] Dirty worktree deletion requires explicit force.
- [x] Worktree state is derived but dirty contents are treated as user data.

## Leases

- [x] Local registry is versioned and repository-scoped.
- [x] Active task/branch/path collisions are prevented.
- [x] Malformed registry fails closed.
- [x] Writes use temporary-file replacement.
- [x] Release does not mutate canonical Task status.

## Context / agents

- [x] V2 `ContextPackage` is reused.
- [x] Strict freshness is required before active allocation.
- [x] Codex/Claude choice does not alter execution semantics.
- [x] Handoffs point back to canonical files.
- [x] Long-running agent process supervision is not required by V3.

## Validation

- [x] Unit coverage planned for manifest, leases, selection and revision checks.
- [x] Real temporary Git repository coverage planned for worktree lifecycle.
- [x] Engineering Graph CI will exercise V3 while preserving V1/V2 smokes.
- [x] Spec Kit and product CI remain independent gates.

## Result

PASS — design is internally consistent and stays within the formal V3 roadmap boundary.