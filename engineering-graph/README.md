# Engineering Graph

Repository-local Neo4j control plane for Spec-Driven and Agent-Driven engineering.

## Authority boundary

Git-backed artifacts are canonical. Neo4j is a rebuildable projection used for traceability, impact analysis, drift checks, bounded agent context and execution planning. Generated context packages are also disposable derived artifacts. No application runtime depends on this directory.

## Local setup

```bash
cd engineering-graph
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
docker compose up -d neo4j
graph-engineering doctor --wait 60
graph-engineering schema
graph-engineering sync
graph-engineering validate
```

Neo4j Browser is exposed on `http://127.0.0.1:7474`; Bolt uses `bolt://127.0.0.1:7687`.

## Core commands

```bash
graph-engineering doctor --wait 60
graph-engineering schema
graph-engineering sync --json
graph-engineering validate --json
graph-engineering stats --json
graph-engineering impact ADR-0018 --depth 3 --json
graph-engineering ready --spec SPEC-010-AGENT-CONTEXT-GRAPH --json
graph-engineering conflicts --spec SPEC-010-AGENT-CONTEXT-GRAPH --json
graph-engineering drift --json
graph-engineering context SPEC-010-AGENT-CONTEXT-GRAPH:T021 --format markdown
graph-engineering waves --spec SPEC-010-AGENT-CONTEXT-GRAPH --json
graph-engineering reset --yes
```

The five fundamental inspection surfaces are `impact`, `ready`, `conflicts`, `drift`, and `context`; `waves` builds on the task DAG/artifact overlap for execution planning.

## V1 graph model

Seven node labels:

- `Requirement`
- `Spec`
- `ADR`
- `Task`
- `CodeArtifact`
- `Test`
- `PullRequest`

Eight relationship names:

- `REALIZED_BY`
- `CONSTRAINED_BY`
- `DECOMPOSED_INTO`
- `DEPENDS_ON`
- `IMPLEMENTED_BY`
- `VALIDATED_BY`
- `IMPLEMENTS`
- `CHANGES`

Node identity is `(repository, canonicalId)`. This prevents collisions when multiple repositories are projected into the same Neo4j database.

## Authoring conventions

The sync engine is intentionally deterministic. It consumes explicit repository evidence:

- Spec Kit `spec.md`, `plan.md`, `tasks.md`;
- stable `FR-###`, `SC-###`, `T###` identifiers;
- ADR filenames/explicit references;
- repository paths mentioned in task/spec metadata;
- Git revision and changed files;
- pull-request event metadata when available;
- optional YAML frontmatter.

Task phase order is not treated as a dependency. Add explicit `depends: T001,T002` evidence when dependency edges are required.

## V2 Agent Context Graph

V2 turns the bounded Context Builder into a revision-aware package contract that can be consumed consistently by different coding agents.

### Generate one task package

```bash
graph-engineering context-batch \
  --task SPEC-010-AGENT-CONTEXT-GRAPH:T021
```

### Generate all READY packages for a spec

```bash
graph-engineering context-batch \
  --spec SPEC-010-AGENT-CONTEXT-GRAPH \
  --json
```

READY mode excludes BLOCKED tasks. Use explicit `--task` only when you intentionally need a specific task package.

Each selected task receives:

```text
context.json   portable machine contract
context.md     human-readable context map
codex.md       Codex-oriented handoff
claude.md      Claude Code-oriented handoff
```

A top-level `manifest.json` records the selected tasks, source revision and package-relative paths.

### Validate freshness before implementation

```bash
graph-engineering context-validate \
  context-packages/.../context.json \
  --strict
```

Strict mode fails if the package revision does not equal current Git HEAD or HEAD cannot be resolved. Non-strict mode can be used to inspect stale packages without treating them as current context.

### Render an adapter from an existing package

```bash
graph-engineering context-adapt context.json --agent codex
graph-engineering context-adapt context.json --agent claude
```

Adapters are pure renderers. They never query Neo4j and never become a separate source of truth.

### Context budgets

```yaml
context:
  max_depth: 3
  max_nodes: 80
  max_bytes: 65536
```

Node/depth limits constrain graph admission. `max_bytes` provides a deterministic final semantic JSON budget. When evidence must be omitted, the package reports `truncatedNodes`, `renderedBytes` and `truncated=true`.

### Package lifecycle

```text
sync
 ↓
validate graph
 ↓
generate package
 ↓
strict freshness validation
 ↓
agent opens canonical files
 ↓
implementation/tests
 ↓
discard/regenerate when revision changes
```

Generated packages live under `engineering-graph/context-packages/` by default and are ignored by Git.

## Context package authority

The package is navigation context only. Agents must open/edit the canonical paths named by the package rather than editing generated files or attempting to modify Neo4j.

The portable JSON package carries repository, source revision, task identity, budgets, summary, linked graph evidence and provenance. Markdown/agent handoffs are renderings of the same package.

## Execution waves

`waves` computes a topological task plan from explicit `DEPENDS_ON` relationships and prevents tasks sharing implementation/test artifacts from occupying the same wave. It never replaces review, CI, branch ownership or worktree discipline.

Worktree allocation and agent execution remain V3 concerns; V2 only prepares validated context packages.

## Drift versus validation

`drift` exposes raw deterministic invariant evidence from the checked-in Cypher query. `validate` applies the repository's configured severity policy (`error`, `warning`, `off`) plus structural checks such as task dependency cycles. Use `drift` for inspection and `validate` as the CI decision surface.

## CI

`.github/workflows/engineering-graph.yml` starts an ephemeral Neo4j instance, installs this package, runs unit tests, validates schema definitions, performs two full syncs, executes the validator and smoke-tests graph queries plus Agent Context Graph package generation/validation/adapters.

Existing application CI and Spec Kit CI remain independent and authoritative for their domains.

## Rebuild / recovery

The graph and generated packages are disposable:

```bash
rm -rf context-packages/*
graph-engineering reset --yes
graph-engineering schema
graph-engineering sync
graph-engineering validate
graph-engineering context-batch --spec SPEC-010-AGENT-CONTEXT-GRAPH
```

No canonical knowledge is lost by deleting either projection.

## Deliberately deferred

V2 does not include AST-wide semantic inference, embeddings, GraphRAG, AI-created authoritative relationships, automatic worktree allocation, agent spawning or autonomous merging. Those capabilities require separate specs and MRs.
