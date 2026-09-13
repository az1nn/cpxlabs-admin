# Convergence: Agent Runner V5

**Feature**: `SPEC-013-AGENT-RUNNER`  
**Implementation anchor**: `6fd7f499becc835a16cbf993253a0893278af1fb`  
**Status**: Converging — implementation complete, final closeout/freeze gates pending

## Conclusion

Agent Runner V5 is implementation-complete against its intended authority boundary. It closes the local process-lifecycle seam after V3 `ExecutionAllocation` without acquiring authority over task selection, canonical Task state, leases, Git publication or Neo4j truth.

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

### PID reuse

Linux runs persist `/proc/<pid>/stat` process-start identity. Stop refuses to signal a PID whose current fingerprint differs from the stored one.

### Process tree termination

The wrapper runs in a dedicated process group/session. Normal stop requests SIGTERM; explicit `--force` may escalate to SIGKILL only after identity validation.

A separate-CLI integration fixture intentionally ignores SIGTERM and proves the force path can terminate it while preserving the V3 lease.

## Detached-result convergence

PASS.

The child wrapper records terminal result state atomically. This allows a later CLI process to observe exit code without being the original OS parent of the target.

Initial testing exposed a zombie-observation edge when a graceful wrapper could exit before recording terminal evidence. The wrapper now handles SIGTERM, forwards termination and records exit evidence before leaving the process lifecycle.

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

The state is already beneath the Git-ignored `.execution/` root and is disposable. Environment values are inherited only at process execution time and are never serialized into `AgentRun`.

Because argv is intentionally recorded, documentation explicitly prohibits putting secrets directly in command argv.

## V1–V5 compatibility

PASS at the implementation anchor.

Engineering Graph #297 on `6fd7f499…` passed:

- all 102 Python unit/integration tests, including V5 real-worktree and separate-CLI force fixtures;
- application-runtime dependency isolation;
- ephemeral Neo4j schema/sync/idempotency/validation;
- V1 fundamental query smokes;
- V2 ContextPackage generation/freshness/adapters/reproducibility/disposal;
- V3 ExecutionManifest/wave/completed-spec gates;
- V4 GraphRAG build/freshness/reproducibility/retrieval/graph expansion/read-only stats gate.

Spec Kit #367 also passed on the same implementation anchor.

Product CI #697 was still running when this convergence document was authored; final freeze will require a fresh three-domain validation on the final HEAD regardless of this initial anchor.

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
- fingerprint mismatch safety against the current test process;
- graceful stop;
- force escalation in separate CLI invocations with a SIGTERM-ignoring child;
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

## Closeout state

Implementation and analysis are complete. Before V5 is frozen and PR #21 becomes Ready for Review:

1. reconcile the Spec 013 task ledger against actual evidence;
2. run Spec Kit, Engineering Graph and Product CI on the resulting closeout HEAD;
3. record final run IDs/HEAD;
4. mark T081 complete only after all three are green on the same final HEAD;
5. repeat the three gates if the freeze ledger/convergence update changes HEAD.
