# Implementation Plan: Graph Engineering Control Plane

**Branch**: `feat/009-graph-engineering-control-plane`  
**Spec**: `specs/009-graph-engineering-control-plane/spec.md`

## Summary

Build a repository-local Graph Engineering control plane using Neo4j Community and a small Python CLI. The graph is a disposable projection of Spec Kit, ADR, code/test path and Git/PR evidence. It adds traceability, impact analysis, task DAG/readiness, artifact-conflict detection, bounded agent context and CI drift gates without becoming a product runtime dependency.

## Technical Context

- **Canonical data**: Git repository only.
- **Graph store**: Neo4j Community `2026.07.1`, engineering-only.
- **Tool runtime**: Python 3.13.
- **Driver**: official `neo4j==6.3.0`.
- **Structured parsing**: `PyYAML==6.0.3` plus standard library Markdown/Git parsing.
- **Existing development lifecycle**: GitHub Spec Kit v1.0.4.
- **Existing CI**: TypeScript/application CI and Spec Kit CI remain independent authoritative gates.

## Constitution Check — Pre-implementation

### I. Spec before implementation
PASS. Feature 009 is specified/planned/tasks-defined before production engineering-tool code is added.

### II. Backend-agnostic frontend
PASS. No web/backend application boundary changes are required. Neo4j is not imported by `apps/web`, `apps/api`, or shared application contracts.

### III. Server authority/authorization
N/A to business authorization. Engineering graph never becomes an authorization source.

### IV. Strict types/tests/CI
PASS. New Python unit/integration checks are additive. Existing TS/PostgreSQL/browser gates are not relaxed.

### V. Simplicity/evolvability
PASS. V1 deliberately excludes AST graphing, embeddings, AI-inferred edges and autonomous distributed scheduling. Seven labels/eight relationship names are enough to prove value.

## Repository Structure

```text
engineering-graph/
├── README.md
├── .env.example
├── compose.yml
├── pyproject.toml
├── requirements.txt
├── config.yaml
├── schema/
│   ├── nodes.yaml
│   ├── relationships.yaml
│   └── constraints.cypher
├── queries/
│   ├── impact.cypher
│   ├── ready-tasks.cypher
│   ├── conflicts.cypher
│   ├── drift.cypher
│   ├── agent-context.cypher
│   ├── stats.cypher
│   └── pr-traceability.cypher
├── src/engineering_graph/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── model.py
│   ├── parser.py
│   ├── extract.py
│   ├── git.py
│   ├── store.py
│   ├── schema.py
│   ├── sync.py
│   ├── validator.py
│   ├── context.py
│   └── planner.py
└── tests/
    ├── fixtures/
    ├── test_parser.py
    ├── test_extract.py
    ├── test_validator.py
    └── test_planner.py
```

Repository integration:

```text
.github/workflows/engineering-graph.yml
AGENTS.md
.specify/templates/* (graph-friendly guidance only)
docs/architecture/graph-engineering.md
docs/adr/0017-graph-engineering-control-plane.md
```

## Extraction Pipeline

```text
Repository checkout
   ├── specs/**/spec.md
   ├── specs/**/tasks.md
   ├── specs/**/plan.md
   ├── docs/adr/*.md
   ├── referenced repository paths
   ├── git log / merge commits
   └── GitHub event JSON (when available)
           ↓
Deterministic extractors
           ↓
In-memory GraphModel
           ├── canonical-id validation
           ├── explicit-reference validation
           └── task-cycle precheck
           ↓
Neo4j Store
           ├── constraints/indexes
           ├── upsert nodes/edges
           └── prune stale projection
```

No extractor calls an LLM.

## Parser Rules

### Spec

From directory name + H1/status:

```text
specs/007-opportunity-workflow/spec.md
→ SPEC-007-OPPORTUNITY-WORKFLOW
```

### Requirements

Recognize feature-local identifiers with deterministic regex:

```text
FR-001
SC-001
```

Create `Requirement` nodes linked `REALIZED_BY` → Spec.

### Tasks

Recognize Spec Kit checkbox syntax:

```text
- [x] T040 [P] [US1] ...
```

Status comes only from checkbox. `[P]`, user-story and phase headings become properties.

### ADRs

Parse `docs/adr/NNNN-slug.md`; explicit `ADR-NNNN` references in spec/plan/tasks create `CONSTRAINED_BY` evidence where the source is Spec-level.

### Paths

Repository-like paths referenced by tasks/frontmatter become `CodeArtifact` or `Test`. Test classification uses deterministic path/name patterns (`test`, `tests`, `.test.`, `.spec.`, `e2e`, Storybook stories).

### Dependencies

Only explicit dependencies create `DEPENDS_ON` edges. Supported sources:

- optional frontmatter `graph.depends_on`;
- task text directive `depends: T001,T002`;
- versioned graph metadata conventions documented in README.

Phase ordering is NOT converted into dependency edges automatically.

## Git/PR Projection

### Merged PRs

Local Git merge commits matching GitHub merge conventions create PullRequest nodes. Changed paths are read from the merge commit diff and connected through `CHANGES`.

### Current PR in Actions

When `GITHUB_EVENT_PATH` identifies a pull request, ingest:

- PR number/title/state/url/head/base SHA/body;
- changed files from checked-out Git diff;
- explicit Task IDs/spec references in PR body.

Task IDs are resolved relative to explicitly named spec path/ID. Ambiguous `T001` without a spec namespace is not linked.

## Neo4j Schema

Constraints use composite `(repository, canonicalId)` uniqueness per label. Path nodes additionally index `(repository,path)`. Task status, Spec status and PR number get useful indexes where supported.

The schema is initialized idempotently with `CREATE CONSTRAINT ... IF NOT EXISTS` / `CREATE INDEX ... IF NOT EXISTS`.

## Sync Semantics

`graph sync` defaults to full projection for the current repository:

1. create `syncRunId`;
2. extract full model;
3. validate extraction;
4. upsert all nodes;
5. upsert all relationships;
6. prune stale relationships/nodes for this repository;
7. print counts + source revision.

Database mutations happen only in the sync/maintenance CLI. Implementation agents do not write Neo4j directly.

## Validator

Rules return deterministic `InvariantResult` records. Configurable rules include:

```text
duplicate-id              error (pre-write)
dangling-reference        error
task-dependency-cycle     error
enforced-spec-no-task     error
completed-task-no-code    warning by default
completed-task-no-test    warning by default
critical-requirement-no-test warning by default
adr-no-consumer           warning
```

Feature 009 itself is marked graph-enforced after bootstrap validation is green. Historical 001–004 remain allowed to have traceability warnings.

## Query API / CLI

```text
graph doctor [--wait SECONDS]
graph schema
graph sync [--repo-root PATH] [--github-event PATH]
graph validate [--json]
graph impact ID [--depth N] [--json]
graph ready [--spec ID] [--json]
graph conflicts [--spec ID] [--json]
graph context TASK-ID [--format markdown|json] [--output PATH]
graph waves [--spec ID] [--json]
graph stats [--json]
```

The installed console script name is `graph-engineering`; `python -m engineering_graph` is equivalent.

## Context Builder

Traversal is task-centered and bounded. Default budget:

```text
maxDepth = 3
maxNodes = 80
```

The package never embeds full code files automatically. It provides exact source paths + graph evidence, leaving the agent to read only what it needs.

## Execution Planner

1. load pending tasks + explicit dependency graph;
2. detect cycles;
3. determine READY/BLOCKED;
4. load implementation/test artifact overlap;
5. topologically schedule a maximal conflict-free set per wave;
6. produce JSON/human report.

The planner does not spawn agents or modify Git.

## Spec Kit Integration

```text
$ speckit-specify
      ↓
graph sync

$ speckit-plan
      ↓
graph sync + impact

$ speckit-tasks
      ↓
graph sync + ready/conflicts/waves

$ speckit-implement
      ↓
graph context SPEC:TASK
      ↓
agent/worktree execution

PR
      ↓
graph sync + validate + drift queries
```

Neo4j unavailable locally → fall back to reading canonical files; no product behavior changes.

## CI Design

Dedicated workflow uses ephemeral Neo4j:

```text
Neo4j 2026.07.1 service
Python 3.13
pip install requirements
unit tests
wait for Bolt
schema
sync
validate
smoke impact/ready/conflicts/context/stats
```

Trigger paths include `engineering-graph/**`, `specs/**`, `docs/adr/**`, `.specify/**`, `AGENTS.md`, and the workflow itself. For source-only changes, sync/validation may run on pull requests when configured globally later; initial workflow focuses on graph-affecting metadata/tool changes to avoid unnecessary CI cost.

## Delivery

This PR implements the complete V1 control-plane foundation in one graph-specific MR. Multi-tenancy feature 008 remains a separate stream and is not coupled to Neo4j.

Future PRs may add:

- V2 richer agent context heuristics;
- V3 first-class agent/worktree execution records;
- V4 GraphRAG/vector search;

only after measured need.

## Constitution Check — Post-design

PASS. Neo4j is explicitly derived/disposable, no product package imports it, the toolchain has deterministic tests/CI, and V1 avoids premature semantic/agent orchestration complexity.
