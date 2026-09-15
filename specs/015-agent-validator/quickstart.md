# Quickstart: Agent Validator V7

V7 assumes V3 has already prepared an active allocation and V5/V6 has produced the successful execution evidence for the same task.

```bash
cd engineering-graph

graph-engineering execution-status --json
graph-engineering runner-status --task <TASK-ID> --json
graph-engineering validation-run <TASK-ID> --json
graph-engineering validation-status --task <TASK-ID> --json
```

Interpretation rules:

- `validation-run` executes only the active allocation's frozen `validationCommands`;
- there is deliberately no `--command` override;
- a `passed` result means the frozen commands passed against one stable workspace identity;
- it does not mean the Spec Kit Task is complete or reviewed;
- it does not release the allocation or modify Git/provider state;
- after any publishable workspace change, run validation again before relying on the evidence.

For architecture and authority details, see `docs/architecture/AGENT_VALIDATOR.md` and ADR-0023.
