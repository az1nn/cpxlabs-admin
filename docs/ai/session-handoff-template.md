# SESSION_HANDOFF

## Session Objective

Describe the single coherent objective of the session.

## Current State

- Repository:
- Base branch:
- Active branch:
- HEAD:
- Active PR(s):
- Active Spec Kit spec:
- Current milestone/phase:

## Final Decisions

List only decisions that remain valid for continuation.

## Superseded Decisions

List approaches, assumptions, branches, PRs, or design choices that must not be reused.

## Completed

Summarize completed work in outcome form. Prefer references to canonical files, commits, PRs, specs, ADRs, and tests over narrative history.

## Relevant Canonical Artifacts

- Specs:
- ADRs:
- Source paths:
- Tests:
- Other Git-backed evidence:

## Automated Validation Gates

Record automated validation gates and their latest known state. Include run IDs/URLs and the exact HEAD/build they validate. Do not claim a gate is current if repository state changed afterward.

## Human Async Gates

Use `docs/ai/human-async-gates.md`.

For each required gate:

```text
Gate ID:
Subject:
Trigger / evidence:
Expected observation:
Approver:
Status: PENDING | PASSED | FAILED | WAIVED
Rationale:
Freshness boundary:
Next action:
```

A required `PENDING` gate blocks final readiness/completion claims. WAIVED requires explicit human rationale.

## Open Items

List unresolved requirements, risks, review feedback, blocked tasks, deferred work, and unresolved gates.

## Freshness / Repository Notes

Record any repository state that a new chat must verify before trusting this handoff, especially branch movement, open PRs, CI, Human Async Gates, generated ContextPackages, or other derived evidence.

## Next Action

State one exact next action that can be executed without reconstructing the previous chat.

## Minimum Bootstrap Context

List the minimum files/commands the next chat must inspect before editing. Prefer bounded canonical context.

## Continuation Prompt

Write a ready-to-paste prompt that contains:

- repository/base/active branch/PR/HEAD;
- active Spec Kit scope;
- automated gate state;
- unresolved required Human Async Gates;
- one exact Next Action;
- freshness instruction;
- relevant authority boundary.

Example structure:

> Continue CPXLabs Admin in `az1nn/cpxlabs-admin`. First verify current `master`, active branch/PR and HEAD against this handoff. Active Spec: `<SPEC-ID>`. Automated gates: `<state>`. Human Async Gates: `<state>`. Treat Git-backed canonical files as authoritative and regenerate stale derived context. Next Action: `<one exact action>`. Do not cross the recorded merge/task/cleanup authority boundary without the required canonical or human evidence.
