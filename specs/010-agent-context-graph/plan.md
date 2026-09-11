# Implementation Plan: Agent Context Graph

## Summary

Extend the existing V1 Engineering Graph Context Builder into a deterministic, portable context-package system for Codex/Claude Code consumption. The implementation remains inside `engineering-graph/`, reuses V1 queries/store/settings, and does not add product-runtime dependencies.

## Architecture

```text
Git / Specs / ADRs / Code / Tests
              │
              ▼
        V1 Graph Sync
              │
              ▼
            Neo4j
              │
              ▼
       Context Builder V2
              │
      ┌───────┴────────┐
      ▼                ▼
 portable JSON      Markdown
 ContextPackage      rendering
      │
      ├───────────────┐
      ▼               ▼
 Codex adapter    Claude adapter
      │               │
      └───────┬───────┘
              ▼
      canonical file navigation
```

## Design decisions

### 1. Extend, do not replace, V1 context

`context.py` remains the central context-builder module. V2 evolves `ContextPackage` with repository/revision/version/provenance/summary metadata while preserving existing task evidence.

### 2. JSON is the portable machine contract

Markdown and agent handoffs are deterministic renderings of the same in-memory package. Adapters never query Neo4j.

### 3. Batch selection comes from V1 READY semantics

`context-batch --spec <id>` uses the same READY query semantics already used by planning. BLOCKED tasks require explicit task selection.

### 4. Freshness is Git revision equality

No semantic guessing across revisions. Package source revision must equal current HEAD in strict mode.

### 5. Three independent budgets

- graph depth;
- graph node count;
- rendered semantic JSON byte count.

Truncation is deterministic and observable.

### 6. Agents receive maps, not duplicated manuals

Codex/Claude handoffs contain task/package pointers, canonical paths and validation commands. They do not copy entire referenced source files into generated prompt artifacts.

## File layout

```text
engineering-graph/
├── src/engineering_graph/
│   ├── context.py              # evolved portable package model
│   ├── context_batch.py        # selection/generation/manifests
│   ├── context_validation.py   # schema + freshness validation
│   ├── agent_adapters.py       # Codex/Claude pure renderers
│   ├── cli.py                  # context/context-batch/context-validate
│   └── ... V1 modules
├── tests/
│   ├── test_context.py
│   ├── test_context_batch.py
│   ├── test_context_validation.py
│   └── test_agent_adapters.py
└── context-packages/           # ignored generated output

specs/010-agent-context-graph/
├── spec.md
├── research.md
├── data-model.md
├── plan.md
├── tasks.md
├── quickstart.md
├── analysis.md
├── convergence.md
└── checklists/requirements.md

docs/adr/0018-agent-context-package-boundary.md
```

## Package generation flow

```text
Task ID / READY Spec
       │
       ▼
ensure graph available
       │
       ▼
Context Builder traversal
       │
       ▼
normalize/sort evidence
       │
       ▼
apply depth/node budget
       │
       ▼
apply maxBytes budget
       │
       ▼
ContextPackage
       │
       ├── context.json
       ├── context.md
       ├── codex.md
       └── claude.md
```

## Validation flow

```text
context.json
   │
   ├── schema/package version
   ├── repository identity
   ├── task identity
   └── source revision
             │
             ▼
       git rev-parse HEAD
             │
      current / stale / unknown
```

## CLI surface

Existing command remains:

```bash
graph-engineering context <TASK-ID> --format markdown|json
```

New V2 commands:

```bash
graph-engineering context-batch --spec <SPEC-ID>
graph-engineering context-batch --task <TASK-ID> --task <TASK-ID>
graph-engineering context-validate <context.json> --strict
graph-engineering context-adapt <context.json> --agent codex|claude
```

`context-batch` emits all four files per selected task and a top-level manifest.

## Rollout

This PR is stacked on the V1 Graph Engineering PR until V1 merges. Before V2 becomes Ready for Review, its base must be retargeted to `master` and all CI gates rerun.

## Test strategy

### Offline unit tests

- semantic reproducibility;
- byte-budget truncation;
- package schema/freshness;
- agent adapter purity/determinism;
- READY batch selection with fake store/fixtures.

### Ephemeral Neo4j CI

After sync:

- generate one package for a known V2 task;
- generate READY packages for the V2 spec;
- validate current package strictly;
- render Codex/Claude adapters;
- delete generated packages and regenerate them;
- verify application graph-runtime isolation.

## Constitution checks

- Git authority preserved.
- Neo4j remains disposable engineering projection.
- generated packages are ignored derived outputs.
- no application package imports graph runtime.
- deterministic relationships only.
- no autonomous merge/execution behavior.

## Deferred

V3 Execution Graph owns worktree allocation, execution leases/reservations and agent scheduling. V4 owns semantic search/embeddings/GraphRAG.
