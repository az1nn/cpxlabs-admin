# Feature Specification: Lifecycle Coordinator V10

**Feature ID**: `SPEC-018-LIFECYCLE-COORDINATOR`

## Objective

Provide one deterministic, read-only lifecycle projection across the existing Engineering Graph execution pipeline so an operator or agent can answer two questions without manually stitching together V3–V9 artifacts:

1. what lifecycle state is this Task currently in?
2. what is the one next action permitted by the current evidence and authority boundary?

V10 is coordination/projection infrastructure only. It consumes canonical Git evidence plus the existing derived execution, validation, publication, post-publication and Human Async Gate evidence. It must never mutate canonical Task state, approve/merge a pull request, release a lease, remove a worktree, publish Git state, self-pass/self-waive a Human Async Gate, or turn derived evidence into canonical truth.

## Authority model

```text
canonical Git / Spec Kit
         |
         v
V3 allocation + lease
         |
V5 runner -> V6 supervisor -> V7 validator -> V8 publisher
                                                |
                                         human review / merge
                                                |
                                         V9 reconciliation
                                                |
                   Human Async Gate evidence ---+
                                                |
                                                v
                                  V10 lifecycle projection
                                  |- current phase
                                  |- blockers
                                  |- evidence summary
                                  |- exactly one next action
                                  `- continuation payload
```

V10 observes; it does not advance authority-bearing state.

## Functional requirements

- **FR-001** V10 MUST produce a versioned lifecycle assessment for one repository/Spec/Task identity.
- **FR-002** The assessment MUST be deterministic for the same evidence set.
- **FR-003** The assessment MUST preserve repository, Spec, Task, branch/worktree and relevant run/publication identity when those artifacts exist.
- **FR-004** V10 MUST distinguish canonical evidence from derived evidence in its output.
- **FR-005** V10 MUST expose the furthest lifecycle phase proven by current evidence without inferring later phases.
- **FR-006** V10 MUST emit zero or more machine-readable blockers and exactly one machine-readable next action.
- **FR-007** The next action MUST be selected from a closed, versioned action vocabulary.
- **FR-008** Missing or contradictory identity evidence MUST fail closed into a blocked assessment rather than being guessed or normalized away.
- **FR-009** Runner success MUST NOT imply validation success, publication success, PR merge, canonical Task completion, or cleanup completion.
- **FR-010** Validation success MUST NOT imply publication, merge, canonical Task completion, or cleanup completion.
- **FR-011** Publication success MUST NOT imply merge, canonical Task completion, or cleanup completion.
- **FR-012** PR merge evidence MUST NOT imply canonical Task completion.
- **FR-013** V9 reconciliation/finalization evidence MUST NOT be rewritten by V10.
- **FR-014** Required Human Async Gates with `PENDING` status MUST block readiness/completion claims and be surfaced as blockers.
- **FR-015** `FAILED` Human Async Gates MUST produce a remediation/retest next action rather than readiness.
- **FR-016** V10 MUST never mark a Human Async Gate `PASSED` or `WAIVED`.
- **FR-017** Stale Human Async Gate evidence MUST NOT be treated as current proof.
- **FR-018** V10 MUST support JSON output suitable for agents and a concise human-readable status.
- **FR-019** V10 MUST be available through the standard `graph-engineering` entrypoint.
- **FR-020** The status operation MUST be read-only with respect to Git, `.execution/`, worktrees, leases, GitHub state, Neo4j and product runtime state.
- **FR-021** V10 MUST generate a continuation payload containing repository, base, branch, PR when known, HEAD/evidence freshness, active Spec, automated gate summary, unresolved Human Async Gates, exact next action and authority boundary.
- **FR-022** A continuation payload is derived context and MUST explicitly instruct the next agent to re-check freshness before acting.
- **FR-023** The lifecycle projection MUST remain usable without Neo4j when the required Git/derived files are locally available.
- **FR-024** V10 MUST preserve V1–V9 product/runtime isolation.
- **FR-025** Lifecycle assessments MUST NOT be projected into Neo4j as canonical task truth.

## Lifecycle semantics

The first implementation MUST cover these phases without collapsing them:

- `unallocated`
- `allocated`
- `running`
- `executed`
- `validated`
- `published`
- `awaiting_human`
- `merged`
- `reconciled`
- `finalized`
- `blocked`

The exact external action vocabulary is defined by the technical contract, but it must keep mutation-bearing actions explicit (for example: run, validate, publish, wait for human gate/review, reconcile, finalize, repair evidence, or stop because the canonical Task is already complete).

## Success criteria

- **SC-001** One command can summarize a Task whose lifecycle evidence spans V3–V9 without mutating any source.
- **SC-002** Conflicting repository/Task/branch/run/publication identities produce `blocked` with concrete reasons.
- **SC-003** Each intermediate state returns one next action and does not skip authority tiers.
- **SC-004** A required `PENDING` Human Async Gate is visible and blocks final-readiness claims even when automated evidence is green.
- **SC-005** A failed human gate routes to remediation/retest.
- **SC-006** A merged PR with an incomplete canonical Task is not reported as completed/finalized.
- **SC-007** A finalized V9 receipt can be represented as final lifecycle evidence without V10 changing any canonical file or cleanup state.
- **SC-008** Continuation output is immediately reusable but declares itself derived and freshness-bound.
- **SC-009** Unit/CLI regression tests prove the status path performs no mutation.
- **SC-010** Spec Kit, Engineering Graph and Product CI remain green on the final freeze HEAD.

## Out of scope

- automatic PR approval, merge, close or auto-merge;
- editing Spec Kit Task checkboxes;
- acquiring/releasing leases;
- creating/removing worktrees;
- starting/stopping runner processes;
- running validation commands;
- committing/pushing/opening PRs;
- deleting local or remote branches;
- deployment/release automation;
- self-approval or self-waiver of Human Async Gates;
- replacing V3–V9 storage/contracts with a new canonical state machine;
- using Neo4j as lifecycle authority.