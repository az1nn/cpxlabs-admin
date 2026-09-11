# Data Model: Agent Context Graph

## Derived artifact model

All entities in this feature are engineering-only derived artifacts. They do not extend the product runtime data model and are not persisted as canonical knowledge in Neo4j.

## ContextPackage

```text
ContextPackage
├── packageVersion: string
├── repository: string
├── sourceRevision: string
├── taskId: string
├── generatedAt: ISO-8601 string
├── freshness: current | stale | unknown
├── budget: ContextPackageBudget
├── summary: ContextPackageSummary
├── task: GraphEntity
├── spec?: GraphEntity
├── requirements: GraphEntity[]
├── adrs: GraphEntity[]
├── dependencies: GraphEntity[]
├── codeArtifacts: GraphEntity[]
├── tests: GraphEntity[]
├── pullRequests: GraphEntity[]
└── provenance: ContextProvenance[]
```

## ContextPackageBudget

```text
maxDepth: integer 1..5
maxNodes: integer 1..500
maxBytes: integer >= 1024
```

## ContextPackageSummary

```text
includedNodes: integer
truncatedNodes: integer
renderedBytes: integer
truncated: boolean
```

`renderedBytes` is measured on the canonical compact JSON payload before pretty/human projections.

## GraphEntity

Portable entity object projected from V1 graph evidence. The package does not invent additional semantic fields.

Expected common fields:

```text
canonicalId?: string
path?: string
title?: string
text?: string
sourcePath?: string
status?: string
```

Unknown safe graph metadata may be preserved when already produced by deterministic V1 queries.

## ContextProvenance

```text
entityId: string
relation: string
via?: string
sourcePath?: string
```

Examples:

```text
SPEC-010...:FR-001 --REALIZED_BY--> SPEC-010...
SPEC-010... --DECOMPOSED_INTO--> SPEC-010...:T012
SPEC-010... --CONSTRAINED_BY--> ADR-0018
SPEC-010...:T012 --IMPLEMENTED_BY--> engineering-graph/src/...
SPEC-010...:T012 --VALIDATED_BY--> engineering-graph/tests/...
```

Provenance is explanatory evidence, not a new source of truth.

## PackageManifest

For generated package directories:

```text
manifestVersion: "1"
repository: string
sourceRevision: string
specId?: string
tasks:
  - taskId: string
    directory: string
    contextJson: string
    contextMarkdown: string
    codexHandoff: string
    claudeHandoff: string
```

A manifest is deterministic for task selection/output-relative paths except generation timestamps inside individual packages.

## FreshnessReport

```text
status: current | stale | unknown
packageRevision: string
currentRevision?: string
strict: boolean
validSchema: boolean
messages: string[]
```

Rules:

- `current`: revisions equal;
- `stale`: revisions differ;
- `unknown`: Git HEAD unavailable;
- strict mode fails for stale/unknown;
- malformed package always fails.

## AgentHandoff

Agent-specific handoffs are renderings, not separate data stores.

Logical content:

```text
agent: codex | claude
repository
taskId
sourceRevision
contextPaths
canonicalPaths[]
validationCommands[]
sourceOfTruthNotice
```

Both adapters consume the same ContextPackage.

## Identity

Context package identity is logically:

```text
(repository, sourceRevision, taskId, budget)
```

Generated timestamp and filesystem destination are not part of semantic identity.

## Persistence

- Neo4j persists the rebuildable V1 graph projection.
- V2 packages are files under ignored `engineering-graph/context-packages/` or explicit ignored output directories.
- No PostgreSQL/product schema changes.
- No canonical package commit required or expected.
