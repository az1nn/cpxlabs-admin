# Analysis: Lifecycle Coordinator V10

## Authority analysis

V10 deliberately adds no authority-bearing transition. `lifecycle-status` composes canonical repository identity, existing V3–V9 derived artifacts, optional Human Async Gate evidence, and read-only PR inspection into one `LifecycleAssessment`. The returned `nextAction` names the owner of the next transition; V10 never executes that transition.

Canonical Task completion remains outside the V10 reducer. A merged PR is therefore only `merged`; the next action is V9 reconciliation, which independently proves base reachability and canonical Task completion before cleanup.

## Requirement-to-evidence map

| Requirements | Evidence |
| --- | --- |
| FR-001–FR-003 | `LifecycleEvidence`, `LifecycleAssessment`, versioned phase/action contract |
| FR-004–FR-005 | `LifecycleEvidence.to_dict()` separates `canonical`, `derived`, and `human`; reducer reports only proven phase |
| FR-006–FR-008 | stable blocker objects, closed `NEXT_ACTIONS`, identity conflict reducer path |
| FR-009–FR-013 | explicit tier-by-tier reducer; unit cases prove runner/validation/publication/merge do not imply later authority |
| FR-014–FR-017 | `HumanAsyncGate`, freshness validation, pending/failed/stale reducer paths, no gate mutation API |
| FR-018–FR-019 | `lifecycle_cli.py`; `runner_entry.py` routing |
| FR-020 | adapter uses read helpers and read-only `gh pr view`; tests assert argv + `shell=False` and unchanged gate input |
| FR-021–FR-022 | `build_continuation()` includes repository/base/branch/PR/HEAD/Spec/Task, automated state, unresolved gates, one action, freshness and authority text |
| FR-023–FR-025 | V10 adapter has no `GraphStore`/Neo4j dependency; product runtime imports remain prohibited; no lifecycle projection persistence |
| SC-001–SC-009 | `engineering-graph/tests/test_lifecycle.py` reducer, identity, human-gate, continuation and read-only coverage |
| SC-010 | verified only by closeout/freeze workflows on final HEAD |

## Decision table

| Strongest current proof | V10 phase | Next action |
| --- | --- | --- |
| no V3 allocation | `unallocated` | `prepare_execution` |
| active V3 allocation | `allocated` | `start_execution` |
| V5 running | `running` | `wait_for_execution` |
| V5 succeeded | `executed` | `run_validation` |
| V7 passed/stable | `validated` | `run_publication` |
| V8 partial publication | `published` | `resume_publication` |
| V8 PR opened, live state unknown | `published` | `inspect_pr_state` |
| PR open and required human evidence resolved | `awaiting_human` | `await_human_review` |
| required HAG pending/stale | `awaiting_human` | `await_human_gate` |
| required HAG failed | `blocked` | `remediate_human_gate` |
| PR merged | `merged` | `reconcile_post_publication` |
| V9 reconciled | `reconciled` | `finalize_post_publication` |
| V9 finalized | `finalized` | `none` |
| contradictory identity | `blocked` | `repair_evidence` |
| failed execution/validation/publication/cleanup | `blocked` | owning remediation action |

## Human Async Gate classification

Spec 018 does not intrinsically require a human/manual acceptance gate. Its behavior is deterministic control-plane classification and read-only I/O that can be asserted by unit/CLI/CI tests. Therefore the expected Spec 018 Human Async Gate set is **NONE** unless review later introduces a genuinely non-automatable acceptance condition.

This is a classification of applicability, not a self-pass or self-waiver of an existing gate.

## Residual risks

- Evidence schemas are intentionally coupled to V3–V9 contracts; future schema changes must update the V10 adapter/tests.
- Live GitHub state may be unavailable. V10 degrades to `inspect_pr_state` rather than guessing.
- Human gate freshness requires an explicit current-HEAD boundary; stale human evidence remains unresolved.
- The lifecycle assessment is derived and can become stale immediately after a repository, PR, runtime, or gate change. Continuation output therefore always requires freshness re-check.