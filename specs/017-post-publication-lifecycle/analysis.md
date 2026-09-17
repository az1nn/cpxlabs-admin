# Analysis: Post-Publication Lifecycle V9

**Feature**: `SPEC-017-POST-PUBLICATION-LIFECYCLE`  
**Status**: Implementation coverage analyzed; final freeze gates pending

## Result

No authority inversion was found. V9 reconciles post-merge evidence and explicit cleanup only; it does not gain PR merge authority or canonical Task mutation authority.

## Functional requirement coverage

| Requirement | Evidence |
|---|---|
| FR-001–FR-002 | `post_publication.py` loads one terminal V8 `PublicationRecord`, validates repository identity, and checks the matching active V3 lease/publication identity before first cleanup. |
| FR-003–FR-005 | `_inspect_pr` uses explicit `gh pr view ... --json ...` argv through `_run_command(shell=False)`; reconciliation requires merged state/merge SHA and `_merge_reachable` proves ancestry. |
| FR-006 | `_refresh_base` fetches the configured base into `refs/remotes/origin/<base>` before canonical evaluation. |
| FR-007–FR-009 | `_task_path` + `_canonical_task_completed` read `tasks.md` from the refreshed base using `git show`, require one exact Task entry, and never edit the checkbox. |
| FR-010 | `post-publication-status` calls read-only reconciliation and performs no lease/worktree mutation. |
| FR-011–FR-013 | `post-publication-finalize` requires explicit `--release-lease`; removal additionally requires `--remove-worktree`; dirty worktree removal fails closed with no force path. |
| FR-014–FR-016 | Versioned `PostPublicationReceipt` is persisted atomically below `.execution/post-publication/`; receipt phase state makes release/removal retries idempotent. |
| FR-017–FR-018 | `post_publication_cli.py` exposes status/finalize JSON/human surfaces through `runner_entry.py`. |
| FR-019–FR-020 | Existing runtime-isolation gate remains green; V9 adds no application import or Neo4j write path. |
| FR-021–FR-024 | `docs/ai/chatgpt-project-instructions.md`, `context-handoff.md`, `session-handoff-template.md`, `continuation-prompt-template.md`, and the Engineering Graph `AGENTS.md` overlay require fresh Continuation Prompts and define their payload/freshness rules. |
| FR-025–FR-031 | `docs/ai/human-async-gates.md`, Project Instructions, handoff/template and Engineering Graph agent rules define Human Async Gate schema/status/freshness, separate them from CI, block readiness on required `PENDING`, and prohibit agent self-pass/self-waive. |

## Success criteria coverage

| Criterion | Evidence |
|---|---|
| SC-001 | Reconciliation/finalization requires merged/reachable PR plus pre-existing checked canonical Task; no Task mutation API exists in V9. |
| SC-002 | `test_open_pr_blocks_finalization`. |
| SC-003 | `test_incomplete_canonical_task_blocks_cleanup`; continuation policy documents exact follow-up rather than implicit completion. |
| SC-004 | `_merge_reachable` + `test_merge_reachability_is_fail_closed`. |
| SC-005 | Finalize path uses the existing exact-task `release_lease` and optional matching `remove_worktree`. |
| SC-006 | `test_dirty_worktree_is_never_force_removed`. |
| SC-007 | basic finalize idempotency plus `test_retry_can_remove_worktree_after_lease_was_already_released`; unrelated allocations are untouched because V9 addresses only the publication Task/worktree. |
| SC-008 | Project Instructions + handoff policy/template + dedicated Continuation Prompt template. |
| SC-009 | Human Async Gate policy explicitly prevents CI/manual evidence conflation. |
| SC-010 | Final Spec Kit + Engineering Graph + Product CI same-HEAD freeze still pending. |

## Safety review

### Merge authority

PASS structurally. V9 calls `gh pr view`; it has no merge/approve/close/auto-merge operation.

### Canonical Task authority

PASS structurally. Task state is read from the refreshed merged base. A missing/ambiguous/unchecked Task blocks cleanup. No V9 code edits `tasks.md`.

### Git command safety

PASS. Commands are argv arrays, `shell=False`, `check=False`; failure interpretation is explicit. Base branch input is restricted before constructing fetch refs.

### Dirty worktree safety

PASS. V9 deliberately has no force option. Dirty worktree cleanup persists a blocked receipt and returns an error.

### Partial-finalization recovery

PASS after a CI-discovered edge-case fix. Engineering Graph #370 exposed that a receipt with `leaseReleased=true` could not resume a previously blocked worktree cleanup because reconciliation still demanded an active lease. The core now treats prior lease release as authorization for only that already-completed phase while continuing to revalidate PR merge, merge reachability and canonical Task evidence. The dedicated retry test passes at the corrected implementation anchor.

### Human Async Gates

PASS as policy. Automated async CI is represented as an automated pending gate. Human Async Gates are created only for genuinely human/external acceptance; required `PENDING` gates block readiness/completion and cannot be self-approved/waived by the agent.

## Implementation anchor

Corrected lifecycle implementation anchor:

`5da98ef88e0adba778de261a1d6cdbd4b6da3467`

Engineering Graph #372 passed on that anchor, including:

- complete Python offline unit/integration suite with V9 retry coverage;
- application-runtime dependency isolation;
- Neo4j schema/sync/idempotency/validation;
- V1–V4 graph/context/execution/GraphRAG gates;
- existing V5–V8 regression tests in the offline suite.

Later commits are documentation/policy convergence and therefore require a fresh final three-domain freeze.

## Human gate assessment for Spec 017

No required Human Async Gate is currently necessary for this tooling-only change. The feature is deterministically covered by repository tests/CI and does not require a deployment/device/manual acceptance observation. Therefore final freeze is gated by automated Spec Kit + Engineering Graph + Product CI only.

If review later adds a manual acceptance requirement, it must be recorded as a Human Async Gate and T054 must remain blocked while that gate is `PENDING`.
