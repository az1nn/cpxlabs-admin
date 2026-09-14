# Agent Runner V5

## Purpose

Agent Runner V5 closes the local process-lifecycle gap after V3 `ExecutionAllocation`. V3 chooses and prepares isolated work; V5 starts and observes one coding-agent process inside that already-allocated worktree.

V5 is engineering tooling only. It does not become a scheduler, Git publisher, task authority or product runtime dependency.

## Authority chain

```text
Git / Spec Kit / code / tests / Git history
                    │
                    ▼
          deterministic Engineering Graph
                    │
                    ▼
          V2 ContextPackage / handoff
                    │
                    ▼
          V3 ExecutionAllocation + lease
                    │
                    ▼
              V5 Agent Runner
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       process    run.json    logs
          │         │         │
          └─────────┴─────────┘
                 derived only
```

Authority never points upward from runner state. `status=succeeded` means only that the configured child argv exited with code `0`.

## Preconditions

A run can start only when:

1. a V3 active lease exists for the task;
2. allocation repository matches current repository identity;
3. allocation `sourceRevision` equals current Git HEAD;
4. expected worktree is registered by Git at the allocated path;
5. registered worktree branch equals the allocation branch;
6. handoff file exists;
7. no non-terminal V5 run already exists for the task.

V5 does not create or repair these conditions. Re-plan/re-prepare with V3 when they are stale.

## Process execution

Target commands are arrays, not shell strings:

```text
["codex", "...agent flags..."]
```

The child target is invoked with `shell=False`. Supported allocation placeholders are expanded token-by-token:

- `{task_id}`
- `{spec_id}`
- `{worktree}`
- `{handoff}`
- `{context}`
- `{branch}`
- `{source_revision}`

No shell interpolation, redirection, globbing or command substitution is performed.

The target cwd is always the allocated worktree. The generated handoff can be delivered as stdin, avoiding shell redirection and keeping the handoff path/result traceable.

## Detached wrapper

`runner_child.py` is a small local wrapper around the configured target process. Its responsibilities are limited to process observation:

1. launch target argv with `shell=False`;
2. optionally feed handoff bytes to stdin;
3. stream stdout/stderr to deterministic files;
4. preserve graceful SIGTERM handling;
5. atomically write the final exit result.

The wrapper exists because a later CLI invocation cannot reliably recover the exit code of an already-detached arbitrary child process without an intermediary that records it.

## Derived state

Default:

```text
engineering-graph/.execution/runs/
├── registry.json
└── <run-id>/
    ├── run.json
    ├── stdout.log
    ├── stderr.log
    └── result.json
```

`registry.json`, per-run metadata, logs and result files are disposable. They are already covered by the ignored `.execution/` root.

Deleting `runs/` does not delete:

- V3 leases;
- V3 worktrees;
- branches;
- context source files;
- specs/ADRs;
- code/tests;
- Git history.

## Run states

```text
running
  ├── exit 0 ----------------> succeeded
  ├── exit non-zero ---------> failed
  ├── explicit stop ---------> stopped
  └── process disappears ----> orphaned
```

Terminal states are execution observations only. They never edit `tasks.md` or release the V3 lease.

## Process identity / PID reuse

A PID is not durable process identity. On Linux, V5 records `/proc/<pid>/stat` process start time as part of a fingerprint. Before destructive signaling, V5 compares the current fingerprint with the stored one.

If identity does not match, V5 refuses to signal the PID. This prevents a stale runner record from terminating an unrelated process after PID reuse.

Platforms where safe identity cannot be verified may observe status, but destructive signaling fails closed rather than guessing.

## Stop semantics

The wrapper is launched with a dedicated session/process group. Normal stop:

1. reconciles current run state;
2. verifies stored process identity;
3. records `stopRequested=true`;
4. sends SIGTERM to the recorded process group;
5. waits for terminal evidence.

`--force` permits explicit escalation when graceful termination does not complete. Identity verification still applies before escalation.

Stopping or finishing a run does not automatically release the V3 lease. Lease release remains a separate operator decision:

```bash
graph-engineering execution-release <TASK-ID>
```

## CLI

```bash
graph-engineering runner-start <TASK-ID> \
  --stdin-handoff \
  --json \
  --command <agent-executable> <agent-argv...>

graph-engineering runner-status --task <TASK-ID>
graph-engineering runner-logs <TASK-ID> --stream both
graph-engineering runner-stop <TASK-ID>
```

Every token after `--command` belongs to the child argv. Put runner options before `--command`.

## Secret boundary

The child inherits the operator environment so an already-authenticated local agent CLI can function, but environment values are never serialized into `AgentRun` metadata.

Do not place secrets directly in argv: argv is intentionally persisted for reproducibility/observability.

## Validation

V5 integration tests use temporary real Git repositories/worktrees and harmless Python processes. They verify:

- exact worktree cwd;
- stdin handoff delivery;
- stdout/stderr capture;
- success/failure exit reconciliation;
- duplicate active-run rejection;
- PID/fingerprint mismatch safety;
- graceful stop behavior;
- active V3 lease preservation after runner termination.

No CI gate invokes Codex, Claude or any external agent/network service.

## Explicit non-goals

V5 does not:

- schedule waves;
- retry agents automatically;
- run validation commands automatically;
- infer task completion;
- edit `tasks.md` automatically;
- commit or push;
- open/review/merge pull requests;
- release V3 leases automatically;
- execute remotely;
- mutate Neo4j with process state.

A future supervisor may coordinate multiple V5 runs, but must preserve the same authority boundary unless a separate ADR explicitly changes it.
