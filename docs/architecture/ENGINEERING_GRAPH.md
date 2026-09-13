# Engineering Control Plane

## Purpose

The Engineering Graph turns relationships that are implicit across Spec Kit artifacts, ADRs, code, tests and pull requests into a queryable projection for humans, CI and coding agents.

It is intentionally not part of the business runtime. Git-backed files remain the source of truth; the Neo4j database and all generated context/execution/retrieval state can be deleted and rebuilt at any time.

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
          ├──────────────────────────────┐
          ▼                              ▼
engineering-graph extractor      GraphRAG corpus/chunker
          │                              │
          ▼                              ▼
validated GraphModel             derived semantic index
          │                              │
          ▼                              │
Neo4j deterministic projection          │
          │                              │
   ┌──────┼───────────────┐              │
   ▼      ▼               ▼              │
 queries  validator       planners       │
   │      │               │              │
 impact  drift       ready/conflicts     │
                         /waves           │
   │      │               │              │
   └──────┴──────┬────────┘              │
                 ▼                       │
        bounded agent context            │
                 │                       │
                 └──────────┬────────────┘
                            ▼
                 semantic seeds + bounded
                 deterministic graph expansion
```

Application packages have no dependency on Neo4j, GraphRAG or the Python engineering toolchain.

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

The schema intentionally has a small vocabulary. New labels/relationship types require a material design change rather than ad-hoc insertion. GraphRAG does not add similarity or inferred relationship types.

## Identity

Every canonical graph node uses composite identity:

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

## V2 context building

Context packages are bounded subgraphs keyed by a task. The builder returns only relevant parent spec, requirements, ADRs, dependencies, implementation paths, tests and PR evidence.

Budgets are explicit (`maxDepth`, `maxNodes`, `maxBytes`). Truncation is surfaced rather than silently producing an unbounded prompt.

This enables:

```text
Task → Engineering Graph → bounded ContextPackage → Codex/Claude/other agent
```

The generated package is still derived context. Agents follow its repository paths back to canonical files before making changes.

## V3 execution planning and allocation

Tasks form a DAG only when explicit `DEPENDS_ON` evidence exists. Phase order is not automatically converted to dependency edges.

The planner computes:

- READY tasks;
- BLOCKED tasks and blockers;
- cycles;
- artifact-overlap conflicts;
- topological execution waves.

A wave never contains two tasks that share an explicitly linked implementation/test artifact. V3 binds the plan to a Git revision, creates isolated Git worktrees and records local derived leases while leaving canonical Task state unchanged.

Execution manifests, leases and handoffs are disposable operational state. Dirty worktree contents are user data and are protected from automatic destructive cleanup.

## V4 GraphRAG

GraphRAG adds semantic discovery without modifying the canonical graph.

```text
Git-tracked eligible files
        │
        ▼
 deterministic chunks
        │
        ▼
 derived embedding index
        │
        ▼
 natural-language retrieval
        │
        ▼
 semantic hit source paths
        │
        ▼
 existing sourcePath/path graph anchors
        │
        ▼
 bounded traversal over existing relationships
```

The semantic index lives outside Neo4j under `engineering-graph/.graphrag/` by default. It is bound to repository revision, provider/model identity, dimensions and chunk configuration.

Only Git-tracked eligible files can enter the corpus. Semantic scores are retrieval evidence only. They never create `SIMILAR_TO`, `RELATED_TO`, inferred `DEPENDS_ON` or any other canonical edge.

Two provider modes exist:

- `hashing`: deterministic offline retrieval surrogate for CI/mechanics;
- `http`: configurable learned embedding endpoint without a mandatory SDK dependency.

GraphRAG result packages keep semantic hits, deterministic graph anchors and graph evidence as separate layers. See `docs/architecture/GRAPHRAG.md` and ADR-0020.

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
Python unit/integration tests
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
V1 query smokes
      ↓
V2 ContextPackage freshness/reproducibility
      ↓
V3 ExecutionManifest/wave smokes
      ↓
V4 semantic-index reproducibility/freshness
      ↓
V4 semantic seed → existing graph expansion
      ↓
prove GraphRAG query leaves graph stats unchanged
```

A graph error blocks that workflow. Warnings remain visible but non-blocking unless promoted in `engineering-graph/config.yaml`.

## Failure model

Neo4j outage does not break the product runtime. Local development may fall back to canonical repository files. GraphRAG index failure or embedding endpoint failure also does not affect product runtime.

Semantic retrieval can operate without graph expansion if Neo4j is unavailable, but such results remain semantic evidence only. CI graph failures must never be hidden by weakening application tests or silently treating generated state as authoritative.

## Delivered roadmap

### V1 — Engineering Graph control plane

- deterministic repository projection;
- traceability/impact/drift;
- task DAG/conflicts/waves;
- CI architecture validation.

### V2 — Agent Context Graph

- portable revision-aware ContextPackage;
- deterministic budgets/hashes;
- Codex/Claude handoffs;
- strict freshness/disposable regeneration.

### V3 — Execution Graph

- revision-bound ExecutionManifest;
- worktree allocation;
- local execution reservations/leases;
- conflict-aware waves and safe release semantics.

### V4 — GraphRAG

- semantic retrieval over Git-tracked repository content;
- revision/provider/model-bound derived vector index;
- graph expansion around semantic seeds;
- ADR/spec/requirement discovery;
- read-only composition with the deterministic graph.

## Governance invariant

Across V1–V4, canonical knowledge remains in Git-backed files and validated deterministic graph edges come only from explicit repository evidence. GraphRAG may help humans/agents discover possible relationships or relevant files, but promotion of semantic inference into graph authority would require a later ADR defining review, provenance and validation semantics.
