# Research: Graph Engineering Control Plane

## Decision 1 — Neo4j is an engineering projection, never source of truth

**Decision**: Git + Markdown + code + tests + Git history remain canonical. Neo4j stores only rebuildable derived graph state.

**Why**: This preserves normal review/versioning, prevents a second documentation authority, and makes Neo4j failure non-impacting to the product runtime.

**Rejected**: authoring architectural knowledge directly in Neo4j; implementation agents mutating canonical graph state.

## Decision 2 — Neo4j Community 2026.07.1

**Decision**: Pin local/CI image to `neo4j:2026.07.1`.

**Why**: It is the current stable Community release at implementation time and is sufficient for Cypher traversal, constraints and indexes. Enterprise-only features are not required for V1.

**Operational boundary**: separate `engineering-graph/compose.yml`, not root product infrastructure.

## Decision 3 — Python 3.13 toolchain

**Decision**: implement the graph CLI in Python 3.13.

**Why**:

- existing Spec Kit CI already provisions Python 3.13;
- repository/file/Git parsing is straightforward;
- official Neo4j Python driver is mature;
- the graph tool remains decoupled from the TypeScript application workspaces.

The application runtime does not gain a Python dependency.

## Decision 4 — Official Neo4j Python driver 6.3 + PyYAML 6.0.3

**Decision**: pin:

```text
neo4j==6.3.0
PyYAML==6.0.3
```

The Neo4j 6.x Python driver supports current Neo4j 2026.x servers. PyYAML is used only for versioned schema/config/frontmatter parsing.

No Graph Data Science client is required in V1.

## Decision 5 — Seven core node labels and eight core relationships

**Decision**: begin with:

```text
Requirement, Spec, ADR, Task, CodeArtifact, Test, PullRequest
```

and:

```text
REALIZED_BY, CONSTRAINED_BY, DECOMPOSED_INTO, DEPENDS_ON,
IMPLEMENTED_BY, VALIDATED_BY, IMPLEMENTS, CHANGES
```

**Why**: These are enough to prove traceability, impact, readiness, conflicts, context and PR evidence without prematurely modeling Agent/Worktree/Commit as first-class graph nodes.

Extension seams remain versioned in schema files.

## Decision 6 — Deterministic extractors, optional explicit frontmatter

**Decision**: sync existing repository artifacts using deterministic conventions first:

- Spec Kit feature directory naming;
- FR/SC regex identifiers;
- task checkbox/ID syntax;
- ADR file naming and explicit ADR references;
- repository-relative paths inside backticks/plain task metadata;
- local Git merge metadata and GitHub Actions event payload when present.

Optional YAML frontmatter can add explicit `depends_on`, `constrained_by`, `implements`, `validated_by` relationships.

**Rejected**: LLM-inferred relationships in V1. Missing explicit evidence remains missing rather than guessed.

## Decision 7 — Feature-scoped canonical IDs

Spec Kit reuses identifiers such as `T001` and `FR-001` across features. Graph IDs therefore use the canonical Spec ID as namespace:

```text
SPEC-007-OPPORTUNITY-WORKFLOW:T040
SPEC-007-OPPORTUNITY-WORKFLOW:FR-021
```

This prevents accidental collisions while retaining human-readable source IDs as properties.

## Decision 8 — Full idempotent sync first, measured incremental sync later

**Decision**: a sync run upserts every observed entity/edge with `syncRunId`, then prunes stale derived state for that repository.

**Why**: the repository is currently small, correctness is more valuable than incremental complexity, and the graph is disposable.

**Required property**: same checkout revision → same logical entity/edge set even though `syncRunId` itself changes.

## Decision 9 — Validation severity supports bootstrap without fake green

**Decision**: structural corruption is an error; incomplete historical traceability can be warning/excluded by config.

Initial error-level invariants:

- duplicate canonical IDs before write;
- dangling explicit references;
- task dependency cycles;
- schema/query failure;
- graph-native enforced specs without tasks.

Initial configurable warning-level invariants:

- completed legacy task without explicit CodeArtifact;
- requirement without direct Test evidence;
- ADR without consumers.

New graph-native features can opt into stricter enforcement.

## Decision 10 — Execution planner is deterministic, not a scheduler

**Decision**: `waves` computes safe batches from Task dependency DAG + shared implementation/test paths.

It outputs a plan; it does not spawn agents, allocate infrastructure, merge branches, or mutate task status.

This keeps execution planning useful to Claude Code/Codex/OpenCode without creating a bespoke orchestration platform.

## Decision 11 — Context Builder produces bounded Markdown + JSON

**Decision**: build a task-centered subgraph and serialize:

- task;
- parent spec;
- requirements;
- ADR constraints;
- dependencies;
- code artifacts;
- tests;
- PR evidence.

Depth/result budgets are mandatory. Agents may use the package as their initial context but can still inspect source files directly.

## Decision 12 — Dedicated CI workflow

**Decision**: add `.github/workflows/engineering-graph.yml` with an ephemeral Neo4j service.

Pipeline:

```text
checkout
→ Python 3.13
→ install pinned graph dependencies
→ unit tests
→ wait/doctor
→ schema init
→ full sync
→ validation
→ smoke fundamental queries
```

This workflow complements rather than replaces application CI or Spec Kit CI.

## Deferred

- AST dependency graph;
- GraphRAG/vector indexes;
- semantic ADR discovery;
- first-class Agent/Worktree/Commit nodes;
- distributed task scheduler;
- AI-inferred edges;
- Neo4j Enterprise/GDS-only features.

They require a measured V1 limitation before adoption.
