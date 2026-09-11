# Research: Agent Context Graph

## Source-derived roadmap

The project source `graph-engineering-neo4j-spec-driven.md` defines V2 — Agent Context Graph with four deliverables:

1. Context Builder;
2. automatic creation of context packages;
3. Claude Code/Codex support;
4. Task → files → tests → ADR context.

The same source keeps GraphRAG, semantic embeddings and execution/worktree orchestration for later roadmap stages. This feature therefore improves the existing V1 Context Builder but does not pull V3/V4 concerns forward.

## Existing repository capability

V1 already provides:

- bounded task context traversal;
- Markdown/JSON rendering;
- task/spec/requirements/ADRs/dependencies/code/tests/PR evidence;
- context CLI command;
- graph validator and READY task query;
- ignored context-package output directories.

V2 should not replace these. It should add a stable package contract, freshness/provenance guarantees, batch generation and agent adapters.

## Current agent integration research

### Codex

OpenAI's current guidance treats `AGENTS.md` as persistent repository context and recommends using it as a concise map to deeper canonical documentation rather than a giant manual. OpenAI also recommends task prompts that name concrete file paths/components and relevant documentation.

Decision:

- keep `AGENTS.md` concise;
- generated task handoffs point to the context package and canonical paths;
- do not append per-task generated content into `AGENTS.md`;
- Codex adapter produces a task handoff Markdown file suitable for pasting/feeding into a Codex task, with explicit canonical-file navigation and validation commands.

### Claude Code

Public Anthropic guidance supports structured state/context and Git-backed incremental workflows, but no stable public requirement justifies coupling this project to a proprietary generated context-file schema.

Decision:

- Claude adapter consumes the same portable ContextPackage;
- emit a deterministic Markdown handoff/prompt file;
- do not mutate `CLAUDE.md` or create a Claude-only source of truth;
- keep adapter semantics equivalent to Codex where possible.

## Package contract decision

Introduce `packageVersion = "1"` with a portable JSON contract and Markdown projection. JSON is the machine contract; Markdown is the human/agent-readable view.

Operational metadata:

- `generatedAt` may differ per generation;
- output path may differ;
- semantic comparison excludes these fields.

Canonical identity/provenance:

- repository;
- sourceRevision;
- taskId;
- relation/source-path provenance for included evidence.

## Freshness decision

A context package is valid only relative to the repository revision from which its graph projection was built.

Modes:

- inspect: report `current | stale | unknown`, exit zero unless package malformed;
- strict: stale or unknown revision is non-zero.

The validator compares package `sourceRevision` with `git rev-parse HEAD`. It does not infer semantic equivalence across revisions.

## Budget decision

V1 supports `maxDepth` and `maxNodes`. V2 adds `maxBytes` at rendering/package assembly time.

Order of deterministic admission remains stable:

1. Task;
2. parent Spec;
3. Requirements;
4. ADRs;
5. dependencies;
6. code artifacts;
7. tests;
8. PR evidence.

If byte budget is exceeded, lower-priority evidence is removed from the end of deterministic sorted groups and truncation is reported explicitly.

## Batch-generation decision

Add a batch command that can select:

- all READY tasks for one spec (default mode);
- explicit task IDs.

BLOCKED tasks are excluded from READY mode and require explicit selection.

Batch output layout:

```text
engineering-graph/context-packages/
└── <spec-id>/
    └── <task-id>/
        ├── context.json
        ├── context.md
        ├── codex.md
        └── claude.md
```

The directory is derived/ignored and can be deleted at any time.

## Agent adapter decision

Adapters are pure renderers over ContextPackage. They MUST NOT query Neo4j.

Shared handoff content:

- task identity;
- source revision;
- context package paths;
- canonical files to open;
- architecture/test evidence;
- instruction to treat Git files as authoritative;
- expected validation commands from repository conventions.

Adapters do not launch agents or allocate worktrees in V2.

## CI decision

Extend the existing Engineering Graph workflow rather than create a competing graph workflow. Add smoke coverage for:

- single-task package generation;
- READY batch generation;
- package validation/freshness;
- Codex/Claude handoffs;
- deterministic semantic package comparison;
- product-runtime dependency isolation remains unchanged.

## Deferred

The following remain separate future specs:

- V3 task execution/worktree allocation/reservations;
- V4 GraphRAG/semantic retrieval/vector search;
- AI-inferred authoritative graph edges;
- agent process spawning or autonomous merges.
