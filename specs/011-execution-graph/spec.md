# Feature Specification: Execution Graph

**Feature Branch**: `feat/011-execution-graph`  
**Created**: 2026-09-11  
**Status**: Draft

## Intent

Evolve the Engineering Graph from deterministic context delivery into an **Execution Graph** that controls safe parallelization of implementation work. V3 MUST consume the V1 task DAG/conflict model and V2 portable `ContextPackage`, calculate dependency-safe conflict-free execution waves, and allocate isolated Git worktrees for selected tasks.

The repository remains authoritative. Neo4j remains a rebuildable engineering projection. Execution plans, leases, worktree metadata and handoffs are operational/derived artifacts and MUST NOT become a second source of truth.

This feature implements the V3 roadmap objective from `graph-engineering-neo4j-spec-driven.md`: task DAG, READY/BLOCKED state, artifact-conflict control, execution waves and worktree allocation. It does **not** add GraphRAG, semantic retrieval, autonomous commits/pushes/merges, or hidden agent-written canonical state.

## User Scenarios & Testing

### US1 — Produce a deterministic execution manifest (P1)

As an engineer or orchestrator, I can request an execution plan for a Spec and receive deterministic READY/BLOCKED state, dependency cycles, artifact conflicts and ordered execution waves.

**Independent test**: run the planner twice over the same projected task graph and assert semantic manifest equality.

### US2 — Allocate one isolated worktree per runnable task (P1)

As an orchestrator, I can materialize a selected wave into deterministic task branches and Git worktrees so concurrent agents do not edit the same working directory.

**Independent test**: prepare a wave inside a temporary Git repository and assert one branch/worktree per allocation, with paths and branch names stable for the same task identities.

### US3 — Never co-schedule conflicting tasks (P1)

As a maintainer, tasks that share implementation/test artifacts are never placed in the same wave or prepared concurrently.

**Independent test**: two READY tasks with an overlapping artifact must appear in different waves and never share a prepared allocation set.

### US4 — Bind each allocation to fresh V2 context (P1)

As an implementation agent, every prepared worktree has a current `ContextPackage` and agent handoff generated from the exact source revision used by the execution plan.

**Independent test**: preparation fails closed when package freshness is stale or when repository HEAD changes between planning and allocation.

### US5 — Record operational leases without mutating canonical planning state (P1)

As an orchestrator, I can reserve a task/worktree with a derived lease so a second preparation attempt detects an active allocation rather than duplicating it.

**Independent test**: preparing the same task twice with an active lease returns a deterministic conflict; releasing the lease permits a new allocation.

### US6 — Clean up safely (P1)

As an engineer, I can release an execution allocation and optionally remove its clean generated worktree while preserving branches or dirty worktrees unless removal is explicitly forced.

**Independent test**: normal release removes metadata and a clean disposable worktree; dirty worktrees fail closed unless explicit force is supplied.

### US7 — Remain agent/vendor independent (P2)

As a developer, V3 can prepare Codex or Claude Code handoffs from the same V2 package while worktree allocation itself has no vendor-specific behavior.

**Independent test**: agent selection changes only the handoff artifact/command metadata, not task selection, wave ordering, branch naming or worktree placement.

## Functional Requirements

- **FR-001**: Git/Markdown/code/tests/Git history MUST remain canonical; Execution Graph state is derived operational state.
- **FR-002**: V3 MUST consume existing V1 planner relationships and V2 `ContextPackage`; it MUST NOT duplicate graph traversal logic inside worktree/agent adapters.
- **FR-003**: An execution manifest MUST identify manifest version, repository, source revision, Spec ID, generated timestamp and selected agent adapter.
- **FR-004**: The manifest MUST include READY tasks, BLOCKED tasks with blockers, dependency cycles, artifact conflicts and ordered waves.
- **FR-005**: Wave computation MUST be deterministic for identical graph state and inputs.
- **FR-006**: Tasks sharing projected implementation/test artifacts MUST NOT appear in the same wave.
- **FR-007**: Task dependency cycles MUST prevent preparation and produce machine-readable cycle evidence.
- **FR-008**: Dependencies outside the selected Spec MUST remain blockers unless they are projected as done.
- **FR-009**: Preparation MUST target an explicit wave or explicit task set already valid under the execution manifest.
- **FR-010**: Preparation MUST fail if repository HEAD no longer matches the manifest source revision unless an explicit replan is performed.
- **FR-011**: Each prepared task MUST receive a deterministic branch name derived from its canonical task ID.
- **FR-012**: Each prepared task MUST receive a deterministic worktree directory under an ignored engineering-only root by default.
- **FR-013**: Worktree creation MUST use Git worktree primitives rather than copying repository directories.
- **FR-014**: Existing branches/worktrees MUST be detected before mutation and MUST NOT be silently overwritten.
- **FR-015**: V3 MUST maintain a derived lease registry containing task ID, branch, worktree path, source revision, agent, status and timestamps.
- **FR-016**: Active leases MUST prevent duplicate allocation of the same task.
- **FR-017**: Lease writes MUST be deterministic/atomic enough for one local orchestrator process and fail closed on malformed registry state.
- **FR-018**: Lease state MUST live under ignored engineering-only output and MUST NOT be synchronized into Neo4j as canonical planning truth.
- **FR-019**: Preparation MUST generate or regenerate a V2 `ContextPackage` for each task from the current graph.
- **FR-020**: Prepared context MUST pass strict freshness validation before the allocation is reported ready.
- **FR-021**: Preparation MUST generate an agent-specific handoff from the same portable package.
- **FR-022**: Codex/Claude selection MUST NOT alter execution semantics, wave composition, branch names or worktree paths.
- **FR-023**: An execution allocation MUST expose canonical task/spec paths, context path, handoff path, branch and worktree location.
- **FR-024**: V3 MAY emit a suggested launch command, but MUST NOT automatically commit, push, merge or delete user work.
- **FR-025**: Agent process spawning is optional orchestration metadata in V3; repository mutation beyond worktree/branch allocation requires an explicit future feature or explicit operator action.
- **FR-026**: Release MUST remove the active lease without changing Task status in canonical Markdown.
- **FR-027**: Release MUST refuse normal removal of a dirty worktree.
- **FR-028**: Forced cleanup MUST require an explicit force flag and MUST remain scoped to the generated worktree.
- **FR-029**: Execution manifests and lease registries MUST support deterministic JSON; human-readable Markdown MAY be provided for operator inspection.
- **FR-030**: All generated execution state MUST be ignored/disposable and reconstructible from Git + graph projection, except uncommitted work inside an allocated worktree which MUST be treated as user data.
- **FR-031**: Engineering Graph CI MUST exercise planning, conflict-safe waves, temporary-repository worktree allocation, lease collision, strict freshness and clean release.
- **FR-032**: Product runtime MUST remain independent of Neo4j/Python execution tooling.
- **FR-033**: Documentation MUST describe plan → prepare → work → validate → release and the source-of-truth boundary.
- **FR-034**: V3 MUST NOT add embeddings, vector search, GraphRAG or LLM-inferred authoritative graph edges.
- **FR-035**: V3 MUST leave a clean seam for a later agent runner to consume an `ExecutionAllocation` without changing planning or context contracts.

## Execution Contract

```text
ExecutionManifest v1
├── repository
├── sourceRevision
├── specId
├── agent
├── ready[]
├── blocked[]
├── cycles[]
├── conflicts[]
└── waves[][]

ExecutionAllocation v1
├── taskId
├── sourceRevision
├── agent
├── branch
├── worktreePath
├── contextPath
├── handoffPath
├── leaseStatus
└── validationCommands[]
```

## Authority / Lifecycle

```text
Git canonical files
      │
      ▼
Engineering Graph projection
      │
      ├──► ExecutionManifest
      │          │
      │          ▼
      │      selected wave
      │          │
      ▼          ▼
ContextPackage   Worktree + lease
      │          │
      └────┬─────┘
           ▼
      Agent handoff
           │
           ▼
   canonical file edits
```

Task status transitions remain canonical Markdown edits and subsequent graph syncs. A lease is not task completion.

## Non-Goals

- GraphRAG, embeddings or semantic search.
- LLM-inferred authoritative relationships.
- Automatic canonical task-status mutation.
- Automatic commit, push, PR creation or merge.
- Automatic deletion of dirty worktrees.
- Product runtime integration.
- Multi-host distributed locking.
- Long-running agent process supervision.

## Success Criteria

- **SC-001**: Same graph/source revision and inputs produce semantically identical execution manifests.
- **SC-002**: READY/BLOCKED/cycle/conflict evidence in the manifest matches the V1 planner for a known fixture.
- **SC-003**: Conflicting tasks never share a wave.
- **SC-004**: Preparing one wave creates exactly one isolated Git worktree and deterministic branch per selected task.
- **SC-005**: Active lease collision prevents duplicate preparation of the same task.
- **SC-006**: Source-revision drift between planning and preparation fails closed.
- **SC-007**: Every successful allocation contains a strictly current V2 package and agent handoff.
- **SC-008**: Clean release removes derived allocation state; dirty worktree removal is refused without force.
- **SC-009**: Engineering Graph CI validates V3 using an ephemeral Neo4j projection and temporary Git repositories while Spec Kit/product CI remain green.
- **SC-010**: `apps/*` and product `packages/*` remain independent of Execution Graph runtime.
- **SC-011**: Operator docs demonstrate the complete deterministic flow from Spec to waves to worktree/handoff to release.

## Source Alignment

The project roadmap defines V3 Execution Graph as control of parallelization through task DAG, READY/BLOCKED state, artifact conflicts, execution waves and worktree allocation. V1 already computes the graph-side DAG/conflict/wave primitives; V2 provides portable context. V3 therefore composes those stable contracts into a lifecycle-safe execution manifest and worktree allocator rather than replacing them.