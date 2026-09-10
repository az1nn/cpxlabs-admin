# Feature Specification: Graph Engineering Control Plane

**Feature Branch**: `feat/009-graph-engineering-control-plane`  
**Created**: 2026-09-10  
**Status**: Ready for Implementation

## Intent

Introduce Neo4j as a rebuildable engineering-control-plane projection over the repository. Git, Markdown specs, ADRs, tests, source code and Git history remain the source of truth. Neo4j MUST never become a business-runtime dependency or a place where canonical project knowledge is authored manually.

The first operational version covers traceability, impact analysis, task readiness, conflict detection, drift validation, agent context packages and deterministic execution waves. Semantic embeddings/GraphRAG are deliberately deferred.

## User Scenarios & Testing

### US1 — Trace a requirement to implementation and validation (P1)

As an engineer or agent, I can traverse Requirement → Spec → Task → Code/Test and PR → Task so that implementation evidence is explicit rather than inferred from large document reads.

**Independent test**: synchronize the repository and query a known Spec Kit feature; requirements, tasks, referenced code/tests, ADR constraints and merged PR evidence are connected deterministically.

### US2 — Compute impact before changing architecture (P1)

As an architect, I can ask what is affected by an ADR/spec/task and receive the bounded connected subgraph so that changes are planned with known consumers and validations.

**Independent test**: run the impact query for a known ADR and verify related specs/tasks/code/tests are returned with path distance.

### US3 — Plan safe parallel execution (P1)

As an agent orchestrator, I can identify READY/BLOCKED tasks, dependency cycles and likely file conflicts, then generate execution waves that never place directly conflicting tasks in the same wave.

**Independent test**: feed a deterministic task DAG with shared artifacts; the planner returns topological waves and separates tasks that overlap on CodeArtifact/Test paths.

### US4 — Build minimum context for an agent (P1)

As an implementation agent, I can request a task context package containing the parent spec, requirements, ADRs, dependencies, likely code, tests and PR evidence without loading the entire repository.

**Independent test**: generate Markdown and JSON context for a known task and verify only the bounded relevant subgraph is included.

### US5 — Detect architecture/spec drift in CI (P1)

As a maintainer, I receive deterministic graph-validation failures for structural errors before merge while legacy/historical gaps can remain configurable warnings during bootstrap.

**Independent test**: inject fixture graphs containing dangling references, duplicate identifiers, task cycles and enforced specs without tasks; validation exits non-zero only for configured error-severity invariants.

### US6 — Operate locally without affecting the product runtime (P2)

As a developer, I can start/stop Neo4j independently, rebuild the entire graph from the repository, inspect it in Neo4j Browser, and lose the graph database without affecting web/API/PostgreSQL behavior.

**Independent test**: delete the Neo4j volume, recreate it, run schema + sync, and obtain the same logical graph counts/relations from the same Git revision.

## Functional Requirements

- **FR-001**: Git/repository artifacts MUST remain canonical; Neo4j MUST be a derived projection that can be destroyed and rebuilt.
- **FR-002**: Neo4j MUST remain outside the application business runtime and outside web/API availability requirements.
- **FR-003**: The core schema MUST support exactly these initial node labels: `Requirement`, `Spec`, `ADR`, `Task`, `CodeArtifact`, `Test`, `PullRequest`; schema extension MUST be explicit/versioned.
- **FR-004**: The core relationship vocabulary MUST support `REALIZED_BY`, `CONSTRAINED_BY`, `DECOMPOSED_INTO`, `DEPENDS_ON`, `IMPLEMENTED_BY`, `VALIDATED_BY`, `IMPLEMENTS`, `CHANGES`.
- **FR-005**: Every graph entity MUST carry stable identity plus repository/source provenance sufficient to rebuild and diagnose extraction.
- **FR-006**: The sync engine MUST be deterministic and idempotent for the same repository revision.
- **FR-007**: Full sync MUST remove stale derived nodes/relationships without requiring manual Neo4j cleanup.
- **FR-008**: Sync MUST parse Spec Kit feature directories, FR/SC identifiers, task checkboxes/IDs, ADR filenames/references and explicit path references without AI inference.
- **FR-009**: Optional Markdown frontmatter MAY add explicit graph metadata, but existing human-readable specs without frontmatter MUST still synchronize via deterministic conventions.
- **FR-010**: New Spec Kit templates MUST document graph-friendly stable IDs/references without making Neo4j required to author a spec.
- **FR-011**: Git ingestion MUST create PullRequest evidence from deterministic local Git/GitHub-event metadata where available and relate changed files.
- **FR-012**: PullRequest → Task linkage MUST use explicit task/spec identifiers from PR metadata; absence of explicit evidence MUST not be guessed by an LLM.
- **FR-013**: The toolchain MUST provide reusable Cypher queries for impact, ready tasks, conflicts, drift and task context.
- **FR-014**: READY computation MUST respect explicit `Task DEPENDS_ON Task` relationships and completed dependency status.
- **FR-015**: The planner MUST detect task dependency cycles and fail planning rather than silently scheduling cyclic work.
- **FR-016**: Conflict detection MUST identify pending tasks sharing implementation/test artifacts.
- **FR-017**: Execution-wave generation MUST respect dependency ordering and MUST not place known artifact-conflicting tasks in the same wave.
- **FR-018**: Context Builder MUST produce bounded Markdown and JSON context packages for one Task.
- **FR-019**: Context packages MUST include parent Spec, Requirements, ADR constraints, task dependencies, CodeArtifacts, Tests and PullRequests when those relations exist.
- **FR-020**: Context Builder MUST support a configurable traversal/depth budget to prevent context explosion.
- **FR-021**: Graph Validator MUST support named invariants with severity `error` or `warning`.
- **FR-022**: Validation MUST detect at minimum duplicate canonical IDs, dangling explicit references, task dependency cycles, active/enforced specs without tasks, and completed enforced tasks without implementation/validation evidence according to configuration.
- **FR-023**: Historical bootstrap gaps MUST be representable as warnings/exclusions without disabling structural validation globally.
- **FR-024**: A dedicated GitHub Actions workflow MUST launch an ephemeral Neo4j service, install the pinned graph toolchain, run unit tests, initialize schema, synchronize the repository and run graph validation.
- **FR-025**: The graph workflow MUST not weaken or replace existing TypeScript, PostgreSQL, Storybook, Playwright or Spec Kit gates.
- **FR-026**: Local Neo4j MUST be provided through an engineering-only Compose file with persistent volume, authentication and health verification.
- **FR-027**: Credentials MUST come from environment variables/.env examples and MUST never be committed as production secrets.
- **FR-028**: The CLI MUST expose at least `doctor`, `schema`, `sync`, `validate`, `impact`, `ready`, `conflicts`, `context`, `waves` and `stats` commands.
- **FR-029**: Query commands MUST support machine-readable JSON output for agent/CI consumption in addition to human-readable output where useful.
- **FR-030**: The repository MUST document the lifecycle integration points with Spec Kit: sync after artifact changes, impact during planning, DAG/conflicts/waves after tasks, context before implementation, drift validation before merge.
- **FR-031**: `AGENTS.md` MUST instruct Codex/Claude/OpenCode-style agents to prefer graph-produced task context when Neo4j is available while retaining file-based fallback when unavailable.
- **FR-032**: Neo4j unavailability MUST degrade engineering assistance only; application build/runtime behavior MUST remain unaffected.
- **FR-033**: The first version MUST NOT add whole-repository embeddings, AI-inferred edges, distributed scheduling, a generic workflow engine, or Neo4j writes by implementation agents.
- **FR-034**: The architecture MUST leave explicit extension seams for future GraphRAG and richer Git/agent/worktree nodes without requiring them in V1.

## Graph Semantics

### Core Nodes

```text
Requirement
Spec
ADR
Task
CodeArtifact
Test
PullRequest
```

### Core Relationships

```text
Requirement -[:REALIZED_BY]-> Spec
Spec        -[:CONSTRAINED_BY]-> ADR
Spec        -[:DECOMPOSED_INTO]-> Task
Spec        -[:DEPENDS_ON]-> Spec
Task        -[:DEPENDS_ON]-> Task
Task        -[:IMPLEMENTED_BY]-> CodeArtifact
Task        -[:VALIDATED_BY]-> Test
PullRequest -[:IMPLEMENTS]-> Task
PullRequest -[:CHANGES]-> CodeArtifact|Test
```

Tests are modeled separately from CodeArtifact even though both are repository paths, so validation coverage can be queried directly.

## Source Conventions

- Spec identity: feature directory `specs/###-slug` → `SPEC-###-SLUG` unless explicit metadata overrides it.
- Requirement identity: feature-scoped `FR-###` / `SC-###` → `<SPEC-ID>:FR-###` / `<SPEC-ID>:SC-###`.
- Task identity: feature-scoped `T###` → `<SPEC-ID>:T###`.
- ADR identity: `docs/adr/0017-*.md` → `ADR-0017`.
- Code/Test paths are repository-relative POSIX paths.
- PR identity: repository + PR number.

Stable IDs are feature-scoped where Spec Kit reuses `T001`, `FR-001`, etc.

## Non-Goals

- Neo4j as runtime database for customers/opportunities/auth/audit.
- Replacing Spec Kit or Git.
- Storing canonical Markdown inside Neo4j.
- AST-level dependency analysis in V1.
- LLM-generated/inferred graph relationships in V1.
- Embeddings/vector indexes/GraphRAG in V1.
- Autonomous merge or distributed agent scheduler.

## Success Criteria

- **SC-001**: Repeating full sync twice at the same Git revision yields identical logical node/edge sets.
- **SC-002**: All seven core labels and eight core relationship types are represented by versioned schema definitions and database constraints/indexes where applicable.
- **SC-003**: Repository fixtures prove extraction of Spec, FR/SC Requirement, Task, ADR, code/test paths and PR evidence.
- **SC-004**: Impact, ready, conflicts, drift and context queries execute successfully against the CI graph.
- **SC-005**: Planner tests prove dependency ordering, cycle rejection and conflict-free waves for deterministic fixtures.
- **SC-006**: Context Builder produces bounded Markdown and JSON packages with expected parent/evidence relations.
- **SC-007**: Validator fixture tests produce non-zero exit for configured structural errors and zero exit for the clean graph.
- **SC-008**: GitHub Actions rebuilds an ephemeral graph from checkout and passes schema + sync + validation without a persistent external Neo4j dependency.
- **SC-009**: Existing application CI and Spec Kit workflows remain unchanged in authority and continue passing.
- **SC-010**: Local documentation demonstrates graph deletion/rebuild and confirms application services do not depend on Neo4j.

## Assumptions

- Python 3.13 is acceptable for engineering tooling because the existing Spec Kit CI already provisions Python.
- Neo4j Community is sufficient for V1 traceability/control-plane queries.
- Full-repository sync is small enough for the current starter; incremental optimization can follow measured need.
- Explicit path references and Git diffs provide enough artifact evidence to prove V1 value without AST analysis.
