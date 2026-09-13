# Analysis: Agent Runner V5

**Feature**: `SPEC-013-AGENT-RUNNER`  
**Status**: Coverage complete; freeze declaration awaiting same-HEAD workflow acceptance

## Result

No specification/implementation authority inversion was found. V5 remains a local derived process-lifecycle layer over an already-active V3 allocation.

## Functional requirement coverage

| Requirement | Evidence |
|---|---|
| FR-001–FR-002 | `runner.load_active_allocation` reads V3 `leases.json` and requires an active lease; V5 does not allocate work. |
| FR-003–FR-006 | `validate_allocation_for_run` checks repository identity, Git HEAD/source revision, registered expected worktree/branch and handoff existence. |
| FR-007 | `start_run` launches the wrapper with `cwd=allocation.worktree_path`; real-worktree tests assert observed cwd. |
| FR-008 | Target execution in `runner_child.py` uses argv + `shell=False`. |
| FR-009 | `expand_command` supports a fixed token-local allocation placeholder set. |
| FR-010 | `--stdin-handoff` passes allocation handoff bytes to child stdin without shell redirection. |
| FR-011 | `runner-start --command ...` accepts literal argv remainder. |
| FR-012 | `AgentRun` contains no environment map/value fields; environment is inherited but not serialized. |
| FR-013–FR-016 | Versioned `AgentRun`, `RunnerRegistry`, `RunnerExitResult`, validation and atomic temp/fsync/replace persistence are implemented in `runner.py`/`runner_child.py`. |
| FR-017 | Default state is `.execution/runs/`, under the already ignored `.execution/` root. |
| FR-018–FR-019 | Registry validation and `start_run` reject more than one non-terminal run for one task. |
| FR-020–FR-021 | `runner-status`/`reconcile_registry` refresh result/liveness and convert vanished processes to terminal `orphaned`. |
| FR-022–FR-023 | Linux `/proc/<pid>/stat` start-time fingerprint is stored/compared before destructive signaling; mismatch fails closed. Zombie state is treated as terminal rather than alive. |
| FR-024–FR-025 | `stop_run` sends process-group SIGTERM first and allows explicit `--force` SIGKILL escalation only after identity validation; locally-owned wrappers are reaped through retained `Popen` handles. |
| FR-026 | Exit code is persisted into runner state only; no canonical Task mutation path exists. |
| FR-027 | `stop_run`/reconciliation do not call V3 lease release; tests assert active lease remains. |
| FR-028–FR-030 | `runner-start`, `runner-status`, `runner-stop`, `runner-logs` expose JSON and human renderings via `runner_cli.py`/`runner_entry.py`. |
| FR-031 | `read_run_logs` reads bounded local stdout/stderr files only. |
| FR-032 | Run state is isolated under `.execution/runs/`; worktree/lease APIs are not cleanup targets. |
| FR-033 | Existing application-runtime dependency isolation gate covers `engineering_graph`/Neo4j imports. |
| FR-034 | V1–V4 tests remain in the same Engineering Graph suite and passed with V5 on the pre-freeze validation anchor. |
| FR-035–FR-037 | V5 tests use harmless Python fixtures, including real temporary Git worktrees, duplicate-run prevention, terminal/stop behavior and lease preservation. |
| FR-038 | `.execution/` remains ignored; V5 stores all generated state beneath it. |

## Success criteria coverage

| Criterion | Evidence |
|---|---|
| SC-001 | Real temporary Git worktree test launches a local fixture, captures cwd/stdin/stdout/stderr and records run/result state. |
| SC-002 | Duplicate non-terminal launch raises `RunnerCollisionError`. |
| SC-003 | Result/liveness reconciliation produces terminal state without a Task mutation API. |
| SC-004 | Graceful stop test terminates a long-running local fixture and records `stopped`. |
| SC-005 | Fingerprint mismatch test proves V5 does not signal a mismatched process identity. |
| SC-006 | Runner CLI surfaces provide JSON contracts suitable for later orchestration. |
| SC-007 | Runner files are below `.execution/runs/`; V3 worktree/lease state is separate. |
| SC-008 | Engineering Graph #303 passed the complete V1–V5 suite on pre-freeze anchor `5c2ca3a8…`. |
| SC-009 | Product CI #703 passed on the same pre-freeze anchor. |
| SC-010 | Spec Kit #372, Engineering Graph #303 and Product CI #703 were green on the same pre-freeze anchor; freeze acceptance requires the same condition again on the resulting final HEAD. |

## Safety / authority review

### Process success is not project success

PASS structurally. No code path translates `exitCode=0` or `status=succeeded` into Task status, Git commit, PR state, lease release or Neo4j relationship state.

### PID reuse and zombie observation

PASS on Linux. A stop operation validates persisted PID plus process-start fingerprint before signaling. An identity mismatch is treated as unsafe and not signaled. `/proc` state `Z` is treated as terminal, preventing a dead wrapper from being misclassified as live while awaiting reap.

### Local process ownership

PASS. When `start_run` and `stop_run` execute inside the same long-lived Python process, the launcher retains the wrapper `Popen` and polls/waits it during reconciliation. This removes the zombie-observation race and avoids leaking locally-owned child handles. Detached later CLI invocations remain supported through persisted PID/fingerprint/result state.

### Shell injection / argv ambiguity

PASS. Target invocation is `shell=False`; runner options precede `--command`, and the remaining tokens are literal child argv. Allocation placeholders are token-local string substitution, not shell syntax.

### Secret persistence

PASS. Child environment may be inherited for local authentication, but environment values are absent from `AgentRun`. Documentation explicitly warns that argv is persisted and therefore must not contain secrets.

### Worktree confinement

PASS. Start validates the registered V3 worktree/branch and fixes wrapper cwd to the allocation worktree. V5 cannot select an arbitrary cwd through its CLI.

### Detached exit recovery

PASS. `runner_child.py` records a versioned exit result so later CLI invocations can reconcile terminal status without needing to remain the OS parent of the target process.

## Validation evidence

Pre-freeze validation anchor: `5c2ca3a8e609d3a960d633c4c303554d26e5d421`.

- Spec Kit #372 — success.
- Engineering Graph #303 — success, including complete V1–V5 offline/integration coverage, runtime isolation, Neo4j, V2, V3 and V4 gates.
- Product CI #703 — success.

The freeze documentation changes Git HEAD, so these runs establish implementation readiness but do not alone satisfy the final same-HEAD freeze contract. The resulting freeze HEAD must pass the same three domains before PR readiness.

## V1–V5 compatibility

```text
V1 deterministic graph / planner
        ↓
V2 ContextPackage / handoff
        ↓
V3 ExecutionAllocation + active lease
        ↓
V4 optional retrieval assistance (orthogonal)
        ↓
V5 local process lifecycle
```

V5 adds no Neo4j labels/relationships, no product runtime dependency and no second task planner/worktree allocator.

## Deferred by design

Not convergence gaps:

- wave-level supervisor/scheduler;
- automatic retries/backoff;
- automatic validation-command execution;
- remote/distributed runners;
- Task status mutation;
- automatic lease release;
- commit/push/PR/review/merge automation;
- process-state projection into Neo4j;
- interpreting agent text/logs as canonical evidence.

Any publication/supervisor layer requires a separate spec/ADR and must preserve the authority boundary unless explicitly redesigned.

## Freeze acceptance rule

The task ledger now declares T001–T081 complete as the freeze declaration. That declaration is accepted only when Spec Kit, Engineering Graph and Product CI all succeed on the resulting final HEAD. A failure in any domain reopens convergence and requires correction before the PR may become Ready for Review.
