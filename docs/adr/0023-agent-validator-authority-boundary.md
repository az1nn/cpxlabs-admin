# ADR-0023: Agent Validator Authority Boundary

**Status**: Accepted

## Context

V3 freezes task-specific validation commands into an active `ExecutionAllocation`. V5 records process lifecycle, and V6 may coordinate several V5 runs. Neither a successful V5 process nor a settled V6 job proves implementation correctness. Executing validations automatically adds subprocess authority and creates evidence that must not be confused with canonical Task state, review approval or Git publication authority.

## Decision

Introduce V7 Agent Validator as local engineering-only validation with these boundaries:

1. V7 validates one active V3 allocation at a time.
2. Validation commands come exclusively from the allocation's frozen `validationCommands`; callers cannot override or append commands.
3. Validation requires the latest V5 run for the task to be `succeeded` and identity-compatible with the allocation.
4. When a non-stopped V6 job owns the task, the supervisor's latest owned `runId` must equal the latest V5 run id and its observation must be `succeeded`.
5. Commands are tokenized with `shlex.split` and executed with `shell=False` from the allocation worktree.
6. Commands run sequentially and stop on first failure by default.
7. V7 persists versioned disposable records/logs only under `.execution/validation/`.
8. `passed` means only that every frozen validation command exited 0 for the recorded worktree/run identity.
9. Validation success does not mark a Spec Kit Task complete, approve review, release a lease, remove a worktree, alter Neo4j, or publish Git state.
10. Commit/push/PR/merge automation requires a separate future spec/ADR and must consume explicit validation evidence rather than inheriting V7 authority implicitly.

## Consequences

### Positive

- process completion and correctness evidence remain separate concepts;
- validation command provenance is deterministic and revision-bound;
- shell injection surface is avoided by refusing arbitrary commands and using `shell=False`;
- validation evidence is inspectable and disposable;
- future publication automation gets a narrow evidence contract without being embedded in validation.

### Trade-offs

- a new validation is required after code changes that invalidate prior evidence;
- leases remain explicitly managed after validation;
- publication remains a separate operator/future-tool step;
- commands requiring shell syntax are intentionally unsupported unless represented as executable argv-compatible commands upstream.

## Rejected alternatives

### Treat V5 exit code 0 as validation success

Rejected. Agent execution success does not prove typechecks/tests/builds succeeded.

### Let operators pass arbitrary `--command`

Rejected. Validation authority would no longer be tied to deterministic V3 planning evidence and would broaden injection/policy risk.

### Combine validation and Git publication in V7

Rejected. Publishing canonical Git history/PR state has materially greater authority and should be designed and reviewed independently.
