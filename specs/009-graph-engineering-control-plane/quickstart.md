# Quickstart: Graph Engineering Control Plane

## Principle

Neo4j is disposable engineering infrastructure. Git/specs/ADRs/code/tests remain canonical.

## Local bootstrap

```bash
cd engineering-graph
cp .env.example .env
docker compose up -d
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m engineering_graph doctor --wait 60
python -m engineering_graph schema
python -m engineering_graph sync --repo-root ..
python -m engineering_graph validate
python -m engineering_graph stats
```

Neo4j Browser is exposed on `http://localhost:7474`; Bolt is `bolt://localhost:7687`.

## Fundamental commands

```bash
python -m engineering_graph impact ADR-0015
python -m engineering_graph ready --spec SPEC-007-OPPORTUNITY-WORKFLOW
python -m engineering_graph conflicts --spec SPEC-007-OPPORTUNITY-WORKFLOW
python -m engineering_graph context SPEC-007-OPPORTUNITY-WORKFLOW:T060 --format markdown
python -m engineering_graph waves --spec SPEC-007-OPPORTUNITY-WORKFLOW
python -m engineering_graph validate --json
```

After package installation, `graph-engineering` is an equivalent console command.

## Rebuild from zero

```bash
cd engineering-graph
docker compose down -v
docker compose up -d
source .venv/bin/activate
python -m engineering_graph doctor --wait 60
python -m engineering_graph schema
python -m engineering_graph sync --repo-root ..
python -m engineering_graph validate
```

Application web/API/PostgreSQL services do not depend on this graph and continue to operate while Neo4j is stopped.

## Spec Kit lifecycle

```text
specify/clarify
  → graph sync

plan
  → graph sync
  → graph impact <spec-or-adr>

tasks
  → graph sync
  → graph ready
  → graph conflicts
  → graph waves

implement task
  → graph context <SPEC:TASK>
  → agent reads only required canonical files

PR
  → graph sync
  → graph validate
  → graph drift/impact checks
```

## Explicit metadata

Existing specs work through deterministic conventions. New/complex specs may add optional frontmatter:

```yaml
---
graph:
  enforced: true
  depends_on:
    - SPEC-005-AUTHENTICATION-AUTHORIZATION
  constrained_by:
    - ADR-0015
---
```

Task text may declare explicit dependency evidence:

```markdown
- [ ] T042 Implement cache namespace (`depends: T040,T041`) `apps/web/src/example.ts`
```

Do not infer a dependency merely because tasks appear in different phases.

## Agent context package

```bash
python -m engineering_graph context \
  SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE:T048 \
  --format json \
  --output .graph-context/T048.json
```

Context outputs are generated artifacts and are ignored by Git.

## Failure semantics

- Neo4j unavailable locally: use canonical files directly; no product runtime impact.
- Graph extraction/structural error in CI: graph workflow fails.
- Historical traceability warning: reported but does not automatically fail unless configuration promotes it to `error`.
- Task dependency cycle: `waves` fails; fix canonical dependency metadata rather than forcing a schedule.
