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
