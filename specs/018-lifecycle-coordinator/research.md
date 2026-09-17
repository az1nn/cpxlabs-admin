# Research: Lifecycle Coordinator V10

## Problem

After V9, the execution pipeline has explicit authority tiers and durable/derived evidence for allocation, execution, supervision, validation, publication and post-publication cleanup. The safety model is strong, but an operator still has to inspect several commands/files and mentally decide what is proven and what action is allowed next.

That manual stitching is now the natural boundary to address. The missing capability is not another mutation tier; it is a deterministic read-only projection over the tiers that already exist.

## Existing authority tiers

- V3 owns allocation/worktree/lease preparation.
- V5 owns one agent process execution record.
- V6 owns bounded supervision/retry orchestration.
- V7 validates the exact current publishable workspace.
- V8 publishes an exact validated workspace and opens/reuses one PR.
- Human/external authority owns review/merge and Human Async Gate decisions.
- V9 reconciles merge + canonical Task completion and performs only explicitly requested cleanup.
- Git/Spec Kit remains canonical project/task truth throughout.

## Boundary selected

Introduce V10 as a read-only lifecycle coordinator.

V10 may:

- read canonical Git/Spec Kit state;
- read existing `.execution/` registries/records/receipts;
- read Human Async Gate declarations supplied to the projection;
- validate cross-artifact identity and freshness;
- compute the furthest proven phase;
- expose blockers;
- select one next action from a closed vocabulary;
- render a continuation payload.

V10 may not:

- acquire/release leases;
- create/remove worktrees;
- launch/stop processes;
- run validation;
- commit/push/open/merge/close PRs;
- mark Tasks complete;
- mutate Human Async Gate status;
- write lifecycle state back into Neo4j or another canonical store.

## Why not remote branch cleanup next

V9 intentionally leaves remote branch deletion out of scope. Adding it immediately would introduce new destructive Git authority. The system still lacks a unified way to explain whether cleanup is even permitted. A read-only coordinator improves safety and operator UX without silently expanding authority.

## Why not make V10 a persisted state machine

Persisting a new lifecycle state machine would duplicate the truth already represented by canonical Git plus V3–V9 evidence and would create drift/recovery problems. V10 therefore computes an assessment on demand and treats all output as derived/freshness-bound.

## Evidence precedence

1. Canonical Git/Spec Kit evidence is authoritative for project/task state.
2. Human Async Gate evidence is authoritative only for the explicitly recorded human/external observation and freshness boundary.
3. V3–V9 runtime/publication/cleanup evidence is derived and only proves its own tier.
4. Later derived evidence does not retroactively prove missing earlier/canonical evidence.
5. Contradictory identity/freshness fails closed.

## Human Async Gates

A required `PENDING` gate blocks final readiness. A `FAILED` gate requires remediation/retest. `PASSED` and `WAIVED` are accepted only when already recorded by human/external authority and fresh for the assessment boundary. V10 never changes gate status.

## Continuation contract

The projection should make the continuation prompt mechanical instead of narrative reconstruction. It will expose a structured continuation payload with repository/base/branch/PR/HEAD/spec, automated evidence summary, unresolved human gates, exactly one next action, freshness instruction and the active authority boundary.

## Compatibility

The coordinator is local/read-only and remains outside product runtime. Neo4j is not required to compute the projection. Existing commands and artifact schemas remain authoritative; V10 composes rather than replaces them.