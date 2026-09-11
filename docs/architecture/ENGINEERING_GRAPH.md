# Engineering Control Plane

## Purpose

The Engineering Graph turns relationships that are implicit across Spec Kit artifacts, ADRs, code, tests and pull requests into a queryable projection for humans, CI and coding agents.

It is intentionally not part of the business runtime. Git-backed files remain the source of truth; the Neo4j database can be deleted and rebuilt at any time.

## System boundary

```text
Git repository (canonical)
  ├── .specify/
  ├── specs/
  ├── docs/adr/
  ├── apps/ + packages/
  ├── tests / e2e / stories
  └── Git + PR metadata
          │
          ▼
engineering-graph extractor
          │
          ▼
validated GraphModel
          │
          ▼
Neo4j projection
          │
   ┌──────┼───────────────┐
   ▼      ▼               ▼
 queries  validator       planners
   │      │               │
 impact  drift       ready/conflicts/waves
   │      │               │
   └──────┴──────┬────────┘
                 ▼
        bounded agent context
```

Application packages have no dependency on Neo4j or the Python engineering toolchain.

## Canonical graph model

### Labels

`Requirement`, `Spec`, `ADR`, `Task`, `CodeArtifact`, `Test`, `PullRequest`.

### Relationships

```text
Requirement --REALIZED_BY------> Spec
Spec --------CONSTRAINED_BY----> ADR
Spec --------DECOMPOSED_INTO---> Task
Spec --------DEPENDS_ON---------> Spec
Task --------DEPENDS_ON---------> Task
Task --------IMPLEMENTED_BY-----> CodeArtifact
Task --------VALIDATED_BY-------> Test
PullRequest --IMPLEMENTS--------> Task
PullRequest --CHANGES-----------> CodeArtifact/Test
```

The schema intentionally has a small vocabulary. New labels/relationship types require a material design change rather than ad-hoc insertion.

## Identity

Every node uses composite identity:

```text
(repository, canonicalId)
```

Examples:

```text
az1nn/cpxlabs-admin + SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE
az1nn/cpxlabs-admin + SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE:T061
az1nn/cpxlabs-admin + ADR-0017
az1nn/cpxlabs-admin + apps/api/src/app.ts
```

Local Spec Kit IDs are namespaced under their Spec so multiple `T001`/`FR-001` identifiers do not collide.

## Extraction contract

The V1 extractor is deterministic and conservative. It reads explicit evidence only:

1. optional Markdown/YAML frontmatter;
2. Spec Kit identifiers and checkboxes;
3. explicit dependency markers;
4. ADR identifiers;
5. repository paths;
6. Git revision/change metadata;
7. PR event metadata when provided by GitHub Actions.

It does not infer relationships from semantic similarity or LLM judgment.

Extraction first builds a typed in-memory `GraphModel`. Dangling explicit references and dependency cycles are detected before database writes. A sync run stamps every projected node/relationship and prunes stale derived entities after successful upsert.

## Drift validation

The Graph Validator runs configurable invariants with `error`, `warning` or `off` severity. Initial rules cover:

- enforced spec without task decomposition;
- task dependency cycles;
- completed task with no explicit implementation evidence;
- completed task with no explicit validation evidence;
- critical requirement with no validation path;
- ADR with no explicit consuming spec.

Historical retrofitted specs may downgrade selected evidence rules from error to warning because their pre-Spec-Kit history is incomplete by design.

## Context building

Context packages are bounded subgraphs keyed by a task. The builder returns only relevant parent spec, requirements, ADRs, dependencies, implementation paths, tests and PR evidence.

Budgets are explicit (`maxDepth`, `maxNodes`). Truncation is surfaced rather than silently producing an unbounded prompt.

This enables:

```text
Task → Engineering Graph → bounded context package → Codex/OpenCode/other agent
```

The generated package is still derived context. Agents follow its repository paths back to canonical files before making changes.

## Execution planning

Tasks form a DAG only when explicit `DEPENDS_ON` evidence exists. Phase order is not automatically converted to dependency edges.

The planner computes:

- READY tasks;
- BLOCKED tasks and blockers;
- cycles;
- artifact-overlap conflicts;
- topological execution waves.

A wave never contains two tasks that share an explicitly linked implementation/test artifact. This provides a conservative basis for parallel worktrees/agents without pretending concurrency is risk-free.

## Pull request traceability

When PR metadata is available, the graph connects PRs to changed code/tests and to explicitly referenced tasks/specs. This supports traversal such as:

```text
PR → Task → Spec ← Requirement
 │
 └→ CodeArtifact/Test
```

PR metadata is evidence, not a source for changing canonical task status.

## CI architecture gate

The Engineering Graph workflow is independent of application CI:

```text
Python unit tests
      ↓
Ephemeral Neo4j
      ↓
Schema init
      ↓
Full repository sync
      ↓
Second sync / idempotency smoke
      ↓
Graph validation
      ↓
Fundamental query smoke tests
      ↓
Architecture graph gate
```

A graph error blocks that workflow. Warnings remain visible but non-blocking unless promoted in `engineering-graph/config.yaml`.

## Failure model

Neo4j outage does not break the product runtime. Local development may fall back to canonical repository files. CI graph failures block only the engineering architecture gate and must never be hidden by weakening application tests or silently treating the graph as authoritative.

## Future roadmap

### V2 — richer agent context

- better explicit task-to-artifact authoring;
- context package manifests/hashes;
- worktree handoff helpers.

### V3 — execution orchestration

- worktree allocation;
- execution reservations/leases outside Neo4j authority;
- conflict-aware agent waves with merge sequencing.

### V4 — GraphRAG

- semantic retrieval over repository content;
- graph expansion around semantic seeds;
- ADR/spec discovery.

GraphRAG must remain retrieval assistance. It may propose relationships, but canonical/validated edges must still come from deterministic repository evidence unless a later ADR explicitly changes that governance model.
