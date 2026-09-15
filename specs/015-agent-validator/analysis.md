# Analysis: Agent Validator V7

## Conformance summary

The implementation preserves the V3/V5/V6 authority boundaries instead of expanding them implicitly. V3 remains the source of frozen validation commands and allocation identity; V5 remains the source of process lifecycle observations; V6 remains orchestration-only. V7 consumes those derived contracts and produces new derived validation evidence only.

## Requirement-to-implementation review

- Command provenance is enforced by `run_validation` reading only `ExecutionAllocation.validation_commands`; the CLI exposes no arbitrary command argument.
- Allocation freshness/worktree registration reuse V5 `validate_allocation_for_run` instead of introducing a conflicting validation path.
- V5 is reconciled before the latest run is selected; only `succeeded` is accepted.
- Run/allocation repository, task, spec, revision, branch and worktree identities are compared explicitly.
- V6 evidence is inspected fail-closed for active ownership and exact `runId` correspondence.
- Every frozen command is tokenized before any command starts, then executed sequentially with `shell=False` and cwd fixed to the allocated worktree.
- stdout/stderr are stored as files and the record stores bounded metadata/log paths.
- A non-zero exit or process launch error stops later commands and yields `failed`.
- Workspace revision plus a deterministic fingerprint of tracked diff/non-ignored untracked content is measured before/after. Drift prevents `passed` even when command exit codes are zero.
- No validation function mutates Spec Kit artifacts, V3 lease state, worktree registration, Git history, provider state or Neo4j.

## Implementation divergence discovered during review

The initial V7 spec required successful frozen commands but did not explicitly state that validation evidence must be invalidated when a gate mutates the publishable workspace. The implementation review identified this as a future publication TOCTOU risk. The final spec/plan/ADR therefore add stable workspace identity as FR-025/FR-026 and SC-011 rather than leaving the stronger implementation undocumented.

## Test evidence

`engineering-graph/tests/test_validation.py` covers successful multi-command execution, stop-on-first-failure, unsuccessful V5 rejection, V6 ownership mismatch and workspace mutation invalidation. `engineering-graph/tests/test_validation_cli.py` covers parser/routing and the absence of a validation command override.

The implementation candidate `40b326795126ab30696c9633157b61f3a3d01fde` passed:

- Spec Kit #387;
- Engineering Graph #320, including the full offline unit/Git worktree suite and graph validation workflow;
- Product CI #722, including typecheck, tests, build, Storybook/component accessibility and Playwright E2E.

## Residual risks

Validation records are local derived evidence and are not cryptographically signed. A future publication layer must re-check the current workspace identity against the selected V7 record immediately before publication and must define its own provider/Git authority policy in a separate spec/ADR.

Commands that intentionally rewrite tracked or non-ignored untracked files cannot themselves produce final `passed` evidence; the operator/agent must accept those changes and run validation again. This is fail-closed by design.
