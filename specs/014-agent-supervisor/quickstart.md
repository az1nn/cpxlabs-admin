# Quickstart: Agent Supervisor V6

V6 assumes V3 planning/preparation has already produced active allocations for one wave.

```bash
graph-engineering execution-plan \
  --spec SPEC-014-AGENT-SUPERVISOR \
  --agent codex \
  --output /tmp/execution.json

graph-engineering execution-prepare /tmp/execution.json --wave 1
```

Create a supervisor job and perform its first tick:

```bash
graph-engineering supervisor-start /tmp/execution.json \
  --wave 1 \
  --max-parallel 2 \
  --max-attempts 2 \
  --stdin-handoff \
  --json \
  --command codex <agent-args...>
```

Advance the job after runner state changes:

```bash
graph-engineering supervisor-tick <JOB-ID> --json
```

Inspect without launching work:

```bash
graph-engineering supervisor-status --job <JOB-ID> --json
```

Stop only job-owned active runs:

```bash
graph-engineering supervisor-stop <JOB-ID> --json
```

Supervisor completion does not release V3 leases. Review canonical evidence and release explicitly when appropriate:

```bash
graph-engineering execution-release <TASK-ID>
```
