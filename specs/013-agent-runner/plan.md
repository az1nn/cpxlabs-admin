# Implementation Plan: Agent Runner V5

## Architecture

```text
canonical Git / Spec Kit / code / tests
                │
                ▼
      V1 Engineering Graph
                │
          V2 ContextPackage
                │
          V3 Execution Graph
                │
       active ExecutionAllocation
                │
                ▼
          V5 Agent Runner
        ┌───────┼────────┐
        ▼       ▼        ▼
   process   run state   logs
        │       │        │
        └───────┴────────┘
             derived only
```

## Modules

### `runner.py`

Own versioned models and lifecycle operations:

- `AgentRun`;
- `RunnerRegistry`;
- command expansion;
- process fingerprinting;
- atomic run/registry persistence;
- start/status/stop/log reads.

### `runner_child.py`

Small subprocess wrapper invoked by the runner. Responsibilities:

1. receive target argv and optional handoff stdin file path;
2. run target argv with `shell=False` in inherited cwd/environment;
3. stream target stdout/stderr into runner-owned files;
4. atomically write `result.json` with exit code/end timestamp;
5. return the target exit code.

The wrapper is needed so detached runs can later recover exit status.

### `runner_cli.py`

CLI-specific argument handling and human/JSON rendering. `cli.py` only registers the surfaces.

## Start algorithm

1. load V3 lease registry;
2. require exactly one active allocation for task;
3. assert repository and Git HEAD equal allocation identity;
4. assert expected Git worktree registration;
5. assert handoff exists;
6. load runner registry and reconcile existing task run;
7. reject existing non-terminal run;
8. resolve argv from explicit override/config template with safe placeholders;
9. create run directory and initial record atomically;
10. launch wrapper in a new session with cwd=allocation worktree;
11. record PID/process fingerprint;
12. return `AgentRun`.

## Status algorithm

1. load run record;
2. if terminal, return it;
3. if `result.json` exists, finalize succeeded/failed/stopped from recorded exit result;
4. otherwise inspect PID + fingerprint;
5. fingerprint matches/alive -> running;
6. process absent -> orphaned;
7. fingerprint mismatch -> identity-mismatch error state for signaling purposes; never signal it.

## Stop algorithm

1. reconcile run;
2. require non-terminal running state;
3. require verifiable fingerprint equality;
4. send SIGTERM to the runner process group;
5. wait bounded interval;
6. if still alive and `--force`, send SIGKILL;
7. reconcile result and mark stop-requested/terminal metadata;
8. leave V3 lease/worktree untouched.

## Command model

The runner stores argv exactly as launched. No shell string is executed. Placeholder expansion is token-local and limited to:

- `{task_id}`
- `{spec_id}`
- `{worktree}`
- `{handoff}`
- `{context}`
- `{branch}`
- `{source_revision}`

Handoff content may be sent to stdin independently of argv.

## Validation strategy

Unit tests use temporary Git repositories and harmless Python fixtures. CI never invokes Codex/Claude or external network APIs.

## Compatibility

V1–V4 APIs remain unchanged. V5 reads V3 leases/allocations and adds no Neo4j schema/relationship vocabulary.
