# Engineering Graph Agent Instructions

These instructions refine the repository-root `AGENTS.md` for files under `engineering-graph/`. Root source-of-truth, Spec Kit, review and Git authority rules still apply.

## Agent Validator V7

V7 is post-execution validation infrastructure for an already-active V3 allocation. It is not Task completion authority and not Git publication authority.

Before relying on V7, verify execution state:

```bash
graph-engineering execution-status --json
graph-engineering runner-status --task <TASK-ID> --json
```

Run and inspect validation:

```bash
graph-engineering validation-run <TASK-ID> --json
graph-engineering validation-status --task <TASK-ID> --json
```

Rules:

- validation commands come only from the active allocation's frozen `validationCommands`; do not add a CLI/API command override;
- keep command execution as argv with `shell=False` and cwd fixed to the allocation worktree;
- latest V5 run must be `succeeded` and identity-compatible with the allocation;
- when V6 supervisor evidence applies, require exact latest `runId` ownership and successful task observation;
- `passed` requires every frozen command to pass and the publishable workspace revision/fingerprint to remain stable before/after validation;
- `.execution/validation/` is derived disposable state, never canonical project knowledge;
- validation success never edits `tasks.md`, releases leases, removes worktrees, commits, pushes, opens/reviews/merges PRs or mutates Neo4j;
- after any publishable workspace change, old validation evidence is stale for publication purposes and validation must run again.

See `docs/architecture/AGENT_VALIDATOR.md` and ADR-0023.

## Git Publisher V8

V8 is the next authority tier after V7. It may publish only an exact current workspace already proven by an explicit passed V7 record.

Rules:

- require exact allocation/validation/worktree/branch identity before mutation;
- fail closed on workspace fingerprint drift;
- preserve a durable publication phase record after each irreversible step;
- never rewrite remote history;
- resume from a recorded commit instead of creating a duplicate commit;
- detect an existing open PR for the exact branch/base pair before creating another;
- publication success does not mark tasks complete, release leases, remove worktrees, merge/approve PRs, or mutate Neo4j;
- `.execution/publication/` is derived disposable evidence.

See `docs/architecture/GIT_PUBLISHER.md` and ADR-0024.

## Post-Publication Lifecycle V9

V9 closes derived execution state after V8 publication and human merge. It is reconciliation/cleanup infrastructure, not Task completion or merge authority.

Inspect before cleanup:

```bash
graph-engineering post-publication-status --publication <PUBLICATION-ID> --json
```

Explicit finalization:

```bash
graph-engineering post-publication-finalize \
  --publication <PUBLICATION-ID> \
  --release-lease \
  --json
```

Optional worktree removal requires additional explicit intent:

```bash
graph-engineering post-publication-finalize \
  --publication <PUBLICATION-ID> \
  --release-lease \
  --remove-worktree \
  --json
```

Rules:

- PR review/merge remains human/external authority; V9 only inspects current PR state;
- a merged PR does not itself mark the Spec Kit Task complete;
- refresh the configured base, prove the merge commit is reachable, then read the canonical Task checkbox from the merged base;
- missing, ambiguous, or unchecked canonical Task evidence blocks cleanup; never edit the checkbox from derived runtime/publication evidence;
- lease release requires explicit `--release-lease` intent;
- worktree removal additionally requires `--remove-worktree` and a clean matching worktree;
- V9 intentionally exposes no force-delete path for dirty worktrees;
- `.execution/post-publication/` receipts are derived idempotency/audit evidence, never project truth or Neo4j truth;
- if lease release succeeds but worktree cleanup is blocked, a later retry may resume only the cleanup phase; merge/base/canonical Task evidence must still be revalidated;
- do not recreate or double-release a lease merely to satisfy a retry.

See `docs/architecture/POST_PUBLICATION_LIFECYCLE.md` and ADR-0025.

## Continuation Prompts

Follow `docs/ai/continuation-prompt-template.md` and `docs/ai/context-handoff.md`.

Every material development update that leaves follow-up work possible must include a ready-to-paste Continuation Prompt with current repository/base/branch/PR/HEAD/Spec, automated gates, unresolved Human Async Gates, one exact Next Action, freshness instructions, and the current authority boundary.

Regenerate it whenever HEAD, PR, CI, Spec Kit, or gate state changes. It is derived context and never overrides Git.

## Human Async Gates

Follow `docs/ai/human-async-gates.md`.

- a required `PENDING` human gate blocks final readiness/completion claims;
- green automated CI never implicitly passes a distinct human gate;
- human acceptance never replaces required automated tests;
- agents must never self-pass or self-waive a human gate;
- automated CI that is merely still running is an automated pending gate, not a Human Async Gate unless human/external acceptance is genuinely required;
- unresolved required gates must appear in the Continuation Prompt and session handoff.

Final feature freeze requires Spec Kit + Engineering Graph + Product CI green on the same final HEAD and no required Human Async Gate remaining `PENDING`.
