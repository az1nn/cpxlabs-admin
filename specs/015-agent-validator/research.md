# Research: Agent Validator V7

## Decision 1 — Validation command authority

Use the V3 `ExecutionAllocation.validationCommands` tuple as the only command source. The commands are created from deterministic task context before execution allocation and therefore have a narrower, reviewable provenance than arbitrary operator input.

Rejected: accepting `validation-run --command ...`. That would let the validator redefine the gate at execution time and weaken the evidence contract.

## Decision 2 — Process precondition

Require the latest V5 run to be `succeeded` and identity-compatible with the active allocation. V5 exit code 0 is only a process observation; it is necessary for V7 but never sufficient for correctness.

When V6 currently owns the task, require exact latest `runId` ownership plus a `succeeded` supervisor observation. This prevents validation from silently attaching to a different process than the active supervisor believes it owns.

## Decision 3 — No shell

Tokenize frozen command strings with `shlex.split` and execute argv with `shell=False`. Tokenize the complete command set before starting the first process so malformed later commands cannot create partial validation execution.

Rejected: shell invocation. The allocation commands in this repository are simple executable commands and do not require shell expansion; a shell would add unnecessary interpretation/injection surface.

## Decision 4 — Workspace identity

A successful command sequence is not durable evidence if the publishable workspace changes during the sequence. Record:

- Git worktree `HEAD`;
- SHA-256 over the tracked binary diff from `HEAD`;
- sorted non-ignored untracked file paths/types/content.

Compute before and after. Overall `passed` requires identical revision and fingerprint.

Ignored/generated files are intentionally excluded because they are not publication inputs under normal Git semantics.

## Decision 5 — Evidence lifecycle

Persist metadata under `.execution/validation/records/` and logs under `.execution/validation/runs/`. Both are derived and disposable. Do not add Neo4j nodes/relationships for runtime validation observations.

## Decision 6 — Publication boundary

Do not commit, push, open PRs, merge, release leases or mark tasks complete. A future publication layer may consume a fresh exact V7 record but requires a separate spec/ADR because its authority changes canonical Git/provider state.
