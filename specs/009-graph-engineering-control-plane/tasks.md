# Tasks: Graph Engineering Control Plane

**Input**: `specs/009-graph-engineering-control-plane/`

**Prerequisites**: `spec.md`, `research.md`, `data-model.md`, `plan.md`

## Phase 1 — Spec Kit Design Gate

- [x] T001 Specify graph-engineering scenarios, boundaries, requirements and measurable success criteria
- [x] T002 [P] Research Neo4j/Python versions and V1 scope tradeoffs
- [x] T003 Define canonical node/relationship/data identity model
- [x] T004 Define deterministic extraction, validation, context and planner architecture
- [ ] T005 [P] Add feature quality checklist and quickstart
- [ ] T006 Add ADR-0017 documenting Neo4j as a disposable engineering projection

## Phase 2 — Toolchain Skeleton

- [ ] T007 Add `engineering-graph/` package layout, pinned requirements and project metadata
- [ ] T008 Add environment/config model with repository id, Neo4j connection and validation budgets
- [ ] T009 [P] Add engineering-only Neo4j Compose file and `.env.example`
- [ ] T010 [P] Add `.gitignore` entries for graph local state/context outputs
- [ ] T011 Add CLI entry point and `doctor` command

## Phase 3 — Versioned Graph Schema

- [ ] T012 Add `schema/nodes.yaml` for seven core node labels
- [ ] T013 Add `schema/relationships.yaml` for eight core relationship names and endpoint constraints
- [ ] T014 Add idempotent Neo4j constraints/indexes Cypher
- [ ] T015 Implement schema loader/initializer
- [ ] T016 [P] Add schema-definition validation tests

## Phase 4 — Deterministic Repository Extraction

- [ ] T017 Implement Markdown frontmatter parser with optional `graph` metadata
- [ ] T018 Implement canonical Spec/Requirement/Task/ADR/path ID normalization
- [ ] T019 Implement Spec Kit spec + FR/SC extraction
- [ ] T020 Implement task checkbox/phase/[P]/[US] extraction
- [ ] T021 Implement explicit Spec/Task dependency extraction without phase inference
- [ ] T022 Implement ADR discovery + explicit constraint references
- [ ] T023 Implement deterministic CodeArtifact/Test path classification
- [ ] T024 Implement local Git revision + merged PR evidence extraction
- [ ] T025 Implement GitHub Actions pull-request event ingestion when available
- [ ] T026 Link PRs to explicitly identified tasks/specs and changed paths
- [ ] T027 [P] Add parser/extractor fixture tests covering current Spec Kit conventions

## Phase 5 — In-Memory Graph Model and Neo4j Sync

- [ ] T028 Implement typed in-memory Node/Edge/GraphModel with canonical duplicate protection
- [ ] T029 Implement explicit-reference/dangling validation before database writes
- [ ] T030 Implement Neo4j store connection/query abstraction
- [ ] T031 Implement node MERGE/upsert by repository + canonicalId
- [ ] T032 Implement relationship MERGE/upsert with provenance
- [ ] T033 Implement sync-run stamping and stale relationship/node pruning
- [ ] T034 Implement full `sync` command with deterministic stats output
- [ ] T035 [P] Add idempotency/model tests proving same source yields same logical graph

## Phase 6 — Fundamental Cypher Queries

- [ ] T036 Add impact query with bounded traversal/depth
- [ ] T037 Add ready/blocked task query
- [ ] T038 Add pending-task artifact conflict query
- [ ] T039 Add drift/invariant evidence query set
- [ ] T040 Add agent-context query
- [ ] T041 [P] Add stats and PR traceability queries
- [ ] T042 Wire `impact`, `ready`, `conflicts`, `stats` CLI commands with JSON output

## Phase 7 — Graph Validator

- [ ] T043 Implement configurable invariant severities
- [ ] T044 Implement duplicate/dangling/cycle/enforced-spec structural checks
- [ ] T045 Implement warning checks for completed task evidence, critical requirement validation and orphan ADRs
- [ ] T046 Implement `validate` command with human + JSON report and non-zero error exit
- [ ] T047 [P] Add clean/error/warning validator fixtures/tests

## Phase 8 — Agent Context and Execution Planner

- [ ] T048 Implement bounded task Context Builder with maxDepth/maxNodes budgets
- [ ] T049 Implement deterministic Markdown + JSON context serializers
- [ ] T050 Implement `context` CLI output/file support
- [ ] T051 Implement task DAG/cycle detection/READY-BLOCKED computation
- [ ] T052 Implement artifact-conflict graph and conflict-free topological wave generation
- [ ] T053 Implement `waves` CLI human + JSON output
- [ ] T054 [P] Add planner tests for ordering, cycle rejection and shared-file conflicts
- [ ] T055 [P] Add context tests proving bounded relevant evidence

## Phase 9 — Spec Kit / Agent / Documentation Integration

- [ ] T056 Update `AGENTS.md` with graph-assisted workflow + canonical file fallback
- [ ] T057 Add architecture documentation for Engineering Control Plane lifecycle
- [ ] T058 Update Spec Kit templates with optional graph-friendly stable reference guidance
- [ ] T059 Add local quick commands/documentation for start/schema/sync/validate/context/waves/reset
- [ ] T060 Ensure no application package imports/requires Neo4j/Python graph runtime

## Phase 10 — CI Architecture Gate

- [ ] T061 Add dedicated `.github/workflows/engineering-graph.yml`
- [ ] T062 Run Python unit suite in CI
- [ ] T063 Launch ephemeral Neo4j 2026.07.1 and verify Bolt readiness
- [ ] T064 Initialize graph schema and full-sync repository in CI
- [ ] T065 Run graph validation and fundamental query smoke checks
- [ ] T066 Keep existing application and Spec Kit CI authority unchanged

## Phase 11 — Convergence

- [ ] T067 Run `$speckit-analyze` against FR-001..FR-034 and constitution
- [ ] T068 Execute graph workflow against the feature branch and fix all error-level drift
- [ ] T069 Verify application CI + Spec Kit CI remain green
- [ ] T070 Run `$speckit-converge` against SC-001..SC-010; append only real uncovered work
- [ ] T071 Freeze PR after Graph Engineering + existing CI gates are green

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

## Format Validation

All tasks use Spec Kit checkbox IDs. `[P]` marks independently executable work.
