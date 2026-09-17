# Engineering Graph

Repository-local control plane for Spec-Driven and Agent-Driven engineering. Git-backed code, Spec Kit artifacts, ADRs, tests and Git history remain canonical; Neo4j and all generated execution/retrieval/process/publication state are derived and disposable.

No application runtime depends on this directory, Neo4j, GraphRAG, agent process tooling, validation, publication, or post-publication state.

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

## Control-plane layers

```text
Git / Spec Kit / ADR / code / tests / Git history        canonical authority
                         |
                         v
V1 deterministic Engineering Graph                      derived projection
                         |
                         v
V2 Agent Context Graph                                  bounded ContextPackage/handoff
                         |
                         v
V3 Execution Graph                                      waves/worktrees/leases
                         |
                         v
V5 Agent Runner                                         local process lifecycle
                         |
                         v
V6 Agent Supervisor                                     bounded scheduling/retries
                         |
                         v
V7 Agent Validator                                      frozen-command validation
                         |
                         v
V8 Git Publisher                                        commit/push/open PR
                         |
                   human review / merge
                         |
                         v
V9 Post-Publication Lifecycle                           reconcile/release/clean worktree

V4 GraphRAG is an orthogonal read-only semantic-discovery sidecar over tracked repository content and existing deterministic graph evidence.
```

Each layer may consume evidence from the preceding layer but does not silently acquire authority owned by the next layer or by humans.

## Core graph commands

```bash
graph-engineering doctor --wait 60
graph-engineering schema
graph-engineering sync --json
graph-engineering validate --json
graph-engineering stats --json
graph-engineering impact <CANONICAL-ID> --depth 3 --json
graph-engineering ready --spec <SPEC-ID> --json
graph-engineering conflicts --spec <SPEC-ID> --json
graph-engineering drift --json
```

V1 uses deterministic repository evidence only. Task phase ordering is not a dependency edge; use explicit `depends:` metadata when dependency evidence is required.

## V2 Agent Context Graph

```bash
graph-engineering context-batch --task <TASK-ID>
graph-engineering context-batch --spec <SPEC-ID> --json
graph-engineering context-validate context-packages/.../context.json --strict
graph-engineering context-adapt context.json --agent codex
graph-engineering context-adapt context.json --agent claude
```

Generated ContextPackages/handoffs are revision-bound derived context. Strictly validate freshness immediately before implementation and regenerate after Git/graph changes.

## V3 Execution Graph

```bash
graph-engineering execution-plan \
  --spec <SPEC-ID> \
  --agent codex \
  --output .execution/manifests/<spec>.json

graph-engineering execution-prepare .execution/manifests/<spec>.json --wave 1 --dry-run
graph-engineering execution-prepare .execution/manifests/<spec>.json --task <TASK-ID>
graph-engineering execution-status
graph-engineering execution-release <TASK-ID>
graph-engineering execution-release <TASK-ID> --remove-worktree
```

V3 owns derived allocation/worktree/lease state. Dirty worktree contents are user work and must never be removed implicitly.

## V4 GraphRAG

```bash
graph-engineering graphrag-build --provider hashing
graph-engineering graphrag-status --provider hashing
graph-engineering graphrag-validate .graphrag/index.json --provider hashing --strict
graph-engineering graphrag-query \
  "<query>" \
  --provider hashing \
  --mode architecture \
  --top-k 8 \
  --depth 2 \
  --max-nodes 80
```

GraphRAG indexes only eligible `git ls-files` content. Semantic similarity is discovery evidence, never a canonical relationship. Graph expansion traverses relationships already present in Neo4j.

## V5 Agent Runner

```bash
graph-engineering runner-start <TASK-ID> \
  --stdin-handoff \
  --json \
  --command <agent-executable> <agent-argv...>

graph-engineering runner-status --task <TASK-ID> --json
graph-engineering runner-logs <TASK-ID> --stream both --json
graph-engineering runner-stop <TASK-ID>
graph-engineering runner-stop <TASK-ID> --force
```

V5 runs one process only for an active V3 allocation, with `shell=False` and cwd fixed to the allocated worktree. Process success is not Task completion and never releases the lease automatically.

## V6 Agent Supervisor

V6 supervises bounded waves/retries over V5 without creating new Task/Git authority.

```bash
graph-engineering supervisor-start ...
graph-engineering supervisor-tick ...
graph-engineering supervisor-status ...
graph-engineering supervisor-stop ...
```

Supervisor ownership/retry evidence remains derived. It may not reinterpret failed/stopped runs as canonical Task state.

## V7 Agent Validator

```bash
graph-engineering validation-run <TASK-ID> --json
graph-engineering validation-status --task <TASK-ID> --json
```

V7 runs only frozen validation commands from the active allocation, uses argv + `shell=False`, and requires a stable publishable workspace fingerprint. `passed` is validation evidence only; it does not commit, push, open a PR, mark the Task complete, or release the lease.

## V8 Git Publisher

```bash
graph-engineering publication-run <TASK-ID> \
  --validation <VALIDATION-ID> \
  --commit-message "<message>" \
  --pr-title "<title>" \
  --pr-body "<body>" \
  --base master \
  --json

graph-engineering publication-resume <PUBLICATION-ID> --json
graph-engineering publication-status --publication <PUBLICATION-ID> --json
```

V8 may commit, push without force and open/reuse a PR only for the exact current workspace proven by V7. It never approves/merges a PR, changes Task status, releases leases, removes worktrees, or mutates Neo4j truth.

## V9 Post-Publication Lifecycle

Read-only reconciliation:

```bash
graph-engineering post-publication-status \
  --publication <PUBLICATION-ID> \
  --json
```

Explicit finalization:

```bash
graph-engineering post-publication-finalize \
  --publication <PUBLICATION-ID> \
  --release-lease \
  --json
```

Optional clean worktree removal:

```bash
graph-engineering post-publication-finalize \
  --publication <PUBLICATION-ID> \
  --release-lease \
  --remove-worktree \
  --json
```

V9 requires all of the following before first cleanup mutation:

- terminal V8 `pr_opened` publication evidence;
- exact repository/spec/task/branch/worktree identity;
- GitHub PR is merged;
- merge commit is reachable from the refreshed configured base branch;
- the canonical Spec Kit Task appears exactly once and is already checked complete in that merged base.

V9 never infers or edits Task completion from runtime/publication state. Lease release is explicit. Worktree removal is additionally explicit and has no force-delete path.

If lease release succeeds but worktree cleanup is blocked by dirty/unregistered state, V9 persists a derived receipt. A later retry may resume cleanup without recreating/double-releasing the lease, while merge/base/canonical Task evidence is still revalidated.

See `docs/architecture/POST_PUBLICATION_LIFECYCLE.md` and ADR-0025.

## Human Async Gates and Continuation Prompts

Human/manual/external acceptance that cannot be synchronously proven is documented through `docs/ai/human-async-gates.md`.

A required `PENDING` Human Async Gate blocks claims of final readiness/completion. Green CI does not implicitly pass a distinct human gate, and human acceptance does not replace automated tests.

Every material development pause/handoff must emit a current Continuation Prompt using `docs/ai/continuation-prompt-template.md`. Prompts are derived and must be regenerated after HEAD/PR/CI/Spec/gate changes.

## Derived state

Typical disposable state:

```text
context-packages/
.graphrag/
.execution/
  contexts/
  manifests/
  runs/
  supervisor/
  validation/
  publication/
  post-publication/
```

Do not blindly delete `.execution/worktrees/`: inspect Git worktree/lease state first because those directories may contain uncommitted user work.

## CI / quality

Engineering Graph CI preserves the whole control-plane baseline:

- Python unit/integration tests, including real temporary Git worktrees and harmless local process fixtures;
- application-runtime dependency isolation;
- ephemeral Neo4j schema/sync/idempotency/validation;
- V1 graph queries;
- V2 context freshness/adapters/reproducibility;
- V3 execution manifest/wave checks;
- V4 GraphRAG build/freshness/retrieval/read-only checks;
- V5 process lifecycle safety;
- V6 supervisor ownership/retry behavior;
- V7 validation identity/fingerprint behavior;
- V8 non-force publication/resume behavior;
- V9 post-merge/canonical-completion/cleanup/idempotency behavior.

Spec Kit and Product CI remain independent gates. A final material feature freeze requires Spec Kit + Engineering Graph + Product CI green on the exact same final HEAD, plus no required Human Async Gate remaining `PENDING`.
