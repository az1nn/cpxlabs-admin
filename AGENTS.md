# AGENTS.md

This repository uses GitHub Spec Kit for material feature development and a repository-local Neo4j Engineering Graph as derived navigation/context/execution infrastructure.

## Source of Truth

Canonical knowledge is always authored in Git-backed files: `.specify/`, `specs/`, `docs/adr/`, source code, tests and Git history. The Engineering Graph is a rebuildable projection only. Never author canonical requirements, architecture decisions, task state, implementation evidence or test evidence directly in Neo4j.

Generated Agent Context Graph packages, Execution Graph manifests, leases and handoffs are also derived and disposable. They are task/execution maps tied to a Git revision, not canonical documentation.

If Neo4j is unavailable, continue from the canonical files. Graph unavailability may reduce planning/context/execution automation but MUST NOT block application runtime or change business behavior.

## Start Here

Before changing a material feature, read:

1. `.specify/memory/constitution.md`
2. the active `specs/###-slug/spec.md`
3. its `plan.md`
4. its `tasks.md`
5. relevant ADRs under `docs/adr/`

If a material feature has no active Spec Kit artifacts, create them before implementation.

When the Engineering Graph is available, use it to reduce context and validate dependencies rather than replacing the files above:

```bash
cd engineering-graph
graph-engineering sync
graph-engineering validate
graph-engineering impact <CANONICAL_ID>
graph-engineering context <TASK_CANONICAL_ID>
graph-engineering context-batch --task <TASK_CANONICAL_ID>
graph-engineering context-validate context-packages/.../context.json --strict
graph-engineering waves --spec <SPEC_CANONICAL_ID>
graph-engineering execution-plan --spec <SPEC_CANONICAL_ID> --agent codex --output .execution/manifest.json
```

Treat graph results as derived evidence. Before editing, follow returned `sourcePath`/`path` references to the canonical files.

## Agent Context Package Workflow

For an implementation task when Neo4j is available:

1. `graph-engineering sync` after relevant specs/tasks/ADRs change;
2. `graph-engineering validate` and fix error-level graph findings;
3. generate a package with `graph-engineering context-batch --task <TASK-ID>` or generate all READY work with `--spec <SPEC-ID>`;
4. run `graph-engineering context-validate <context.json> --strict` immediately before implementation;
5. Codex uses the generated `codex.md`; Claude Code uses `claude.md`;
6. open the canonical files listed by the handoff/package before editing;
7. run repository validation commands after changes;
8. discard/regenerate packages whenever Git revision or graph evidence changes.

A stale package is not current implementation context. Never bypass strict freshness because a generated file “looks right.”

`context-batch --spec` selects READY tasks only. BLOCKED tasks require explicit task selection; package generation is not authority to ignore dependency state.

## Conversation Context Handoffs

AI-assisted work must follow `docs/ai/context-handoff.md`.

The repository-owned source for ChatGPT Project Instructions is `docs/ai/chatgpt-project-instructions.md`. Mirror that file into the ChatGPT Project settings when configuring the project; future policy edits belong in Git first.

Continuously assess whether the current conversation remains a coherent working context. Do not display context-health status on every response and do not recommend a new chat merely because the conversation is long.

Prefer semantic handoff boundaries: completed feature/PR group, Spec Kit phase, milestone, architecture freeze, workstream change, or a point where stale/superseded conversation state materially increases implementation risk.

When the policy reaches RED, explicitly recommend a new chat and generate a `SESSION_HANDOFF.md` from `docs/ai/session-handoff-template.md`. The handoff must summarize final state, identify superseded decisions, point to canonical Git-backed artifacts, record freshness risks, and provide one exact `Next Action`.

A new chat must validate repository freshness and re-read the bounded canonical artifacts it needs. `SESSION_HANDOFF.md`, chat history, ContextPackages, graph projections, and execution manifests are derived context and never override Git-backed source of truth.

## Execution Graph Workflow

V3 may allocate implementation work into isolated Git worktrees. Use this only after the graph is synchronized and validated.

```bash
graph-engineering execution-plan \
  --spec <SPEC-ID> \
  --agent codex \
  --output engineering-graph/.execution/manifests/<spec>.json

graph-engineering execution-prepare \
  engineering-graph/.execution/manifests/<spec>.json \
  --wave 1 \
  --dry-run

graph-engineering execution-prepare \
  engineering-graph/.execution/manifests/<spec>.json \
  --wave 1

graph-engineering execution-status
```

Rules for prepared allocations:

- work only inside the `worktreePath` returned for the Task;
- read the generated `handoffPath` and `contextPath`, then open canonical repository files before editing;
- do not edit `.execution/` files as project knowledge;
- an active lease means “allocated”, not “Task complete”;
- do not manually move a Task to done based on lease state; update canonical `tasks.md` only when implementation evidence warrants it;
- do not combine tasks from different execution waves to bypass dependency/conflict safety;
- if Git HEAD changes after planning, re-sync/replan rather than bypassing revision checks;
- dirty worktrees are user data and must not be removed automatically.

Release a lease when work is no longer allocated:

```bash
graph-engineering execution-release <TASK-ID>
```

Remove a clean generated worktree only when desired:

```bash
graph-engineering execution-release <TASK-ID> --remove-worktree
```

`--force` is destructive and should be used only when the operator intentionally discards dirty worktree contents.

Execution Graph does not authorize automatic commit, push, PR creation, merge or canonical task-status mutation.

## Spec Kit Commands

Codex is the versioned default integration and uses native skills:

- `$speckit-constitution`
- `$speckit-specify`
- `$speckit-clarify`
- `$speckit-plan`
- `$speckit-tasks`
- `$speckit-analyze`
- `$speckit-implement`
- `$speckit-converge`

OpenCode is supported through the official Specify CLI integration switch, not simultaneous installation. Spec Kit v1.0.4 declares the OpenCode integration unsafe for multi-install alongside Codex. When working locally with OpenCode, switch to it with `specify integration switch opencode`, use the generated `/speckit.*` commands, then switch back to Codex before committing managed integration files.

Specifications `001` through `004` are historical retrofits. New feature work starts through Spec Kit; do not use those historical files as evidence that the earlier implementation followed Spec Kit originally.

## Graph-Friendly Authoring

Stable explicit references improve deterministic graph quality. Prefer these conventions when they are known during authoring:

- keep Spec Kit requirement IDs (`FR-###`, `SC-###`) and task IDs (`T###`) stable inside a feature;
- reference ADRs by stable ID such as `ADR-0019`;
- place repository paths in backticks when a task is expected to change or validate a concrete file;
- express real task dependencies explicitly with `depends: T001,T002` instead of relying on phase ordering;
- optional YAML frontmatter may add graph metadata, but must remain readable and useful without Neo4j;
- never add a graph edge merely because an AI model considers two concepts similar.

The graph canonicalizes local IDs under the parent spec, e.g. `SPEC-011-EXECUTION-GRAPH:T001`, so task IDs can remain human-friendly in `tasks.md`.

## Architecture Rules

- `apps/web` may depend on shared contracts/providers but never Prisma/database/Fastify implementation details.
- `apps/api` keeps persistence behind repository interfaces.
- `packages/contracts` contains transport/application contracts only; never export ORM-generated types.
- TanStack Router owns route/search/URL state; TanStack Query owns remote cache.
- `DataProvider` is for generic CRUD only. Domain workflows require explicit named use cases/APIs.
- Authorization UI checks are UX only. Server authorization is authoritative and deny-by-default.
- Add a package only when there is a concrete reuse/boundary need; avoid premature internal frameworks.
- Structural/cross-cutting decisions require an ADR.
- No application package may import the Neo4j driver or `engineering_graph`; Graph Engineering belongs to development/CI tooling only.
- Agent adapters consume portable ContextPackage files; they do not implement independent graph traversal or write canonical project knowledge.
- Execution Graph worktrees/leases are derived local orchestration state; they do not replace canonical Task status or branch/PR review authority.

## Graph-Assisted Planning

For material work after `tasks.md` exists:

1. run `graph-engineering sync`;
2. run `graph-engineering validate` and fix error-level findings;
3. run `graph-engineering ready --spec <SPEC>` and `graph-engineering conflicts --spec <SPEC>`;
4. use `graph-engineering waves --spec <SPEC>` or `execution-plan` to propose parallel work only when the explicit dependency DAG and changed-artifact evidence support it;
5. generate/validate a bounded context package before assigning implementation work, or let `execution-prepare` do this as part of allocation;
6. re-sync/replan after task/spec/ADR/code/test/PR evidence changes.

A generated execution wave is a plan, not authority to bypass branch/MR ownership, CI, review or the Spec Kit lifecycle.

## Quality Gates

Do not weaken TypeScript or CI rules to make a change pass.

Baseline application commands:

```bash
pnpm typecheck
pnpm test
pnpm build
pnpm test:storybook
pnpm e2e
```

Engineering Graph validation is additional:

```bash
cd engineering-graph
python -m unittest discover -s tests -v
graph-engineering doctor --wait 60
graph-engineering schema
graph-engineering sync
graph-engineering validate
```

Keep `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` enabled. Critical HTTP/database journeys must remain covered against the real reference API and PostgreSQL where applicable. Graph validation supplements but never replaces application tests.

## Pull Requests

A material PR should include:

- Spec path
- tasks completed
- ADRs added/changed
- tests and validation performed
- convergence status or remaining gaps

When Graph Engineering is available, the PR should also be syncable into the graph so `PR -> Task -> Spec -> Requirement` and `PR -> CodeArtifact/Test` evidence can be queried where explicit identifiers/changed paths support those edges.

Implementation that diverges materially from the spec/plan must update those artifacts before merge.
