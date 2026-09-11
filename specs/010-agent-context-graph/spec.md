# Feature Specification: Agent Context Graph

**Feature Branch**: `feat/010-agent-context-graph`  
**Created**: 2026-09-10  
**Status**: Draft

## Intent

Evolve the deterministic Engineering Graph from a repository traceability/control-plane foundation into an operational **Agent Context Graph**. The graph MUST produce bounded, reproducible task context packages that agents can consume without scanning the whole repository, while Git/Markdown/code/tests remain canonical.

This feature implements the V2 roadmap objective from `graph-engineering-neo4j-spec-driven.md`: Context Builder, automatic context-package creation, Claude Code/Codex support, and explicit Task → files → tests → ADR context. It does **not** introduce semantic embeddings, GraphRAG, autonomous scheduling, worktree allocation, or direct agent writes to Neo4j.

## User Scenarios & Testing

### US1 — Generate a deterministic task package (P1)

As an implementation agent, I can request one Task and receive a bounded package containing the task, parent spec, relevant requirements, ADRs, dependencies, implementation paths, test paths and PR evidence.

**Independent test**: generate the same task package twice at the same Git revision and assert semantic JSON equality excluding generation timestamp/output path.

### US2 — Generate packages automatically for READY work (P1)

As an orchestrator or engineer, I can generate context packages for all READY tasks in a spec so agents do not need manual context assembly.

**Independent test**: a fixture spec with READY/BLOCKED tasks generates packages only for READY tasks by default and can explicitly include a selected task list.

### US3 — Consume context from Codex and Claude Code (P1)

As a developer using Codex or Claude Code, I can generate an agent-specific handoff that references the portable context package and canonical repository files without duplicating the source of truth.

**Independent test**: Codex and Claude adapters produce deterministic handoff files that contain task identity, package location, canonical paths, validation commands and source revision.

### US4 — Detect stale context before implementation (P1)

As an agent, I can detect that a package was generated from an older repository revision and fail closed before treating it as current implementation context.

**Independent test**: generate at revision A, move repository HEAD to revision B, run package validation, and assert stale status/non-zero exit when strict freshness is requested.

### US5 — Enforce context budgets and provenance (P1)

As a maintainer, I can cap graph depth, node count and rendered package size while retaining provenance explaining why each artifact was included.

**Independent test**: a dense graph fixture is truncated deterministically at configured budgets and every included item contains relation/source provenance.

### US6 — Operate without Neo4j as a hard dependency (P2)

As a developer, application runtime and ordinary repository work continue when Neo4j is unavailable; context generation alone degrades.

**Independent test**: application CI/build does not import or require the Agent Context Graph runtime, and context CLI fails with a clear engineering-only error when Neo4j is unavailable.

## Functional Requirements

- **FR-001**: Git/Markdown/code/tests/Git history MUST remain canonical; generated context packages are disposable derived artifacts.
- **FR-002**: V2 MUST build on the V1 Engineering Graph and MUST NOT add a product-runtime dependency on Neo4j or Python graph tooling.
- **FR-003**: A context package MUST identify `packageVersion`, repository, source revision, task canonical ID, generated timestamp, budgets and freshness metadata.
- **FR-004**: A context package MUST include the Task and parent Spec when present.
- **FR-005**: A context package MUST include linked Requirements and ADR constraints when present.
- **FR-006**: A context package MUST include explicit Task dependencies and their statuses.
- **FR-007**: A context package MUST include linked CodeArtifact and Test paths when present.
- **FR-008**: A context package MUST include PullRequest evidence when linked by deterministic V1 provenance.
- **FR-009**: Every included graph entity/relation MUST retain enough provenance to explain why it is in the package.
- **FR-010**: Context traversal MUST remain bounded by configurable max depth and max nodes.
- **FR-011**: Rendered package output MUST support deterministic JSON and human-readable Markdown.
- **FR-012**: Context package semantic content MUST be reproducible for the same graph state/source revision and inputs.
- **FR-013**: Generated packages MUST be written under ignored engineering-only output directories and MUST NOT become canonical documentation by default.
- **FR-014**: The CLI MUST support generation for one explicit Task.
- **FR-015**: The CLI MUST support batch generation for READY tasks in one Spec.
- **FR-016**: Batch generation MUST NOT silently include BLOCKED tasks unless explicitly requested.
- **FR-017**: The CLI MUST support explicit task-selection input for deterministic targeted batch generation.
- **FR-018**: Package validation MUST detect malformed package schema, unknown task identity and repository/source-revision mismatch.
- **FR-019**: Strict freshness validation MUST return non-zero when a package revision differs from current Git HEAD.
- **FR-020**: Non-strict inspection MAY report staleness without failing.
- **FR-021**: Agent adapters MUST consume the portable context-package model rather than implement separate graph traversals.
- **FR-022**: A Codex adapter MUST generate a handoff compatible with repository `AGENTS.md` conventions and point the agent to canonical files before editing.
- **FR-023**: A Claude Code adapter MUST generate a portable Markdown handoff/prompt context without requiring canonical knowledge to be copied into Neo4j or a proprietary store.
- **FR-024**: Agent handoffs MUST include task ID, source revision, package path, relevant paths and expected validation commands.
- **FR-025**: Agent adapters MUST NOT automatically launch an agent, create a worktree, commit, push or merge in V2.
- **FR-026**: Context package generation MUST expose machine-readable summary statistics including included/truncated node counts and package byte size.
- **FR-027**: Oversized packages MUST truncate deterministically and report truncation rather than silently exceed configured limits.
- **FR-028**: The context system MUST avoid embedding raw secrets/credentials and MUST only project canonical repository content/metadata already selected by deterministic graph relations.
- **FR-029**: CI MUST test single-task generation, READY batch generation, freshness validation and both agent adapters against deterministic fixtures or an ephemeral graph.
- **FR-030**: CI MUST continue to prove `apps/*` and product `packages/*` do not depend on graph tooling.
- **FR-031**: `AGENTS.md` MUST document how agents request/validate a context package and then open canonical files named by it.
- **FR-032**: The operator documentation MUST explain package lifecycle: sync → validate graph → generate → validate freshness → consume → discard/regenerate.
- **FR-033**: V2 MUST NOT add embeddings, vector search, semantic retrieval, LLM-inferred authoritative edges, autonomous task allocation or worktree scheduling.
- **FR-034**: The design MUST leave a clean extension seam for V3 Execution Graph to consume READY task packages without coupling V2 to a scheduler.

## Context Package Contract

```text
ContextPackage
├── packageVersion
├── repository
├── sourceRevision
├── taskId
├── generatedAt
├── freshness
├── budget
│   ├── maxDepth
│   ├── maxNodes
│   └── maxBytes
├── summary
│   ├── includedNodes
│   ├── truncatedNodes
│   └── renderedBytes
├── task
├── spec
├── requirements[]
├── adrs[]
├── dependencies[]
├── codeArtifacts[]
├── tests[]
├── pullRequests[]
└── provenance[]
```

`generatedAt` and output location are operational metadata and are excluded from semantic reproducibility comparison.

## Agent Adapter Boundary

```text
Neo4j
  │
  ▼
Context Builder
  │
  ▼
Portable ContextPackage (JSON/Markdown)
  │
  ├──► Codex handoff
  └──► Claude Code handoff
```

Adapters do not query Neo4j independently and do not become sources of truth.

## Non-Goals

- GraphRAG/vector search/embeddings.
- Whole-repository semantic inference.
- Agent execution or spawning.
- Worktree allocation/reservations.
- Autonomous commits, pushes or merges.
- Neo4j-authored canonical documentation.
- Product runtime integration.

## Success Criteria

- **SC-001**: Same task/revision/budgets produce semantically identical JSON packages across repeated generation.
- **SC-002**: A known task package contains its Spec, Requirements, ADRs, dependencies, CodeArtifacts, Tests and PR evidence when the graph contains those relations.
- **SC-003**: READY batch generation selects only READY tasks by default and produces one package per selected task.
- **SC-004**: Strict freshness validation fails for a package generated from an older Git revision and succeeds for current revision.
- **SC-005**: Budget fixtures prove deterministic truncation by depth/node/byte limits with explicit truncation statistics.
- **SC-006**: Codex and Claude Code adapters both generate deterministic handoffs from the same portable package without separate graph queries.
- **SC-007**: Generated outputs remain ignored/disposable and can be recreated after deletion.
- **SC-008**: Engineering Graph CI exercises package generation/validation/adapters against ephemeral Neo4j while existing Spec Kit/product CI remain green.
- **SC-009**: Application packages remain free of Neo4j/Agent Context Graph runtime dependencies.
- **SC-010**: Documentation demonstrates the full agent flow from Task ID to validated package to canonical file navigation.

## Source Alignment

The project roadmap defines V2 Agent Context Graph around four deliverables: Context Builder, automatic context packages, Claude Code/Codex support, and Task → files → tests → ADR relationships. This spec preserves that scope while treating package schema, freshness, deterministic budgets and adapter boundaries as implementation architecture needed to make those deliverables verifiable.
