# ADR-0019: Execution Graph Worktree and Lease Boundary

- **Status**: Accepted
- **Date**: 2026-09-11
- **Decision owners**: cpxlabs-admin architecture
- **Related spec**: `SPEC-011-EXECUTION-GRAPH`

## Context

V1 makes task dependencies, readiness, shared-artifact conflicts and waves queryable. V2 creates revision-aware portable context packages for Codex/Claude. The V3 roadmap requires safe parallel execution and worktree allocation.

Without an explicit execution boundary, agents could share one working directory, duplicate task allocation, act on stale graph/context revisions, or confuse transient execution state with canonical task status.

## Decision

Introduce an `ExecutionManifest` and `ExecutionAllocation` boundary around Git worktrees and a local derived lease registry.

```text
V1 planner + V2 ContextPackage
            │
            ▼
     ExecutionManifest
            │
            ▼
    selected safe wave
            │
            ▼
 Git worktree + active lease
            │
            ▼
    ExecutionAllocation
            │
            ▼
      agent handoff
```

### ExecutionManifest

The manifest is pure deterministic planning evidence bound to one repository/source revision. It carries READY/BLOCKED state, cycles, conflicts and ordered waves.

### Git worktree

Each selected Task receives a deterministic branch/worktree. Git worktree primitives are the isolation mechanism; repository directories are never copied as an orchestration substitute.

### Lease registry

The local registry prevents duplicate task/branch/path allocation inside one checkout/orchestrator domain. It is versioned, repository-scoped and written under ignored engineering-only state.

A lease is operational state only. It never changes canonical Task status and is not authoritative planning data in Neo4j.

## Freshness

Preparation fails if:

- manifest source revision differs from current Git HEAD;
- a generated V2 ContextPackage is not strictly current;
- manifest repository differs from configured repository;
- task selection attempts to cross execution waves.

Replanning is required rather than bypassing revision safety.

## Agent boundary

Worktree allocation is agent/vendor neutral. Codex/Claude selection controls only which V2 handoff accompanies the allocation.

V3 does not automatically:

- commit;
- push;
- create/merge PRs;
- mark canonical Tasks done;
- supervise long-running coding-agent processes.

A future runner may consume `ExecutionAllocation` without changing planner/context contracts.

## Cleanup

Releasing a lease does not delete user work. Worktree removal is explicit. Dirty worktree removal fails unless the operator explicitly requests force.

Generated manifests, context files and lease metadata are disposable. Dirty/uncommitted worktree contents are user data and are not disposable.

## Consequences

### Positive

- deterministic safe parallelization;
- one worktree per task avoids shared index/working-directory state;
- revision drift is detected before mutation;
- duplicate allocation is blocked locally;
- agent adapters stay thin and vendor-independent;
- execution state remains auditable without becoming canonical.

### Negative

- local lease registry is not a distributed lock;
- stale/abandoned worktrees require operator cleanup;
- Git worktree lifecycle adds failure modes not present in read-only V1/V2 tooling;
- branch naming/resume semantics require discipline.

## Rejected alternatives

### Shared working directory for parallel agents

Rejected because concurrent indexes/files create nondeterministic conflict and cleanup behavior.

### Copy repository directories per task

Rejected because copies detach from Git worktree metadata, duplicate object state and make branch ownership ambiguous.

### Store lease/task execution state as canonical Neo4j data

Rejected because Neo4j is a rebuildable projection and cannot become the authoritative task/execution record.

### Automatically commit/push/merge on preparation

Rejected because V3's formal roadmap scope is parallelization/worktree allocation, not autonomous repository publication.

## Future compatibility

A later agent runner may consume `ExecutionAllocation` for process launch/supervision. V4 GraphRAG may enrich ContextPackage retrieval. Neither changes the source-of-truth direction established here.