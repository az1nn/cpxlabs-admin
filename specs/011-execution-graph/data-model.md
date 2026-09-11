# Data Model: Execution Graph

**Feature**: `SPEC-011-EXECUTION-GRAPH`

## ExecutionManifest

```text
ExecutionManifest
├── manifestVersion: string
├── repository: string
├── sourceRevision: string
├── specId: string | null
├── agent: codex | claude
├── generatedAt: ISO-8601 string
├── ready: TaskId[]
├── blocked: BlockedTask[]
├── cycles: TaskId[][]
├── conflicts: TaskConflict[]
└── waves: ExecutionWave[]
```

### Semantics

- `sourceRevision` binds the plan/context base to one Git revision.
- `generatedAt` is operational metadata and is excluded from semantic reproducibility comparison.
- `waves` are dependency-safe and conflict-free according to the existing V1 planner.
- cycle presence makes the manifest non-preparable.

## ExecutionWave

```text
ExecutionWave
├── index: positive integer
└── tasks: TaskId[]
```

Tasks are sorted deterministically by the planner's priority + canonical ID order.

## ExecutionAllocation

```text
ExecutionAllocation
├── allocationVersion: string
├── repository: string
├── taskId: string
├── specId: string
├── sourceRevision: string
├── agent: codex | claude
├── branch: string
├── worktreePath: string
├── contextPath: string
├── handoffPath: string
├── leaseStatus: planned | active | released
├── createdAt: ISO-8601 string
├── updatedAt: ISO-8601 string
└── validationCommands: string[]
```

`planned` is emitted by dry-run only and is never persisted as an active lease. `active` means the task is locally allocated. `released` records historical local release state.

An active allocation means the task has isolated working state and fresh planning/context evidence. It does not mean the task is started/completed in canonical planning state.

## LeaseRegistry

```text
LeaseRegistry
├── registryVersion: string
├── repository: string
└── leases: ExecutionAllocation[]
```

### Invariants

- at most one active lease per `taskId`;
- at most one active lease per `branch`;
- at most one active lease per resolved `worktreePath`;
- registry repository must equal configured repository ID;
- malformed/unknown-version registry fails closed;
- writes use temporary file + atomic replace where supported.

Released entries may remain as local operational history; only `active` entries participate in collision ownership.

## WorktreeDescriptor

Internal model for observed Git worktrees:

```text
WorktreeDescriptor
├── path: absolute path
├── head: commit SHA | null
├── branch: ref name | null
├── bare: bool
└── detached: bool
```

This is discovered via `git worktree list --porcelain`; it is not persisted as canonical graph data.

## PreparationRequest

```text
PreparationRequest
├── manifestPath: path
├── wave: integer | null
├── tasks: TaskId[]
├── executionRoot: path | null
└── dryRun: bool
```

The agent is already bound by `ExecutionManifest.agent`; preparation does not independently change it.

Exactly one task-selection mode is active:

- explicit `wave`; or
- explicit task IDs validated as a subset of one manifest wave.

## PreparationResult

```text
PreparationResult
├── repository
├── sourceRevision
├── specId
├── allocations: ExecutionAllocation[]
└── dryRun: bool
```

A dry run computes deterministic branch/path/allocation metadata and validates current V2 context without mutating Git worktrees or writing active leases.

## State transitions

```text
dry-run
  └──► planned (not persisted as active lease)

prepare
  └──► active lease + worktree
             │ execution-release
             ▼
        released lease
```

Canonical task state remains separate:

```text
pending → done
```

That transition occurs only through edits to canonical task Markdown followed by Graph Sync.

## Branch normalization

```text
canonical Task ID
      │ lower + replace non [a-z0-9._-] with '-'
      ▼
exec/<safe-task-id>
```

Repeated separators are collapsed; leading/trailing separators are removed. Empty normalized IDs are invalid.

## Existing deterministic task state

The allocator distinguishes resume from collision:

- the exact expected `worktreePath` already registered on the exact expected deterministic task branch can be resumed without resetting it;
- the expected branch already checked out at another path is a collision;
- an existing filesystem path that is not a registered Git worktree is a collision;
- existing task branch history is never silently reset or overwritten.

This preserves prior task work while preventing V3 from claiming unrelated worktree state.

## Execution root

Default:

```text
engineering-graph/.execution/
├── leases.json
├── manifests/<spec-safe>.json
├── contexts/<task-safe>/
│   ├── context.json
│   ├── context.md
│   └── codex.md | claude.md
└── worktrees/<task-safe>/
```

All metadata paths are derived and Git-ignored. Dirty/uncommitted content inside a worktree is explicitly exempt from "disposable" treatment and is user data.