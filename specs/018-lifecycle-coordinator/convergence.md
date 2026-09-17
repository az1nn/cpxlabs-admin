# Convergence: Lifecycle Coordinator V10

## Scope convergence

Implementation remains within the Spec 018 authority boundary:

- one read-only lifecycle projection;
- one closed phase vocabulary;
- one closed next-action vocabulary;
- stable blocker codes;
- provenance-separated canonical/derived/human evidence;
- read-only V3–V9 artifact adapters;
- optional read-only GitHub PR inspection;
- explicit Human Async Gate handling;
- freshness-bound continuation payload;
- no new lifecycle persistence or Neo4j authority.

No merge, Task-completion, lease/worktree, process, validation, publication or Human Async Gate mutation authority was added to V10.

## Implementation evidence

- `engineering-graph/src/engineering_graph/lifecycle.py`
- `engineering-graph/src/engineering_graph/lifecycle_cli.py`
- `engineering-graph/src/engineering_graph/runner_entry.py`
- `engineering-graph/tests/test_lifecycle.py`
- `docs/architecture/LIFECYCLE_COORDINATOR.md`
- `engineering-graph/README.md`
- `engineering-graph/AGENTS.md`
- ADR-0026

## Safety convergence

The reducer stops at the strongest tier actually proven. In particular:

- V5 success -> V7 still required;
- V7 success -> V8 still required;
- V8 PR opened -> live/human merge evidence still required;
- merge -> V9 canonical Task reconciliation still required;
- V9 reconciliation -> explicit V9 finalization still required;
- required unresolved Human Async Gates remain visible and blocking;
- contradictory cross-artifact identity returns `blocked / repair_evidence`.

`lifecycle-status` calls no save/release/remove/start/stop/validate/publish/merge function. Live GitHub inspection uses `gh pr view` only, argv execution, `shell=False`.

## Human Async Gates

**Spec 018 Human Async Gates: NONE.**

Rationale: V10 is deterministic control-plane classification plus read-only I/O. Its acceptance criteria are synchronously testable through unit/CLI/CI evidence. No manual visual/device/production/external-propagation observation is required by the spec.

This does not pass or waive any gate; it records that no separate Human Async Gate is required for this feature.

## Automated closeout

Candidate/final workflow evidence is intentionally populated by the task ledger and Caveman handoff after GitHub Actions completes. Final freeze requires all three workflows green on one exact final HEAD:

- Spec Kit;
- Engineering Graph;
- Product CI.

Any content commit after a candidate run invalidates that candidate for final freeze and requires the same three gates again.

## Convergence status

Implementation/spec/authority convergence is complete. Automated regression/freeze convergence remains pending until the three required workflows are green on the exact ledger/freeze HEAD.