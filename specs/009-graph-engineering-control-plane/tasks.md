# Tasks: Graph Engineering Control Plane

**Input**: `specs/009-graph-engineering-control-plane/`

**Prerequisites**: `spec.md`, `research.md`, `data-model.md`, `plan.md`

## Phase 1 — Spec Kit Design Gate

- [x] T001 Specify graph-engineering scenarios, boundaries, requirements and measurable success criteria
- [x] T002 [P] Research Neo4j/Python versions and V1 scope tradeoffs
- [x] T003 Define canonical node/relationship/data identity model
- [x] T004 Define deterministic extraction, validation, context and planner architecture
- [x] T005 [P] Add feature quality checklist and quickstart
- [x] T006 Add ADR-0017 documenting Neo4j as a disposable engineering projection

## Phase 2 — Toolchain Skeleton

- [x] T007 Add `engineering-graph/` package layout, pinned requirements and project metadata
- [x] T008 Add environment/config model with repository id, Neo4j connection and validation budgets
- [x] T009 [P] Add engineering-only Neo4j Compose file and `.env.example`
- [x] T010 [P] Add `.gitignore` entries for graph local state/context outputs
- [x] T011 Add CLI entry point and `doctor` command

## Phase 3 — Versioned Graph Schema

- [x] T012 Add `schema/nodes.yaml` for seven core node labels
- [x] T013 Add `schema/relationships.yaml` for eight core relationship names and endpoint constraints
- [x] T014 Add idempotent Neo4j constraints/indexes Cypher
- [x] T015 Implement schema loader/initializer
- [x] T016 [P] Add schema-definition validation tests

## Phase 4 — Deterministic Repository Extraction

- [x] T017 Implement Markdown frontmatter parser with optional `graph` metadata
- [x] T018 Implement canonical Spec/Requirement/Task/ADR/path ID normalization
- [x] T019 Implement Spec Kit spec + FR/SC extraction
- [x] T020 Implement task checkbox/phase/[P]/[US] extraction
- [x] T021 Implement explicit Spec/Task dependency extraction without phase inference
- [x] T022 Implement ADR discovery + explicit constraint references
- [x] T023 Implement deterministic CodeArtifact/Test path classification
- [x] T024 Implement local Git revision + merged PR evidence extraction
- [x] T025 Implement GitHub Actions pull-request event ingestion when available
- [x] T026 Link PRs to explicitly identified tasks/specs and changed paths
- [x] T027 [P] Add parser/extractor fixture tests covering current Spec Kit conventions

## Phase 5 — In-Memory Graph Model and Neo4j Sync

- [x] T028 Implement typed in-memory Node/Edge/GraphModel with canonical duplicate protection
- [x] T029 Implement explicit-reference/dangling validation before database writes
- [x] T030 Implement Neo4j store connection/query abstraction
- [x] T031 Implement node MERGE/upsert by repository + canonicalId
- [x] T032 Implement relationship MERGE/upsert with provenance
- [x] T033 Implement sync-run stamping and stale relationship/node pruning
- [x] T034 Implement full `sync` command with deterministic stats output
- [x] T035 [P] Add idempotency/model tests proving same source yields same logical graph

## Phase 6 — Fundamental Cypher Queries

- [x] T036 Add impact query with bounded traversal/depth
- [x] T037 Add ready/blocked task query
- [x] T038 Add pending-task artifact conflict query
- [x] T039 Add drift/invariant evidence query set
- [x] T040 Add agent-context query
- [x] T041 [P] Add stats and PR traceability queries
- [x] T042 Wire `impact`, `ready`, `conflicts`, `stats` CLI commands with JSON output

## Phase 7 — Graph Validator

- [x] T043 Implement configurable invariant severities
- [x] T044 Implement duplicate/dangling/cycle/enforced-spec structural checks
- [x] T045 Implement warning checks for completed task evidence, critical requirement validation and orphan ADRs
- [x] T046 Implement `validate` command with human + JSON report and non-zero error exit
- [x] T047 [P] Add clean/error/warning validator fixtures/tests

## Phase 8 — Agent Context and Execution Planner

- [x] T048 Implement bounded task Context Builder with maxDepth/maxNodes budgets
- [x] T049 Implement deterministic Markdown + JSON context serializers
- [x] T050 Implement `context` CLI output/file support
- [x] T051 Implement task DAG/cycle detection/READY-BLOCKED computation
- [x] T052 Implement artifact-conflict graph and conflict-free topological wave generation
- [x] T053 Implement `waves` CLI human + JSON output
- [x] T054 [P] Add planner tests for ordering, cycle rejection and shared-file conflicts
- [x] T055 [P] Add context tests proving bounded relevant evidence

## Phase 9 — Spec Kit / Agent / Documentation Integration

- [x] T056 Update `AGENTS.md` with graph-assisted workflow + canonical file fallback
- [x] T057 Add architecture documentation for Engineering Control Plane lifecycle
- [x] T058 Update Spec Kit templates with optional graph-friendly stable reference guidance
- [x] T059 Add local quick commands/documentation for start/schema/sync/validate/context/waves/reset
- [x] T060 Ensure no application package imports/requires Neo4j/Python graph runtime

## Phase 10 — CI Architecture Gate

- [x] T061 Add dedicated `.github/workflows/engineering-graph.yml`
- [x] T062 Run Python unit suite in CI
- [x] T063 Launch ephemeral Neo4j 2026.07.1 and verify Bolt readiness
- [x] T064 Initialize graph schema and full-sync repository in CI
- [x] T065 Run graph validation and fundamental query smoke checks
- [x] T066 Keep existing application and Spec Kit CI authority unchanged

## Phase 11 — Convergence

- [x] T067 Run `$speckit-analyze` against FR-001..FR-034 and constitution
- [x] T068 Execute graph workflow against the feature branch and fix all error-level drift
- [x] T069 Verify application CI + Spec Kit CI remain green
- [x] T070 Run `$speckit-converge` against SC-001..SC-010; append only real uncovered work
- [ ] T071 Freeze PR after Graph Engineering + existing CI gates are green
- [x] T072 [Convergence] Expose `drift` as a first-class CLI query and execute it explicitly in the Neo4j CI smoke gate after SC-004 revealed the missing executable surface

## Dependencies

```text
Spec/plan
   ↓
tool skeleton + schema
   ↓
extractors + graph model
   ↓
Neo4j sync
   ↓
queries + validator
   ↓
context + planner
   ↓
Spec Kit/agent integration
   ↓
CI graph gate
   ↓
analyze/converge
```

## Parallelization

- T009/T010 can run alongside core Python skeleton after T007.
- Schema definition T012/T013 can run in parallel before T015.
- Spec/task/ADR/Git extractors T019–T025 can be developed independently after canonical identity T018.
- Fundamental Cypher queries T036–T041 are parallel after sync model exists.
- Context and planner implementation can proceed in parallel after query/model contracts are stable.
- Documentation/templates and CI wiring can run in parallel after CLI commands stabilize.

## Convergence Note

T072 was appended by `$speckit-converge` rather than silently changing SC-004. The baseline requirement explicitly calls for impact, ready, conflicts, drift and context to execute successfully; `drift.cypher` existed but was not exposed/smoke-tested as a command. The new CLI surface closes that evidence gap without expanding the graph model.

## Format Validation

All tasks use Spec Kit checkbox IDs. `[P]` marks independently executable work. Explicit task dependencies, when required, use `depends:` evidence rather than inferred phase order.
