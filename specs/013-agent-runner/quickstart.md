# Quickstart: Agent Runner V5

## Prerequisites

Prepare an allocation with V3 first:

```bash
graph-engineering execution-plan \
  --spec SPEC-013-AGENT-RUNNER \
  --agent codex \
  --output engineering-graph/.execution/manifests/spec-013.json

graph-engineering execution-prepare \
  engineering-graph/.execution/manifests/spec-013.json \
  --task <TASK-ID>
```

## Start a local runner process

Use explicit argv while developing/testing:

```bash
graph-engineering runner-start <TASK-ID> \
  --stdin-handoff \
  --command python \
  --command -c \
  --command 'print("fixture")' \
  --json
```

For a real coding agent, provide the installed CLI argv explicitly or configure the agent command template locally. V5 deliberately does not shell-expand command strings.

## Inspect

```bash
graph-engineering runner-status --task <TASK-ID>
graph-engineering runner-status --json
```

## Read logs

```bash
graph-engineering runner-logs <TASK-ID> --stream stdout
graph-engineering runner-logs <TASK-ID> --stream stderr
```

## Stop

```bash
graph-engineering runner-stop <TASK-ID>
```

Force escalation is explicit:

```bash
graph-engineering runner-stop <TASK-ID> --force
```

Stopping a run does not release the V3 lease. Release remains explicit:

```bash
graph-engineering execution-release <TASK-ID>
```

## Authority reminder

A successful agent process means only `exitCode=0`. It does not mean the Spec Kit Task is complete and does not authorize automatic commit/push/PR/merge.
