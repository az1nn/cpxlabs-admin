# Requirements Checklist: Agent Validator V7

- [x] Validation command provenance is deterministic and cannot be overridden by the caller.
- [x] Active V3 allocation/revision/worktree identity is required.
- [x] Latest V5 execution must be `succeeded` and allocation-compatible.
- [x] V6 exact `runId` ownership is verified when supervisor evidence applies.
- [x] Validation commands are pre-tokenized and executed with `shell=False`.
- [x] First command failure stops later validation commands.
- [x] stdout/stderr are written to derived per-command logs.
- [x] Validation records are versioned and atomically persisted.
- [x] Workspace identity is fingerprinted before and after validation.
- [x] Workspace mutation prevents an overall `passed` result.
- [x] Validation evidence cannot mutate canonical Task state.
- [x] Validation evidence cannot release leases/remove worktrees.
- [x] Validation evidence cannot commit/push/open/review/merge PRs.
- [x] Runtime state remains outside Neo4j and application packages.
- [x] Unit/CLI coverage includes success, failure, ownership and mutation cases.
- [x] Implementation-candidate Spec Kit, Engineering Graph and Product CI all passed before convergence freeze.
