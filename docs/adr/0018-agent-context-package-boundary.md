# ADR-0018: Portable Agent Context Package Boundary

- **Status**: Accepted
- **Date**: 2026-09-10
- **Decision owners**: cpxlabs-admin architecture
- **Related spec**: `SPEC-010-AGENT-CONTEXT-GRAPH`

## Context

The V1 Engineering Graph can already produce bounded task context from Neo4j. The V2 roadmap requires automatic context packages and support for Codex/Claude Code. A direct integration where each agent queries Neo4j independently would duplicate traversal semantics, couple the graph to specific vendors and make context difficult to reproduce or validate.

## Decision

Introduce a portable `ContextPackage` as the stable boundary between the Engineering Graph and coding agents.

```text
Neo4j
  │
  ▼
Context Builder
  │
  ▼
Portable ContextPackage JSON
  │
  ├── Markdown human view
  ├── Codex handoff
  └── Claude Code handoff
```

JSON is the machine-readable package contract. Markdown and agent-specific handoffs are pure renderings of that package.

The package records:

- repository and source Git revision;
- task identity;
- parent spec/requirements/ADRs;
- dependencies;
- implementation/test paths;
- PR evidence;
- traversal/render budgets;
- provenance and truncation statistics.

Generated context is disposable. Git/Markdown/code/tests remain authoritative.

## Agent integration

`AGENTS.md` stays concise and persistent. Per-task generated context is not appended to it. Codex and Claude adapters point agents to canonical repository paths named by the package.

Adapters:

- do not query Neo4j;
- do not mutate canonical files;
- do not launch agents;
- do not create worktrees;
- do not commit/push/merge.

Those execution concerns belong to the future Execution Graph.

## Freshness

A package identifies the Git revision from which its graph projection was derived. Strict validation fails when package revision differs from current repository HEAD or cannot be verified.

No semantic-equivalence inference is attempted across revisions.

## Consequences

### Positive

- one deterministic context contract across agents;
- vendor adapters remain thin and replaceable;
- reproducible debugging of what context an agent received;
- stale package detection;
- future Execution Graph can consume packages without knowing traversal details;
- future GraphRAG can enrich the builder behind the same boundary without making agents Neo4j clients.

### Negative

- package schema requires versioning discipline;
- generated files add an engineering artifact lifecycle;
- byte-budget enforcement adds normalization logic beyond V1 node budgets.

## Rejected alternatives

### Agent-specific Neo4j clients

Rejected because traversal and authority rules would diverge between agents.

### Generated task-specific `AGENTS.md` / `CLAUDE.md` as canonical context

Rejected because persistent instruction files should remain concise repository maps, while task context is disposable and revision-specific.

### Embed full canonical file contents in every package

Rejected for context explosion and duplication. V2 primarily supplies a precise map to canonical files; semantic content expansion belongs to a later GraphRAG design.

## Future compatibility

V3 Execution Graph may attach scheduling/worktree/lease metadata around a ContextPackage. V4 GraphRAG may enrich retrieval before package assembly. Neither changes Git authority or permits agent adapters to become sources of truth.
