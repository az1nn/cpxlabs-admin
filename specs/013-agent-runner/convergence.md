# Convergence: Agent Runner V5

**Feature**: `SPEC-013-AGENT-RUNNER`  
**Pre-freeze validation anchor**: `5c2ca3a8e609d3a960d633c4c303554d26e5d421`  
**Status**: Freeze declared; final PR readiness is conditional on all three required workflows being green on the resulting freeze HEAD

## Conclusion

Agent Runner V5 converges against its intended authority boundary. It closes the local process-lifecycle seam after V3 `ExecutionAllocation` without acquiring authority over task selection, canonical Task state, leases, Git publication or Neo4j truth.

Delivered behavior:

- versioned `AgentRun`, runner registry and exit-result contracts;
- atomic local persistence under `.execution/runs/`;
- active V3 allocation/lease requirement;
- repository/revision/worktree/branch/handoff freshness validation;
- literal argv execution with `shell=False`;
- token-local allocation placeholders;
- exact allocated-worktree cwd confinement;
- optional handoff delivery through stdin;
- detached child wrapper with recoverable exit result;
- separate stdout/stderr logs;
- duplicate non-terminal task-run prevention;
- running/succeeded/failed/stopped/orphaned reconciliation;
- Linux process-start fingerprinting for PID-reuse safety;
- graceful process-group SIGTERM plus explicit force escalation;
- local `Popen` ownership/reaping when the launcher remains alive;
- `/proc` zombie-state handling so terminated wrappers are not misclassified as live;
- bounded log reads;
- `runner-start`, `runner-status`, `runner-stop`, `runner-logs`;
- real temporary Git-worktree integration fixtures;
- successful/non-zero/orphan/duplicate/graceful/force lifecycle coverage;
- proof that V3 lease state remains active after runner exit/stop;
- no application runtime dependency.

## Authority convergence

PASS.

```text
Canonical Git / Spec Kit / code / tests / Git history
                     │
                     ▼
             V1 deterministic graph
                     │
                     ▼
             V2 context + handoff
                     │
                     ▼
        V3 allocation + active lease
                     │
                     ▼
             V5 Agent Runner
           ┌─────────┼─────────┐
           ▼         ▼         ▼
        process    run state   logs
           │         │         │
           └─────────┴─────────┘
                  derived only
```

No V5 process state is projected back into canonical Task state. `exitCode=0` is process evidence only.

## Process safety convergence

PASS.

### No shell authority

Target commands are persisted/executed as argv arrays with `shell=False`. Runner options terminate at `--command`; remaining tokens are literal child argv. Allocation placeholders are token-local substitution rather than shell interpolation.

### Worktree confinement

Start requires the expected V3 Git worktree to be registered on the allocated branch and launches the wrapper with cwd fixed to that worktree.

### PID reuse and process observation

Linux runs persist `/proc/<pid>/stat` process-start identity. Stop refuses to signal a PID whose current fingerprint differs from the stored one. The runner also treats `/proc` state `Z` as terminal rather than alive and reaps locally-owned wrappers through retained `Popen` handles when possible.

### Process tree termination

The wrapper runs in a dedicated process group/session. Normal stop requests SIGTERM; explicit `--force` may escalate to SIGKILL only after identity validation.

A separate-CLI integration fixture intentionally ignores SIGTERM and proves the force path can terminate it while preserving the V3 lease.

## Detached-result convergence

PASS.

The child wrapper records terminal result state atomically so a later CLI process can observe exit code without being the original OS parent of the target.

Testing exposed two important lifecycle edges and both are now covered by implementation behavior:

1. graceful wrapper termination must still leave recoverable terminal evidence;
2. a dead wrapper may remain briefly visible as a Linux zombie and must not be classified as an active runner.

## State / secret convergence

PASS.

Default state:

```text
engineering-graph/.execution/runs/
├── registry.json
└── <run-id>/
    ├── run.json
    ├── stdout.log
    ├── stderr.log
    └── result.json
```

The state is beneath the Git-ignored `.execution/` root and is disposable. Environment values are inherited only at process execution time and are never serialized into `AgentRun`. Because argv is intentionally recorded, documentation explicitly prohibits putting secrets directly in command argv.

## V1–V5 compatibility

PASS on pre-freeze anchor `5c2ca3a8e609d3a960d633c4c303554d26e5d421`:

- Spec Kit #372: success;
- Engineering Graph #303: success;
- Product CI #703: success.

Engineering Graph #303 includes the complete V1–V5 suite, runtime dependency isolation, ephemeral Neo4j validation, V2 ContextPackage checks, V3 execution checks and V4 GraphRAG checks.

Because this convergence/ledger update changes Git HEAD, the repository freeze is accepted only after the same three workflow domains are green again on the resulting final HEAD. No further repository mutation is needed after that acceptance; final run IDs may be recorded in PR metadata without changing the frozen commit.

## Test evidence

V5 tests cover:

- run/registry/result schema and malformed registry rejection;
- duplicate non-terminal registry/run rejection;
- literal argv placeholder behavior;
- exact real Git-worktree cwd;
- stdin handoff delivery;
- stdout/stderr capture;
- successful exit reconciliation;
- non-zero exit reconciliation;
- vanished-process orphan reconciliation;
- fingerprint mismatch safety;
- graceful stop;
- force escalation in separate CLI invocations with a SIGTERM-ignoring child;
- zombie/reaping lifecycle behavior exercised by the core stop tests;
- V3 active lease preservation after success/failure/stop;
- runner CLI command parsing/routing/JSON surfaces.

## Deliberately deferred

The following are not V5 convergence gaps:

- wave-level supervisor/scheduler;
- automatic retries/backoff;
- automatic validation-command execution;
- remote/distributed execution;
- automatic Task status changes;
- automatic lease release;
- commit/push/PR/review/merge automation;
- process-state projection into Neo4j;
- interpretation of agent output/log text as canonical evidence.

A future supervisor/publication layer requires a new spec/ADR and must preserve the authority direction unless explicitly redesigned.

## Freeze contract

`tasks.md` declares T001–T081 complete. That declaration becomes accepted only when Spec Kit, Engineering Graph and Product CI all report success for the resulting final HEAD. If any gate fails, V5 is not frozen and the failing cause must be corrected before PR readiness.
