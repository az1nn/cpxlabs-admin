# Lifecycle Assessment Contract V1

## Input identity

Every assessment is anchored by:

- `repository`
- `taskId`
- `specId`
- current repository `headSha`

Existing V3–V9 artifacts may additionally provide `sourceRevision`, `branch`, `worktreePath`, `runId`, `validationId`, `publicationId`, PR identity and post-publication receipt identity.

All overlapping identity fields must agree. Contradiction produces `phase=blocked` and `nextAction=repair_evidence`.

## Phases

Closed V1 vocabulary:

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

A later phase is reported only when the evidence owned by that tier exists and is valid.

## Next actions

Closed V1 vocabulary:

- `prepare_execution`
- `start_execution`
- `wait_for_execution`
- `repair_execution`
- `run_validation`
- `repair_validation`
- `run_publication`
- `resume_publication`
- `inspect_pr_state`
- `await_human_review`
- `await_human_gate`
- `remediate_human_gate`
- `reconcile_post_publication`
- `finalize_post_publication`
- `repair_cleanup`
- `repair_evidence`
- `none`

Exactly one action is returned.

## Stable blocker codes

V1 defines:

- `identity_conflict`
- `runner_failed`
- `supervisor_exhausted`
- `validation_failed`
- `publication_failed`
- `pr_state_unavailable`
- `human_gate_pending`
- `human_gate_failed`
- `human_gate_stale`
- `post_publication_blocked`

A blocker contains a stable code plus human-readable detail.

## Human Async Gate input

Optional JSON evidence is an array of objects using the repository policy fields:

```json
[
  {
    "gateId": "HAG-001",
    "subject": "preview smoke",
    "triggerEvidence": "preview deployment 123",
    "expectedObservation": "critical journey succeeds",
    "approver": "repository owner",
    "status": "PENDING",
    "rationale": null,
    "freshnessBoundary": "HEAD abc123",
    "nextAction": "record the smoke result",
    "required": true
  }
]
```

`required` defaults to `true`. A required PASSED/WAIVED gate is fresh only when the current assessment `headSha` is represented in `freshnessBoundary`. A required gate that is PENDING, FAILED, or stale cannot support a final readiness/completion claim. V10 never writes this file or changes a gate status.

## Output

```json
{
  "assessmentVersion": "1",
  "repository": "owner/repo",
  "taskId": "SPEC-018-LIFECYCLE-COORDINATOR:T001",
  "specId": "SPEC-018-LIFECYCLE-COORDINATOR",
  "headSha": "...",
  "phase": "validated",
  "nextAction": "run_publication",
  "blockers": [],
  "evidence": {},
  "humanAsyncGates": [],
  "continuation": {
    "repository": "owner/repo",
    "baseBranch": "master",
    "branch": "...",
    "prUrl": null,
    "headSha": "...",
    "specId": "SPEC-018-LIFECYCLE-COORDINATOR",
    "taskId": "...",
    "automatedState": {},
    "unresolvedHumanAsyncGates": [],
    "nextAction": "run_publication",
    "freshnessInstruction": "Re-check repository HEAD, PR and gate evidence before acting; Git/current external state wins over this derived payload.",
    "authorityBoundary": "V10 is read-only projection; execute the next action only through its owning subsystem/human authority."
  }
}
```

The assessment and continuation payload are derived operational context, not canonical project truth.