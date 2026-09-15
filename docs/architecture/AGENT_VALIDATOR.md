# Agent Validator V7

## Purpose

Agent Validator V7 separates coding-agent process success from implementation validation. It consumes the active V3 allocation, verifies successful V5/V6 execution identity, runs only the allocation's frozen validation commands, and writes disposable machine-readable evidence.

V7 is engineering tooling only. It is not canonical Task state, review approval, lease ownership, a Git publisher or a product-runtime dependency.

## Authority chain

```text
Git / Spec Kit / code / tests
          |
          v
V3 ExecutionAllocation
  | validationCommands
  v
V5 succeeded AgentRun
  | exact run identity
  +--> V6 ownership check when applicable
  v
V7 Agent Validator
  |
  +--> argv subprocesses (shell=False)
  +--> logs + validation record
       derived only
```

## Preconditions

Validation starts only when:

1. the task has an active V3 allocation;
2. allocation repository/source revision/worktree/branch are current and registered;
3. the allocation has at least one frozen validation command;
4. the latest V5 run exists and is `succeeded`;
5. latest V5 repository/task/spec/revision/branch/worktree identity matches the allocation;
6. any active V6 supervisor claim owns that exact latest run id and observes the task as `succeeded`.

## Command provenance and execution

The CLI does not accept `--command`. V7 executes only `validationCommands` persisted by V3 preparation. Every command is tokenized with `shlex.split`, then passed to `subprocess.run(..., shell=False)` with cwd forced to the allocation worktree.

All frozen commands are tokenized before the first subprocess starts. Commands then run sequentially. Execution stops on the first failed command.

## Workspace binding

V7 records the worktree Git revision plus a SHA-256 fingerprint over the tracked diff and non-ignored untracked files before and after validation. A record is `passed` only if every command exits 0 and the publishable workspace fingerprint remains stable while validation runs.

This makes later evidence consumption fail-safe: a future publication layer can require the current workspace to match the validated fingerprint instead of treating an old `passed` record as timeless approval.

## Derived state

```text
engineering-graph/.execution/validation/
├── records/
│   └── <validation-id>.json
└── runs/
    └── <validation-id>/
        ├── command-001.stdout.log
        ├── command-001.stderr.log
        └── ...
```

The entire subtree is disposable and stores no canonical project knowledge.

## CLI

```bash
graph-engineering validation-run <TASK-ID> --json
graph-engineering validation-status --task <TASK-ID> --json
graph-engineering validation-status --validation <VALIDATION-ID> --json
```

## Explicit non-goals

V7 does not:

- infer or write Spec Kit Task completion;
- accept arbitrary validation commands;
- release V3 leases or remove worktrees;
- commit, push, open/review/merge pull requests;
- turn validation success into review approval;
- project validation runtime evidence into Neo4j;
- execute validations remotely.

Publication automation requires a separate spec/ADR and should consume an exact fresh V7 workspace fingerprint rather than extending V7 authority implicitly.
