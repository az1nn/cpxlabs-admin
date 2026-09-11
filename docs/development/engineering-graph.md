# Engineering Graph Development Workflow

## Goal

Use Neo4j as a local/CI engineering projection over the repository to answer traceability, impact, drift, agent-context and parallelization questions without moving canonical project knowledge out of Git.

V2 Agent Context Graph adds revision-aware disposable context packages for Codex and Claude Code. These packages are navigation artifacts, not canonical documentation.

## Prerequisites

- Python 3.13+
- Docker / Docker Compose
- Git checkout with repository history

## First run

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

## Daily workflow

After pulling/changing specs, ADRs, tasks, code or tests:

```bash
cd engineering-graph
graph-engineering sync
graph-engineering validate
```

Before starting material work:

```bash
graph-engineering ready --spec SPEC-010-AGENT-CONTEXT-GRAPH
graph-engineering conflicts --spec SPEC-010-AGENT-CONTEXT-GRAPH
graph-engineering waves --spec SPEC-010-AGENT-CONTEXT-GRAPH
```

## Agent Context Graph workflow

### Generate one task package

```bash
graph-engineering context-batch \
  --task SPEC-010-AGENT-CONTEXT-GRAPH:T044
```

The default output lives below `engineering-graph/context-packages/` and is ignored by Git.

Each task directory contains:

```text
context.json
context.md
codex.md
claude.md
```

`context.json` is the portable machine contract. The other files are projections/renderings from the same package.

### Generate all READY packages for a spec

```bash
graph-engineering context-batch \
  --spec SPEC-010-AGENT-CONTEXT-GRAPH \
  --json
```

READY mode excludes BLOCKED tasks. Explicit `--task` selection can generate a package for inspection but does not change task readiness or dependency state.

### Validate freshness immediately before implementation

```bash
graph-engineering context-validate \
  context-packages/SPEC-010-AGENT-CONTEXT-GRAPH/SPEC-010-AGENT-CONTEXT-GRAPH_T044/context.json \
  --strict
```

The package revision comes from the Neo4j projection's `sourceRevision`, not from a fresh local assumption. Strict validation compares that graph revision with current Git HEAD and fails for `stale` or `unknown`.

This protects against the dangerous sequence:

```text
graph synced at revision A
        ↓
Git moves to revision B
        ↓
old Neo4j context queried
        ↓
strict context validation FAILS
```

### Agent handoffs

```bash
graph-engineering context-adapt context.json --agent codex
graph-engineering context-adapt context.json --agent claude
```

The adapters are pure renderers over the portable JSON package. They do not query Neo4j independently.

Codex handoffs point to repository `AGENTS.md`; Claude Code handoffs remain portable Markdown. Both list canonical files and relevant validation commands.

### Context budgets

`engineering-graph/config.yaml` defines defaults:

```yaml
context:
  max_depth: 3
  max_nodes: 80
  max_bytes: 65536
```

Override when needed:

```bash
graph-engineering context-batch \
  --task SPEC-010-AGENT-CONTEXT-GRAPH:T044 \
  --depth 2 \
  --max-nodes 40 \
  --max-bytes 32768
```

Budgets are hard bounds. If optional evidence does not fit, lower-priority evidence is deterministically truncated and the package reports `truncatedNodes`, `renderedBytes` and `truncated`. If the mandatory Task/Spec metadata cannot fit, generation fails rather than emitting an invalid package.

### Regenerate after repository movement

```bash
rm -rf context-packages/*
graph-engineering sync
graph-engineering validate
graph-engineering context-batch --spec SPEC-010-AGENT-CONTEXT-GRAPH
```

Do not keep a stale generated package alive by manually changing its revision field.

## Single context inspection

For human inspection without writing the full package directory:

```bash
graph-engineering context SPEC-010-AGENT-CONTEXT-GRAPH:T044 \
  --format markdown
```

Open the canonical source paths named in that output before editing.

## Impact analysis

```bash
graph-engineering impact ADR-0018 --depth 3
graph-engineering impact SPEC-010-AGENT-CONTEXT-GRAPH:T044 --depth 3 --json
```

Depth is bounded; current CLI caps impact traversal at 5 hops and context packages use configured depth/node/byte budgets.

## Querying directly

Neo4j Browser is available at `http://127.0.0.1:7474` in local Compose. Prefer the checked-in Cypher files under `engineering-graph/queries/` when a reusable query exists.

Direct graph experimentation is fine for analysis. Do not manually edit nodes/edges and then treat those edits as project knowledge; the next sync may intentionally overwrite/prune them.

## Rebuild

```bash
graph-engineering reset --yes
graph-engineering schema
graph-engineering sync
graph-engineering validate
```

Destroy local Neo4j state if desired:

```bash
docker compose down -v
```

The repository remains complete without the database.

## Validation severities

`engineering-graph/config.yaml` controls rule severity:

```yaml
validation:
  rules:
    enforced-spec-no-task: error
    task-dependency-cycle: error
    completed-task-no-code: warning
```

Use `error` only for invariants the repository can deterministically prove. Do not promote a heuristic warning to a blocking error until authoring conventions make the required evidence reliable.

## Graph-friendly Spec Kit authoring

Prefer stable explicit references:

```markdown
- [ ] T044 Extend Engineering Graph workflow `.github/workflows/engineering-graph.yml`
```

Use ADR references such as `ADR-0018` when a spec/plan is constrained by a durable decision. Optional frontmatter may provide machine-friendly graph metadata, but the Markdown body must remain sufficient for humans without Neo4j.

## Pull requests

GitHub Actions can pass `$GITHUB_EVENT_PATH` into `graph-engineering sync --github-event ...`. The extractor can then project the current PR plus changed-path/task/spec evidence without using Neo4j as a PR authority.

The recommended PR validation order is:

```text
application CI (when applicable)
Spec Kit integration status
Engineering Graph offline tests
Engineering Graph ephemeral Neo4j sync
Engineering Graph validation/query smoke
Agent Context package generation
strict freshness validation
Codex/Claude adapter smoke
semantic package reproducibility
```

## Troubleshooting

### Neo4j not ready

```bash
graph-engineering doctor --wait 90
```

Check:

```bash
docker compose ps
docker compose logs neo4j
```

### Context package is stale immediately after generation

Run:

```bash
git rev-parse HEAD
graph-engineering sync
graph-engineering context-batch --task <TASK-ID>
graph-engineering context-validate <context.json> --strict
```

If generation reports a graph `sourceRevision` different from HEAD, the graph projection is stale. Re-sync it. Do not edit the generated package to silence freshness validation.

### Wrong repository id

The tool prefers `GRAPH_REPOSITORY_ID`, then normalized `remote.origin.url`, then the checkout directory name. CI sets `GRAPH_REPOSITORY_ID=az1nn/cpxlabs-admin` for deterministic identity.

### Validation warning for historical specs

Specifications 001–004 were retrofitted after implementation. Selected missing-evidence findings are intentionally downgraded by `historical_spec_prefixes`; do not fabricate old edges to silence warnings.

### Graph differs after two syncs

`sourceRevision`/`syncRunId` are provenance and may change as metadata. The logical canonical nodes/edges and counts for identical repository content must remain stable. Investigate nondeterministic extraction if logical graph shape changes.
