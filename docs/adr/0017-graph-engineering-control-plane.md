# ADR-0017: Neo4j Engineering Graph as a Disposable Control-Plane Projection

**Status**: Accepted  
**Date**: 2026-09-10

## Context

The repository is Spec-Driven and increasingly agent-assisted. Requirements, specs, ADRs, tasks, code, tests and pull requests are versioned, but their relationships are mostly implicit. Agents must repeatedly scan broad context to infer impact, dependencies, executable tasks and validation coverage.

A graph model can make those relations explicit, but introducing Neo4j risks creating a second source of truth or a runtime dependency if the boundary is not strict.

## Decision

Adopt Neo4j Community as an **engineering-only, rebuildable projection** of canonical repository artifacts.

Canonical authority remains:

```text
Git
├── Markdown specs / plans / tasks
├── ADRs
├── code
├── tests
└── Git/PR history
```

The projection is built by deterministic extractors and may be destroyed/rebuilt at any time.

Initial graph model is intentionally bounded to seven node labels:

```text
Requirement
Spec
ADR
Task
CodeArtifact
Test
PullRequest
```

and eight relationship names:

```text
REALIZED_BY
CONSTRAINED_BY
DECOMPOSED_INTO
DEPENDS_ON
IMPLEMENTED_BY
VALIDATED_BY
IMPLEMENTS
CHANGES
```

## Operational Boundary

Neo4j:

- lives under `engineering-graph/`;
- has its own Compose lifecycle;
- is used by local engineering tooling and a dedicated GitHub Actions graph workflow;
- is not imported by `apps/web`, `apps/api`, or application contract packages;
- does not participate in business request handling;
- does not replace PostgreSQL, Spec Kit, Git, CI, authentication, authorization or audit.

If Neo4j is unavailable, engineering graph assistance is temporarily unavailable. Product runtime behavior is unaffected.

## Extraction Policy

V1 relationships are created only from deterministic evidence:

- Spec Kit identifiers and checkbox/task syntax;
- explicit Markdown/YAML graph metadata;
- explicit ADR/task/spec references;
- repository path references;
- local Git metadata;
- GitHub Actions pull-request event metadata.

LLM-inferred graph edges are prohibited in V1. Missing evidence stays missing.

## Sync Policy

Full sync is the default. Each run:

1. parses the canonical checkout;
2. validates canonical IDs/references;
3. upserts observed nodes/edges;
4. stamps a sync run id/source revision;
5. prunes stale derived state.

This favors correctness and rebuildability over premature incremental-sync complexity.

## Validation Policy

Graph structural invariants can be CI errors. Historical/incomplete traceability can begin as warnings through versioned configuration. The distinction is explicit; validation is never globally disabled just to obtain a green build.

## Agent Policy

Agents may query the graph to build bounded context, impact sets, ready-task lists and conflict-free execution waves. Agents still edit canonical repository files, never Neo4j directly.

The execution planner produces plans only; it is not an autonomous merge/scheduling authority.

## Deferred Decisions

The following require separate evidence/ADRs if introduced:

- AST-wide dependency graph;
- GraphRAG/vector search/embeddings;
- AI-inferred relationships;
- first-class Agent/Worktree/Commit graph nodes;
- distributed task scheduling;
- Neo4j Enterprise or Graph Data Science dependencies.

## Consequences

### Positive

- explicit requirement-to-code/test/PR traceability;
- cheap architectural impact analysis;
- task DAG/readiness and overlap visibility;
- smaller, deterministic context packages for agents;
- CI can detect a class of spec/architecture drift;
- graph can be rebuilt from Git after loss/corruption.

### Costs

- Python/Neo4j engineering toolchain must be maintained;
- extractors depend on stable repository conventions;
- explicit metadata is sometimes needed where deterministic parsing cannot infer intent safely;
- an additional CI job consumes time/resources.

These costs are accepted because Neo4j remains isolated from product runtime and V1 is deliberately narrow.
