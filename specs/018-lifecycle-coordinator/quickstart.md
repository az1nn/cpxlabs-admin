# Quickstart: Lifecycle Coordinator V10

## Inspect one Task

```bash
graph-engineering lifecycle-status \
  --task SPEC-018-LIFECYCLE-COORDINATOR:T008 \
  --json
```

The command is read-only. It may inspect existing local V3–V9 evidence and the published PR state, but it does not advance any lifecycle tier.

## Include Human Async Gates

```bash
graph-engineering lifecycle-status \
  --task SPEC-018-LIFECYCLE-COORDINATOR:T008 \
  --human-gates .execution/human-gates.json \
  --json
```

Human gate input is read-only. Required `PENDING`, `FAILED`, or stale gate evidence remains visible and blocking at the human/readiness boundary.

## Offline/local-only PR inspection

```bash
graph-engineering lifecycle-status \
  --task SPEC-018-LIFECYCLE-COORDINATOR:T008 \
  --no-pr-inspect \
  --json
```

If a V8 publication has opened a PR but live PR state is unavailable, V10 stops at `published` and returns `inspect_pr_state`; it does not guess merge state.

## Authority reminder

The returned `nextAction` is a recommendation constrained by evidence, not permission for V10 to perform that mutation. Run the owning V3–V9 command or obtain the required human/external decision separately.