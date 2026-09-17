# ADR-0026: Lifecycle Projection Authority Boundary

**Status**: Accepted

## Context

V3 through V9 intentionally separate allocation, execution, supervision, validation, publication, human merge and post-publication cleanup into distinct authority tiers. This prevents a successful lower tier from silently granting authority to a later tier.

After V9, the missing operator capability is a unified answer to “what is proven now?” and “what is the next permitted action?” Today that requires manually correlating canonical Spec Kit state, leases, runner/supervisor evidence, validation records, publication records, PR/human state, post-publication receipts and Human Async Gates.

A naive solution would persist a new lifecycle state machine or add a coordinator that advances those tiers automatically. Both approaches would weaken the existing authority model by either duplicating canonical truth or silently aggregating mutation authority.

## Decision

1. Introduce V10 as a read-only lifecycle projection/coordinator.
2. V10 computes lifecycle status on demand from canonical Git/Spec Kit evidence plus existing derived V3–V9 evidence and explicitly supplied Human Async Gate evidence.
3. V10 owns no mutation authority: it cannot acquire/release leases, create/remove worktrees, start/stop agents, run validation, publish Git state, approve/merge/close PRs, edit canonical Tasks, or change Human Async Gate status.
4. V10 must preserve evidence provenance. Canonical Git/Spec Kit evidence, human/external evidence and derived runtime/publication evidence remain distinguishable in the assessment.
5. Later-tier evidence never backfills missing authority in an earlier tier. Runner success does not imply validation; validation does not imply publication; publication does not imply merge; merge does not imply canonical Task completion; reconciliation does not create canonical completion.
6. Contradictory repository/Spec/Task/branch/worktree/run/publication identity fails closed into a blocked assessment.
7. The assessment exposes one versioned phase, zero or more stable blocker codes and exactly one next action from a closed vocabulary.
8. Required `PENDING`, `FAILED`, or stale Human Async Gate evidence blocks readiness according to the human-gate policy. V10 never self-passes or self-waives a gate.
9. V10 may render a continuation payload, but that payload is derived, freshness-bound context and never overrides Git or current external state.
10. V10 status is computed read-only and is not projected into Neo4j as canonical lifecycle truth.

## Consequences

### Positive

- operators and agents can reason about the full lifecycle from one deterministic projection;
- no new destructive or Git mutation authority is introduced;
- authority gaps remain visible instead of being silently inferred;
- continuation prompts can be generated from structured evidence rather than narrative memory;
- the projection remains recoverable from Git plus disposable local evidence;
- testing the lifecycle decision table is possible without invoking subprocess/GitHub mutations.

### Trade-offs

- V10 cannot “fix” a blocked lifecycle; the reported next action must be executed by the owning subsystem or human authority;
- some evidence remains external/local and may be absent or stale;
- the coordinator must evolve when V3–V9 schemas evolve;
- a single status view does not eliminate the need to inspect detailed subsystem evidence during remediation.

## Rejected alternatives

### Persist a new canonical lifecycle state machine

Rejected because it would duplicate Git/Spec Kit and V3–V9 evidence, creating a second source of truth and recovery/drift problems.

### Let the coordinator automatically execute the next action

Rejected because it would aggregate mutation authority across tiers and make a read/status command capable of changing repository/process state.

### Infer missing phases from later evidence

Rejected because it collapses the explicit authority boundaries established by V3–V9.

### Use Neo4j as lifecycle authority

Rejected because the Engineering Graph is a rebuildable derived projection and must remain non-canonical.