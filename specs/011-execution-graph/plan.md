# Implementation Plan: Execution Graph

**Feature**: `SPEC-011-EXECUTION-GRAPH`  
**Branch**: `feat/011-execution-graph`

## Architecture

V3 composes the existing V1 planner and V2 context package into an execution lifecycle:

```text
Neo4j task projection
       │
       ▼
existing planner.py
       │
       ▼
ExecutionManifest
       │
       ├── validate sourceRevision
       ├── select wave/tasks
       └── detect active lease/external worktree
                     │
                     ▼
              WorktreeAllocator
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
  V2 ContextPackage       Git worktree
          │                     │
          ▼                     │
  Codex/Claude handoff          │
          └──────────┬──────────┘
                     ▼
            ExecutionAllocation
                     │
                     ▼
                LeaseRegistry
```

## New modules

### `execution.py`

Pure execution-domain contracts:

- `ExecutionManifest`;
- `ExecutionWave`;
- `ExecutionAllocation`;
- semantic JSON helpers;
- manifest construction from existing `ExecutionPlan`;
- manifest loader/schema validation.

### `worktrees.py`

Git worktree boundary:

- stable branch/path normalization;
- `git worktree list --porcelain` parser;
- branch/worktree collision detection;
- create/remove worktree;
- dirty-state inspection;
- no graph access.

### `leases.py`

Local derived state:

- load/validate registry;
- acquire/release task allocation lease;
- collision checks;
- atomic write via temporary file replacement.

### `orchestrator.py`

Composition layer:

- verify manifest source revision;
- validate selected wave/task set;
- generate current V2 package;
- generate selected agent handoff;
- create worktree + allocation;
- acquire/release leases;
- dry-run support;
- cleanup newly created derived state when preparation fails safely.

## CLI

### `execution-plan`

```text
graph-engineering execution-plan --spec SPEC-011-... --agent codex --output <manifest>
```

Pure planning; no worktree mutation.

### `execution-prepare`

```text
graph-engineering execution-prepare <manifest> --wave 1 [--dry-run]
```

or explicit tasks:

```text
graph-engineering execution-prepare <manifest> --task <TASK> --task <TASK>
```

Explicit tasks must all belong to the same valid manifest wave so callers cannot bypass conflict/dependency safety.

### `execution-status`

Reads local lease registry and observed worktrees.

### `execution-release`

```text
graph-engineering execution-release <TASK> [--remove-worktree] [--force]
```

Default releases lease only. Worktree removal is opt-in; dirty worktree removal requires `--force`.

## Source revision strategy

Planning records current `git rev-parse HEAD`. Preparation checks equality before any mutation. Each generated V2 package is also strictly freshness-validated. A source revision mismatch requires re-running `execution-plan`.

## Worktree strategy

Default execution root:

```text
engineering-graph/.execution/
```

Worktree:

```text
engineering-graph/.execution/worktrees/<task-safe>/
```

Branch:

```text
exec/<task-safe>
```

Creation command conceptually:

```text
git worktree add <path> -b <branch> <sourceRevision>
```

Existing branch or path is a hard collision in V3.

## Context strategy

Context artifacts are generated outside the task worktree under the execution root, then referenced by handoff metadata. This avoids polluting canonical worktrees with generated files while preserving auditability.

Preparation order:

1. validate manifest schema + revision;
2. validate wave/task selection;
3. validate leases/worktree collisions;
4. generate V2 context package(s);
5. strict freshness validation;
6. create Git branch/worktree(s);
7. write agent handoff(s);
8. acquire/write active leases;
9. emit allocations.

If a later step fails, only newly created clean derived worktrees/leases may be rolled back automatically.

## Agent runner boundary

V3 allocations expose everything a later runner needs:

- task ID;
- worktree path;
- branch;
- context package;
- handoff;
- source revision;
- validation commands.

V3 itself does not supervise agent processes, commit, push, create PRs or merge.

## Tests

### Unit

- manifest determinism/load validation;
- branch/path normalization;
- porcelain worktree parsing;
- lease collisions and malformed registry;
- wave/task selection validation;
- revision mismatch failure;
- clean/dirty release semantics.

### Integration

Use a temporary Git repository with at least one initial commit to verify real `git worktree add/remove` behavior without mutating the checkout running the tests.

### Engineering Graph CI

After ephemeral Neo4j sync:

- generate `execution-plan` for Spec 011;
- verify deterministic manifest semantics;
- verify cycles/conflicts/waves contract;
- run temporary Git repository worktree lifecycle tests via unit/integration suite;
- preserve existing V1/V2 smokes;
- preserve application dependency isolation.

## Documentation

- ADR-0019: Execution Graph/worktree lease boundary;
- `docs/architecture/EXECUTION_GRAPH.md`;
- `docs/development/engineering-graph.md` V3 flow;
- `AGENTS.md` prepared-worktree consumption rules;
- quickstart in this Spec Kit feature.

## Deferred

- GraphRAG/embeddings;
- distributed lease service;
- multi-host scheduling;
- automatic agent process supervision;
- automatic commit/push/PR/merge;
- canonical Task state mutation from lease state.