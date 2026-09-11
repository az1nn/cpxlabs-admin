# Agent Context Graph Architecture

## Purpose

The Agent Context Graph is V2 of the repository Engineering Graph roadmap. V1 makes engineering relationships explicit and queryable; V2 turns those relationships into revision-aware, bounded context packages that coding agents can consume reproducibly.

The feature does not change the product architecture. Neo4j and generated packages remain development/CI tooling.

## Authority model

```text
Canonical
Git / Specs / ADRs / Code / Tests / Git history
                 │
                 ▼
Derived
Engineering Graph (Neo4j)
                 │
                 ▼
Derived
Portable ContextPackage
                 │
          ┌──────┴──────┐
          ▼             ▼
      Codex map     Claude map
```

Authority always points upward. Agents may navigate from generated package to canonical files; generated package content never overrides the repository.

## Why a portable package boundary

Direct agent → Neo4j integration would create one query/traversal implementation per agent and make it difficult to answer a basic audit question: *what exact context did this agent receive?*

ADR-0018 therefore makes `ContextPackage` the stable machine boundary.

Benefits:

- one graph traversal policy;
- deterministic agent inputs;
- explicit Git-revision freshness;
- agent/vendor independence;
- future Execution Graph can schedule packages without understanding retrieval;
- future GraphRAG can enrich retrieval behind the builder without changing agent interfaces.

## Package structure

```text
ContextPackage v1
├── repository + sourceRevision
├── task identity
├── generatedAt + freshness
├── budgets
│   ├── maxDepth
│   ├── maxNodes
│   └── maxBytes
├── summary/truncation
├── task + parent spec
├── requirements + ADRs
├── dependencies
├── code artifacts + tests
├── PR evidence
└── provenance
```

`generatedAt` is operational metadata. Semantic reproducibility compares the rest of the normalized contract.

## Retrieval policy

V2 continues the deterministic V1 query model. No LLM chooses graph edges.

Admission order is stable:

1. Task;
2. parent Spec;
3. Requirements;
4. ADRs;
5. dependencies;
6. code artifacts;
7. tests;
8. PR evidence.

Depth/node budgets are applied during graph evidence admission. Byte budget is applied after portable package assembly. Lower-priority evidence is removed deterministically from the tail until the package fits; Task/Spec are mandatory.

If mandatory metadata cannot fit the configured byte budget, generation fails rather than silently emitting an oversized package.

## Provenance

Every selected relation is represented as explanatory provenance. Examples:

```text
Task     <- DECOMPOSED_INTO - Spec
Requirement - REALIZED_BY -> Spec
Spec - CONSTRAINED_BY -> ADR
Task - DEPENDS_ON -> Task
Task - IMPLEMENTED_BY -> CodeArtifact
Task - VALIDATED_BY -> Test
PullRequest - IMPLEMENTS -> Task
```

The package's provenance explains selection; it does not create graph truth.

## Freshness

A package records the Git revision used while building it.

```text
package.sourceRevision == git HEAD  → current
package.sourceRevision != git HEAD  → stale
Git HEAD unavailable                → unknown
```

`context-validate --strict` succeeds only for `current`. This is intentionally syntactic revision equality; V2 does not guess whether two revisions are semantically equivalent.

## Automatic packages

`context-batch --spec <SPEC>` asks the existing READY query for task selection. BLOCKED tasks are not included.

Explicit task generation bypasses READY selection only in the sense that a named package can be produced for inspection; it does not change task status or dependency authority.

Each package directory is replaced atomically enough for a local derived artifact: the old task directory is removed and regenerated from the current graph/revision. A top-level manifest provides a deterministic index.

## Agent adapters

Adapters are pure rendering functions over `ContextPackage`.

### Codex

The generated `codex.md`:

- points to repository `AGENTS.md`;
- names canonical files;
- records task/revision/context path;
- supplies relevant repository validation commands;
- states that generated context is derived.

Per-task content is not appended to persistent `AGENTS.md`.

### Claude Code

The generated `claude.md` uses the same package/evidence and remains ordinary portable Markdown. V2 does not establish a Claude-specific canonical knowledge store.

## Failure modes

### Neo4j unavailable

Context generation fails as an engineering-assistance operation. Product runtime/build behavior remains unchanged.

### Stale package

Strict validation fails before implementation.

### Budget exhausted

Optional lower-priority evidence is deterministically truncated and reported. If Task/Spec metadata alone cannot fit, generation fails.

### Missing task

Generation fails with an explicit lookup error; no guessed task identity.

### Adapter unavailable

CLI rejects unknown adapter names.

## CI

The Engineering Graph workflow owns V2 validation because the feature is an extension of graph tooling, not product behavior.

Required CI evidence:

- offline unit tests;
- application runtime isolation;
- ephemeral Neo4j sync/validation;
- single package generation;
- strict freshness pass;
- READY batch generation;
- Codex/Claude handoff generation;
- package delete/regenerate proof;
- semantic reproducibility proof.

Product CI and Spec Kit remain independent authority gates.

## Future extension seam

V3 Execution Graph may consume:

```text
READY Task
   ↓
ContextPackage
   ↓
worktree / reservation / agent assignment
```

V4 GraphRAG may enhance the retrieval phase before `ContextPackage` assembly. Neither future stage changes the source-of-truth direction.
