# Quickstart: Agent Context Graph

## Prerequisite

V1 Engineering Graph must be available and synchronized.

```bash
cd engineering-graph
. .venv/bin/activate
docker compose up -d neo4j
graph-engineering doctor --wait 60
graph-engineering schema
graph-engineering sync
graph-engineering validate
```

## Generate one package

```bash
graph-engineering context-batch \
  --task SPEC-010-AGENT-CONTEXT-GRAPH:T021
```

Expected derived output:

```text
engineering-graph/context-packages/
└── SPEC-010-AGENT-CONTEXT-GRAPH/
    └── SPEC-010-AGENT-CONTEXT-GRAPH_T021/
        ├── context.json
        ├── context.md
        ├── codex.md
        └── claude.md
```

## Generate all READY packages for one spec

```bash
graph-engineering context-batch \
  --spec SPEC-010-AGENT-CONTEXT-GRAPH
```

BLOCKED tasks are not selected by default.

## Validate freshness

```bash
graph-engineering context-validate \
  engineering-graph/context-packages/SPEC-010-AGENT-CONTEXT-GRAPH/SPEC-010-AGENT-CONTEXT-GRAPH_T021/context.json \
  --strict
```

Strict validation fails when the package Git revision is stale or cannot be verified.

## Render an adapter directly

```bash
graph-engineering context-adapt path/to/context.json --agent codex
graph-engineering context-adapt path/to/context.json --agent claude
```

## Agent workflow

```text
Task ID
  ↓
Graph sync + validate
  ↓
Generate context package
  ↓
Strict freshness validation
  ↓
Read codex.md / claude.md
  ↓
Open canonical repository files referenced by the package
  ↓
Implement + validate using repository commands
```

The generated package is navigation context. Never edit it as the canonical implementation/specification source.

## Regenerate

Packages are disposable:

```bash
rm -rf engineering-graph/context-packages/*
graph-engineering context-batch --spec SPEC-010-AGENT-CONTEXT-GRAPH
```

## Budgets

Defaults come from `engineering-graph/config.yaml`.

```yaml
context:
  max_depth: 3
  max_nodes: 80
  max_bytes: 65536
```

CLI overrides may lower/raise them within validated limits.
