# Engineering Graph

Repository-local Neo4j control plane for Spec-Driven and Agent-Driven engineering.

## Authority boundary

Git-backed artifacts are canonical. Neo4j is a rebuildable projection used for traceability, impact analysis, drift checks, bounded agent context and execution planning. No application runtime depends on this directory.

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
graph-engineering impact ADR-0017 --depth 3 --json
graph-engineering ready --spec SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE --json
graph-engineering conflicts --spec SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE --json
graph-engineering drift --json
graph-engineering context SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE:T061 --format markdown
graph-engineering waves --spec SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE --json
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

## Context packages

`context` returns a bounded package around one task. It includes the parent spec, requirements, ADRs, dependencies, likely code/tests and PR evidence up to configured `max_depth`/`max_nodes` limits.

The package is navigation context only. Agents must open/edit the canonical paths named by the package rather than attempting to modify Neo4j.

Generated packages should go under `engineering-graph/context-packages/` or `engineering-graph/out/`; both are ignored by Git.

## Execution waves

`waves` computes a topological task plan from explicit `DEPENDS_ON` relationships and prevents tasks sharing implementation/test artifacts from occupying the same wave. It never replaces review, CI, branch ownership or worktree discipline.

## Drift versus validation

`drift` exposes raw deterministic invariant evidence from the checked-in Cypher query. `validate` applies the repository's configured severity policy (`error`, `warning`, `off`) plus structural checks such as task dependency cycles. Use `drift` for inspection and `validate` as the CI decision surface.

## CI

`.github/workflows/engineering-graph.yml` starts an ephemeral Neo4j instance, installs this package, runs unit tests, validates schema definitions, performs two full syncs, executes the validator and smoke-tests impact/ready/conflicts/drift/context plus waves/stats.

Existing application CI and Spec Kit CI remain independent and authoritative for their domains.

## Rebuild / recovery

The graph is disposable:

```bash
graph-engineering reset --yes
graph-engineering schema
graph-engineering sync
graph-engineering validate
```

No canonical knowledge is lost by deleting the graph.

## Deliberately deferred

V1 does not include AST-wide inference, embeddings, GraphRAG, AI-created relationships, a distributed scheduler or direct agent writes to Neo4j. Those capabilities require separate specs and evidence that the deterministic graph provides value first.
