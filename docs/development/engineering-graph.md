# Engineering Graph Development Workflow

## Goal

Use Neo4j as a local/CI engineering projection over the repository to answer traceability, impact, drift, agent-context, execution and semantic-discovery questions without moving canonical project knowledge out of Git.

V2 Agent Context Graph adds revision-aware disposable ContextPackages. V3 Execution Graph composes those packages with the task planner to produce conflict-safe waves and isolated Git worktrees. V4 GraphRAG adds a revision/provider-bound semantic sidecar index that discovers repository content and then expands only through existing deterministic Neo4j relationships. V5 Agent Runner consumes an already-active V3 allocation to start and observe one local child-process lifecycle inside the allocated worktree.

Generated packages, manifests, leases, semantic indexes, retrieval results, runner metadata and runner logs are operational artifacts, not canonical documentation.

## Prerequisites

- Python 3.13+
- Docker / Docker Compose
- Git checkout with repository history
- optional learned embedding HTTP endpoint for production-quality semantic retrieval
- optional locally installed/authenticated coding-agent CLI for real V5 runs

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

## Daily graph workflow

After pulling/changing specs, ADRs, tasks, code or tests:

```bash
cd engineering-graph
graph-engineering sync
graph-engineering validate
```

Before starting material task work:

```bash
graph-engineering ready --spec <SPEC-ID>
graph-engineering conflicts --spec <SPEC-ID>
graph-engineering waves --spec <SPEC-ID>
```

## V2 Agent Context Graph workflow

Generate one task package:

```bash
graph-engineering context-batch --task <TASK-ID>
```

Generate all READY packages:

```bash
graph-engineering context-batch --spec <SPEC-ID> --json
```

Each task directory contains:

```text
context.json
context.md
codex.md
claude.md
```

`context.json` is the portable contract. The other files are renderings from the same package.

Validate freshness immediately before implementation:

```bash
graph-engineering context-validate <context.json> --strict
```

The package revision comes from the projected graph. Strict validation compares it with current Git HEAD and fails for stale/unknown state.

Agent renderers:

```bash
graph-engineering context-adapt context.json --agent codex
graph-engineering context-adapt context.json --agent claude
```

Default budgets:

```yaml
context:
  max_depth: 3
  max_nodes: 80
  max_bytes: 65536
```

Regenerate after repository movement rather than editing freshness metadata manually.

## V3 Execution Graph workflow

Build a revision-bound manifest:

```bash
graph-engineering execution-plan \
  --spec <SPEC-ID> \
  --agent codex \
  --output .execution/manifests/current.json
```

Dry-run:

```bash
graph-engineering execution-prepare \
  .execution/manifests/current.json \
  --wave 1 \
  --dry-run \
  --json
```

Prepare one wave/task:

```bash
graph-engineering execution-prepare \
  .execution/manifests/current.json \
  --wave 1
```

Preparation sequence:

```text
manifest repository/revision validation
        ↓
wave/task conflict validation
        ↓
active lease collision check
        ↓
V2 ContextPackage build + strict freshness
        ↓
context/handoff write
        ↓
Git worktree create/resume
        ↓
active lease acquisition
```

Inspect/release:

```bash
graph-engineering execution-status --json
graph-engineering execution-release <TASK-ID>
graph-engineering execution-release <TASK-ID> --remove-worktree
```

Dirty worktree removal fails unless explicit `--force` is supplied. V3 never commits, pushes, creates/merges PRs or changes canonical Task status automatically.

Default local state:

```text
engineering-graph/.execution/
├── leases.json
├── manifests/
├── contexts/
└── worktrees/
```

Generated metadata is disposable; dirty worktree contents are user data.

## V4 GraphRAG workflow

### 1. Synchronize deterministic graph evidence

GraphRAG graph expansion depends on the current deterministic projection:

```bash
graph-engineering sync
graph-engineering validate
```

### 2. Build the semantic sidecar index

For deterministic offline/CI mechanics:

```bash
graph-engineering graphrag-build \
  --provider hashing \
  --output .graphrag/index.json
```

The hashing provider is a lexical feature-hashing retrieval surrogate. Use it for deterministic validation, not as a claim of learned semantic quality.

For a learned embedding endpoint:

```bash
export GRAPH_RAG_EMBEDDING_URL='https://embedding-service.example/v1/embeddings'
export GRAPH_RAG_EMBEDDING_MODEL='your-model'
export GRAPH_RAG_EMBEDDING_API_KEY='...'
export GRAPH_RAG_DIMENSIONS='1536'

graph-engineering graphrag-build --provider http
```

The HTTP contract sends:

```json
{"model":"your-model","input":["chunk one","chunk two"]}
```

and expects ordered embedding records under `data`. Provider credentials remain process-local and are never stored in the index.

### 3. Validate freshness

```bash
graph-engineering graphrag-status --provider <provider>
graph-engineering graphrag-validate .graphrag/index.json --provider <provider> --strict
```

Strict mode fails closed on:

- repository mismatch;
- Git revision mismatch;
- provider/model mismatch;
- dimensions mismatch;
- chunk/corpus configuration mismatch.

Rebuild after any mismatch. `--allow-stale` on query is only for deliberate exploratory retrieval across Git revision drift; it does not make provider/model/config incompatibility valid.

### 4. Query semantic seeds and deterministic graph evidence

```bash
graph-engineering graphrag-query \
  "why does GraphRAG remain retrieval assistance?" \
  --index .graphrag/index.json \
  --provider hashing \
  --mode architecture \
  --top-k 8 \
  --min-score 0.0 \
  --depth 2 \
  --max-nodes 80 \
  --json
```

Interpret the output in three separate layers:

```text
semanticHits   = vector-ranked tracked-file chunks
anchors        = existing graph nodes resolved by sourcePath/path
graphEvidence  = traversal over existing deterministic relationships
```

Do not treat semantic similarity as a graph relationship. A high score only means the retriever found a similar chunk.

### 5. Architecture discovery

Use `--mode architecture` for ADR/spec/requirement discovery. Architecture paths are prioritized while the original semantic score remains visible.

This mode does not write or infer `CONSTRAINED_BY`, `DEPENDS_ON`, `RELATED_TO`, etc. The only relationships shown as graph evidence are ones already projected from explicit Git-backed evidence.

### 6. Corpus safety

Only `git ls-files` paths are eligible. Then extension and excluded-prefix filters from `config.yaml` are applied.

Generated/vendor/cache prefixes are excluded, including `.graphrag`, `.execution`, ContextPackages, node modules, dist, coverage and browser-test outputs. Therefore an untracked local secret or note cannot enter the corpus merely because it exists on disk.

### 7. Index lifecycle

Default state:

```text
engineering-graph/.graphrag/
└── index.json
```

The index contains a versioned manifest plus deterministic chunks/vectors. It records repository revision, provider/model, dimensions, chunk configuration and semantic SHA-256.

Writes use temporary-file + fsync + atomic replace. Deleting `.graphrag/` loses no canonical knowledge.

## V5 Agent Runner workflow

V5 starts only after V3 has prepared and leased a Task. It does not allocate work itself.

### 1. Confirm the allocation

```bash
graph-engineering execution-status --json
```

The task must have an active lease and its allocation must still match current Git HEAD. If the allocation is stale, re-sync/re-plan/re-prepare; do not bypass V5 revision checks.

### 2. Start the process

Put all V5 options before `--command`. Everything after `--command` becomes literal child argv:

```bash
graph-engineering runner-start <TASK-ID> \
  --stdin-handoff \
  --json \
  --command <agent-executable> <agent-arg-1> <agent-arg-2>
```

The child is launched with:

```text
shell=False
cwd=<allocation.worktreePath>
new process session/group
```

Supported token-local placeholders:

```text
{task_id}
{spec_id}
{worktree}
{handoff}
{context}
{branch}
{source_revision}
```

No shell interpolation, command substitution, globbing or redirection is performed.

When `--stdin-handoff` is used, the generated V2/V3 handoff bytes are sent directly to child stdin.

### 3. Observe status

```bash
graph-engineering runner-status --task <TASK-ID>
graph-engineering runner-status --json
```

States are process observations:

```text
running
succeeded
failed
stopped
orphaned
```

`status=succeeded` / `exitCode=0` does **not** mean the Spec Kit Task is complete. Review implementation/tests and update canonical task evidence separately.

### 4. Inspect bounded logs

```bash
graph-engineering runner-logs <TASK-ID> --stream stdout
graph-engineering runner-logs <TASK-ID> --stream stderr
graph-engineering runner-logs <TASK-ID> --stream both --max-bytes 65536 --json
```

Logs are derived local state. `runner-logs` only reads log files; it does not execute repository code.

### 5. Stop safely

```bash
graph-engineering runner-stop <TASK-ID>
```

Normal stop validates process identity and sends graceful SIGTERM to the recorded process group. Force escalation is explicit:

```bash
graph-engineering runner-stop <TASK-ID> --timeout 5 --force
```

On Linux the stored process fingerprint includes `/proc/<pid>/stat` start identity. If the PID now belongs to a different process, V5 refuses to signal it.

### 6. Lease remains independent

Runner termination never releases the V3 lease automatically:

```bash
graph-engineering execution-release <TASK-ID>
```

This separation is deliberate: process completion is not equivalent to task/review completion.

### 7. Runner state

```text
engineering-graph/.execution/runs/
├── registry.json
└── <run-id>/
    ├── run.json
    ├── stdout.log
    ├── stderr.log
    └── result.json
```

Runner state is versioned, local, Git-ignored and disposable. Environment values are never serialized. Do not place secrets in argv because argv is intentionally recorded for reproducibility.

See `docs/architecture/AGENT_RUNNER.md` and ADR-0021.

## Single context inspection

For human inspection without writing a full package directory:

```bash
graph-engineering context <TASK-ID> --format markdown
```

Open canonical source paths named in that output before editing.

## Impact analysis

```bash
graph-engineering impact ADR-0021 --depth 3
graph-engineering impact SPEC-013-AGENT-RUNNER:T031 --depth 3 --json
```

Depth is bounded. Context, execution and GraphRAG surfaces all expose explicit budgets rather than permitting hidden unbounded traversal.

## Querying Neo4j directly

Neo4j Browser is available at `http://127.0.0.1:7474` in local Compose. Prefer checked-in Cypher files under `engineering-graph/queries/` when a reusable query exists.

Direct graph experimentation is fine for analysis. Do not manually edit nodes/edges and then treat those edits as project knowledge; sync may overwrite/prune them.

GraphRAG itself performs read-only graph queries. Agent Runner state is not written to Neo4j at all.

## Rebuild

Rebuild deterministic graph state:

```bash
graph-engineering reset --yes
graph-engineering schema
graph-engineering sync
graph-engineering validate
```

Rebuild semantic state:

```bash
rm -rf .graphrag
graph-engineering graphrag-build --provider <provider>
graph-engineering graphrag-validate --provider <provider> --strict
```

Discard only runner observation state:

```bash
rm -rf .execution/runs
```

This does not release leases or remove worktrees. Inspect V3 state separately before cleanup.

Destroy local Neo4j if desired:

```bash
docker compose down -v
```

The Git repository remains complete without Neo4j, ContextPackages, Execution Graph metadata, GraphRAG indexes or Agent Runner records/logs.

## Validation severities

`engineering-graph/config.yaml` controls deterministic graph rule severity. Use `error` only for invariants the repository can deterministically prove. Semantic similarity and process lifecycle observations are not validator rules or canonical edge sources.

## Graph-friendly Spec Kit authoring

Prefer stable explicit references and repository paths. Use ADR references such as `ADR-0021` when a spec/plan is constrained by a durable decision. Markdown remains sufficient for humans without Neo4j/GraphRAG/Runner state.

## Pull requests and validation order

GitHub Actions can pass `$GITHUB_EVENT_PATH` into `graph-engineering sync --github-event ...`. PR metadata remains evidence only.

Recommended validation order:

```text
application CI (when applicable)
Spec Kit integration status
Engineering Graph offline unit/integration tests
Engineering Graph ephemeral Neo4j sync/idempotency
Graph validation/query smokes
V2 ContextPackage freshness/adapters/reproducibility
V3 ExecutionManifest/wave/worktree/lease validation
V4 GraphRAG build/freshness/reproducibility
V4 controlled semantic retrieval + graph anchor/expansion
V4 before/after graph stats equality
V5 harmless local runner lifecycle tests
V5 worktree cwd + stdin handoff + logs + terminal status assertions
V5 duplicate-run/stop/PID-safety + lease-preservation assertions
```

V5 CI uses local Python fixture processes only. It never invokes a networked coding agent.

## Troubleshooting

### Neo4j not ready

```bash
graph-engineering doctor --wait 90
```

Check `docker compose ps` and `docker compose logs neo4j`.

### Context package is stale

```bash
git rev-parse HEAD
graph-engineering sync
graph-engineering context-batch --task <TASK-ID>
graph-engineering context-validate <context.json> --strict
```

Do not edit generated revision metadata.

### Execution manifest/allocation is stale

```bash
graph-engineering sync
graph-engineering validate
graph-engineering execution-plan --spec <SPEC-ID> --agent codex --output .execution/manifest.json
```

Re-prepare the task after repository movement rather than bypassing revision checks.

### GraphRAG index is stale/incompatible

```bash
graph-engineering graphrag-status --provider <provider> --json
graph-engineering graphrag-validate --provider <provider> --strict --json
```

If revision/provider/model/dimensions/config differ, rebuild. Do not edit the index manifest/hash manually.

### Learned embedding endpoint unavailable

Canonical files and deterministic graph remain usable. Use `hashing` only for offline retrieval mechanics/CI if appropriate; do not represent it as equivalent learned semantic quality.

### GraphRAG query has hits but no anchors

The chunk can be semantically useful even when its path is not represented as a deterministic graph node. Inspect the hit path directly. Graph expansion only begins from paths represented by existing `sourcePath`/`path` graph evidence.

### Runner refuses to start

Check:

```bash
graph-engineering execution-status --json
git rev-parse HEAD
graph-engineering runner-status --task <TASK-ID> --json
```

Common causes are no active V3 lease, stale allocation revision, missing/unregistered worktree, missing handoff or an existing non-terminal run.

### Runner refuses to stop because identity changed

Do not bypass the check. Inspect the recorded PID/fingerprint and current OS process manually. PID reuse is precisely the condition the fail-closed behavior is protecting against.

### Runner exited but lease is still active

Expected. V5 never infers Task completion and never releases a lease automatically. Review the work, then explicitly release with `execution-release` when appropriate.

### Worktree release refuses cleanup

Run `graph-engineering execution-status --json` and inspect the worktree. Normal cleanup protects dirty/untracked files. Use `--force` only for intentional data discard.

### Wrong repository ID

The tool prefers `GRAPH_REPOSITORY_ID`, then normalized `remote.origin.url`, then checkout directory name. CI pins `az1nn/cpxlabs-admin`.

### Historical validation warnings

Specifications 001–004 were retrofitted after implementation. Selected evidence findings are downgraded by `historical_spec_prefixes`; do not fabricate historical edges to silence them.

### Logical graph differs after identical sync/query

`sourceRevision`/`syncRunId` are provenance. Canonical graph shape/counts must remain stable for identical repository content. GraphRAG query must leave logical stats unchanged because it is read-only; Agent Runner must not modify Neo4j at all.
