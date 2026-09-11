# Engineering Graph Development Workflow

## Goal

Use Neo4j as a local/CI engineering projection over the repository to answer traceability, impact, drift, agent-context and parallelization questions without moving canonical project knowledge out of Git.

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
graph-engineering ready --spec SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE
graph-engineering conflicts --spec SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE
graph-engineering waves --spec SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE
```

Before assigning one task to an agent/worktree:

```bash
graph-engineering context SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE:T061 \
  --format markdown \
  --output context-packages/T061.md
```

Open the canonical source paths named in that package before editing.

## Impact analysis

```bash
graph-engineering impact ADR-0017 --depth 3
graph-engineering impact SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE:T061 --depth 3 --json
```

Depth is bounded; current CLI caps impact traversal at 5 hops and context packages use the configured node budget.

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
- [ ] T042 [P] Add validator tests `engineering-graph/tests/test_validator.py` (`depends: T043`)
```

Use ADR references such as `ADR-0017` when a spec/plan is constrained by a durable decision. Optional frontmatter may provide machine-friendly graph metadata, but the Markdown body must remain sufficient for humans without Neo4j.

## Pull requests

GitHub Actions can pass `$GITHUB_EVENT_PATH` into `graph-engineering sync --github-event ...`. The extractor can then project the current PR plus changed-path/task/spec evidence without using Neo4j as a PR authority.

The recommended PR validation order is:

```text
application CI (when applicable)
Spec Kit integration status (when applicable)
Engineering Graph unit tests
Engineering Graph ephemeral Neo4j sync
Engineering Graph validation/query smoke
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

### Wrong repository id

The tool prefers `GRAPH_REPOSITORY_ID`, then normalized `remote.origin.url`, then the checkout directory name. CI sets `GRAPH_REPOSITORY_ID=az1nn/cpxlabs-admin` for deterministic identity.

### Validation warning for historical specs

Specifications 001–004 were retrofitted after implementation. Selected missing-evidence findings are intentionally downgraded by `historical_spec_prefixes`; do not fabricate old edges to silence warnings.

### Graph differs after two syncs

`sourceRevision`/`syncRunId` are provenance and may change as metadata. The logical canonical nodes/edges and counts for identical repository content must remain stable. Investigate nondeterministic extraction if logical graph shape changes.
