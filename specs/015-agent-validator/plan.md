# Implementation Plan: Agent Validator V7

## Summary

Add a local validation boundary after V5/V6 execution and before any future publication automation. V7 consumes the active V3 allocation as the command authority, verifies successful V5/V6 ownership evidence, executes only frozen validation commands with `shell=False`, binds the result to a deterministic workspace fingerprint, and persists bounded disposable evidence under `.execution/validation/`.

## Architecture

```text
Git / Spec Kit / code / tests
          |
          v
V3 active ExecutionAllocation
  | frozen validationCommands
  v
V5 latest succeeded AgentRun
  |
  +-- optional V6 exact runId ownership check
  v
V7 Agent Validator
  |
  +--> workspace fingerprint before
  +--> sequential argv subprocesses (shell=False)
  +--> stdout/stderr command logs
  +--> workspace fingerprint after
  +--> versioned validation record
       derived/disposable only
```

## Implementation slices

1. Add `validation.py` models, invariants, atomic persistence and status lookup.
2. Reuse V3 allocation/worktree safety and V5 registry reconciliation rather than duplicating ownership models.
3. Add optional V6 exact-run ownership verification when a supervisor job claims the task.
4. Pre-tokenize only allocation-frozen commands with `shlex.split`; execute sequentially with `shell=False` and captured files.
5. Bind evidence to Git HEAD plus SHA-256 over tracked diff and non-ignored untracked files before/after validation; fail overall validation on drift.
6. Add `validation-run` and `validation-status` CLI surfaces through the composed local entrypoint.
7. Add unit/CLI tests for success, first-failure stop, stale/unsuccessful run rejection, supervisor ownership mismatch, workspace mutation and command-injection absence.
8. Add architecture/operator documentation plus a scoped `engineering-graph/AGENTS.md` workflow.
9. Run convergence and freeze only after Spec Kit + Engineering Graph + Product CI are green on one final HEAD.

## Safety invariants

- V7 never invents validation commands; V3 allocation is the only command source.
- V7 never invokes a shell.
- Validation starts only after successful execution evidence with matching allocation identity.
- Supervisor evidence, when present, must own the exact latest V5 run id.
- A `passed` record requires an unchanged worktree revision/fingerprint throughout validation.
- Validation evidence never means Task completion or review approval.
- V7 never writes canonical project artifacts, releases leases or publishes Git state.
- Logs/records remain under ignored `.execution/validation/`.

## Compatibility

No product package imports `engineering_graph`. V3–V6 APIs remain unchanged; V7 composes existing allocation, runner and supervisor read/reconcile primitives. No Neo4j schema change is required.

## Complexity tracking

A separate validator is justified because V6 process success deliberately does not establish correctness. Keeping validation separate preserves least authority and creates a stable evidence boundary that a future publication layer may consume without turning V7 itself into a Git publisher.
