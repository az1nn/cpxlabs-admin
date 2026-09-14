# Engineering Graph

Repository-local Neo4j control plane for Spec-Driven and Agent-Driven engineering, with bounded context, execution orchestration, GraphRAG retrieval and local agent process lifecycle.

## Authority boundary

Git-backed artifacts are canonical. Neo4j is a rebuildable deterministic projection used for traceability, impact analysis, drift checks, bounded agent context and execution planning. Generated ContextPackages, execution manifests, leases, GraphRAG indexes/results and Agent Runner process metadata/logs are disposable derived artifacts.

No application runtime depends on this directory, Neo4j, an embedding provider, the Agent Runner or generated graph/retrieval/process state.

## Local setup

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

Neo4j Browser is exposed on `http://127.0.0.1:7474`; Bolt uses `bolt://127.0.0.1:7687`.

## Core commands

```bash
graph-engineering doctor --wait 60
graph-engineering schema
graph-engineering sync --json
graph-engineering validate --json
graph-engineering stats --json
graph-engineering impact ADR-0021 --depth 3 --json
graph-engineering ready --spec SPEC-013-AGENT-RUNNER --json
graph-engineering conflicts --spec SPEC-013-AGENT-RUNNER --json
graph-engineering drift --json
graph-engineering context SPEC-013-AGENT-RUNNER:T031 --format markdown
graph-engineering waves --spec SPEC-013-AGENT-RUNNER --json
graph-engineering execution-plan --spec SPEC-013-AGENT-RUNNER --agent codex --output .execution/manifest.json
graph-engineering graphrag-build --provider hashing
graph-engineering graphrag-query "Agent Runner authority" --provider hashing --mode architecture
graph-engineering runner-status --json
graph-engineering reset --yes
```

## V1 deterministic graph model

Seven node labels:

- `Requirement`
- `Spec`
- `ADR`
- `Task`
- `CodeArtifact`
- `Test`
- `PullRequest`

Eight relationship names:

- `REALIZED_BY`
- `CONSTRAINED_BY`
- `DECOMPOSED_INTO`
- `DEPENDS_ON`
- `IMPLEMENTED_BY`
- `VALIDATED_BY`
- `IMPLEMENTS`
- `CHANGES`

Node identity is `(repository, canonicalId)`. The sync engine consumes explicit repository evidence only. Task phase order is not treated as dependency evidence; use explicit `depends: T001,T002` when dependency edges are required.

GraphRAG and Agent Runner do not add labels or relationship types to this vocabulary.

## V2 Agent Context Graph

Generate one task package:

```bash
graph-engineering context-batch --task SPEC-013-AGENT-RUNNER:T031
```

Generate all READY packages for a spec:

```bash
graph-engineering context-batch --spec SPEC-013-AGENT-RUNNER --json
```

Each selected task receives:

```text
context.json   portable machine contract
context.md     human-readable context map
codex.md       Codex-oriented handoff
claude.md      Claude Code-oriented handoff
```

Validate freshness immediately before implementation:

```bash
graph-engineering context-validate context-packages/.../context.json --strict
```

Adapters are pure renderers:

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

Generated packages are ignored by Git and must be regenerated when repository/graph evidence changes.

## V3 Execution Graph

Build a revision-bound execution manifest:

```bash
graph-engineering execution-plan \
  --spec SPEC-013-AGENT-RUNNER \
  --agent codex \
  --output .execution/manifests/spec-013.json
```

Dry-run or prepare one conflict-safe wave/task:

```bash
graph-engineering execution-prepare .execution/manifests/spec-013.json --wave 1 --dry-run
graph-engineering execution-prepare .execution/manifests/spec-013.json --task <TASK-ID>
```

Inspect/release allocations:

```bash
graph-engineering execution-status
graph-engineering execution-release <TASK-ID>
graph-engineering execution-release <TASK-ID> --remove-worktree
```

V3 creates/resumes deterministic worktrees and local derived leases only after revision, wave and V2 ContextPackage freshness checks. Dirty worktree contents are user data and are not removed unless explicit destructive `--force` is supplied.

V3 never commits, pushes, creates/merges PRs or changes canonical Task status automatically.

## V4 GraphRAG

V4 adds semantic repository discovery followed by read-only deterministic graph expansion.

```text
Git-tracked repository content
        ↓
deterministic chunks
        ↓
derived vector index
        ↓
semantic query hits
        ↓
sourcePath/path graph anchors
        ↓
existing Neo4j relationships only
```

### Build an offline deterministic index

```bash
graph-engineering graphrag-build \
  --provider hashing \
  --output .graphrag/index.json
```

`hashing` is a deterministic zero-network retrieval surrogate for CI/offline mechanics. It is not equivalent to a learned semantic embedding model.

### Validate/index status

```bash
graph-engineering graphrag-status --provider hashing
graph-engineering graphrag-validate .graphrag/index.json --provider hashing --strict
```

Strict validation checks repository identity, Git revision, provider/model/dimensions and corpus/chunk configuration.

### Query and expand the graph

```bash
graph-engineering graphrag-query \
  "why does Agent Runner remain outside canonical task authority?" \
  --index .graphrag/index.json \
  --provider hashing \
  --mode architecture \
  --top-k 8 \
  --depth 2 \
  --max-nodes 80
```

Result evidence is deliberately separated into:

- `semanticHits`: vector-ranked source chunks;
- `anchors`: existing deterministic graph nodes resolved from hit paths;
- `graphEvidence`: bounded traversal over relationships already present in Neo4j.

Semantic score and graph distance are not collapsed into an opaque authority score.

### Learned embeddings through HTTP

```bash
export GRAPH_RAG_EMBEDDING_URL='https://embedding-service.example/v1/embeddings'
export GRAPH_RAG_EMBEDDING_MODEL='your-model'
export GRAPH_RAG_EMBEDDING_API_KEY='...'
export GRAPH_RAG_DIMENSIONS='1536'

graph-engineering graphrag-build --provider http
graph-engineering graphrag-validate --provider http --strict
graph-engineering graphrag-query "runner authority" --provider http --mode architecture
```

The HTTP boundary avoids a mandatory provider SDK. Credentials are never stored in the semantic index.

Only `git ls-files` paths can enter the corpus. Generated `.graphrag/` state is ignored by Git and disposable. GraphRAG never creates semantic relationship truth in Neo4j.

See `docs/architecture/GRAPHRAG.md` and ADR-0020.

## V5 Agent Runner

V5 consumes an already-active V3 allocation and manages one local child-process lifecycle. It does not choose work, create worktrees, change leases or publish Git changes.

### Start

Put runner-owned options before `--command`; every token after `--command` belongs literally to the child argv:

```bash
graph-engineering runner-start <TASK-ID> \
  --stdin-handoff \
  --json \
  --command <agent-executable> <agent-argv...>
```

The runner requires:

- active V3 lease;
- current repository/revision identity;
- exact registered allocation worktree/branch;
- generated handoff file;
- no existing non-terminal run for the task.

The target is launched with `shell=False` and cwd fixed to the allocated worktree. Handoff bytes may be supplied directly to stdin.

### Inspect status/logs

```bash
graph-engineering runner-status --task <TASK-ID>
graph-engineering runner-status --json
graph-engineering runner-logs <TASK-ID> --stream stdout
graph-engineering runner-logs <TASK-ID> --stream both --json
```

Versioned local state lives under:

```text
engineering-graph/.execution/runs/
├── registry.json
└── <run-id>/
    ├── run.json
    ├── stdout.log
    ├── stderr.log
    └── result.json
```

The whole subtree is derived/disposable and already covered by the ignored `.execution/` root.

### Stop

```bash
graph-engineering runner-stop <TASK-ID>
graph-engineering runner-stop <TASK-ID> --force
```

On Linux the runner records a `/proc` process-start fingerprint in addition to PID and refuses to signal a PID whose identity no longer matches. Child processes run in a dedicated process group so lifecycle signals cover the spawned tree.

A terminal runner state does **not** release the V3 lease:

```bash
graph-engineering execution-release <TASK-ID>
```

Lease release remains explicit because process termination is not Task completion.

### Agent Runner authority

`running`, `succeeded`, `failed`, `stopped` and `orphaned` are process observations only. Even `succeeded`/exit code `0` does not mark a Spec Kit Task complete or authorize commit/push/PR/merge.

Environment variables can be inherited by an installed local agent CLI but are never serialized into `AgentRun`; do not put secrets in argv because argv is intentionally recorded.

See `docs/architecture/AGENT_RUNNER.md` and ADR-0021.

## Drift versus validation

`drift` exposes raw deterministic invariant evidence. `validate` applies configured severity policy (`error`, `warning`, `off`) plus structural checks. Use `drift` for inspection and `validate` as the CI decision surface.

## CI

`.github/workflows/engineering-graph.yml` runs:

1. Python unit/integration tests, including real temporary Git worktrees, GraphRAG tests and harmless local Agent Runner lifecycle fixtures;
2. application-runtime dependency isolation guard;
3. ephemeral Neo4j schema/sync/idempotency/validation;
4. V1 fundamental query smokes;
5. V2 ContextPackage freshness/adapters/reproducibility/disposal;
6. V3 ExecutionManifest/wave/completed-spec smokes;
7. V4 GraphRAG build/freshness/reproducibility/retrieval/graph-expansion smokes;
8. V5 worktree-cwd, stdin-handoff, logs, exit/stop, duplicate-run and lease-preservation assertions through the offline integration suite.

CI never invokes a real Codex/Claude/networked agent for V5. Existing application CI and Spec Kit CI remain independent and authoritative for their domains.

## Rebuild / recovery

Derived graph/context/execution/retrieval/runner metadata is disposable:

```bash
rm -rf context-packages/* .graphrag .execution/contexts .execution/manifests .execution/runs
graph-engineering reset --yes
graph-engineering schema
graph-engineering sync
graph-engineering validate
graph-engineering graphrag-build --provider hashing
```

Do not blindly delete `.execution/worktrees/`: inspect `execution-status`/Git worktree state first because those directories may contain uncommitted user work. Deleting `.execution/runs/` does not release leases or remove worktrees.

No canonical knowledge is lost by deleting the Neo4j projection, ContextPackages, clean execution metadata, GraphRAG index or Agent Runner logs/records.

## Deliberately deferred

V5 still does not include semantic similarity as canonical graph edges, LLM answer synthesis, distributed multi-host scheduling, wave-level agent supervision/retries, automatic validation execution, automatic Task mutation, automatic lease release, remote execution, or autonomous commit/push/PR creation/merge. Those require separate specs/ADRs/PRs.
