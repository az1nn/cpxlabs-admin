# Convergence: Execution Graph

**Feature**: `SPEC-011-EXECUTION-GRAPH`  
**Date**: 2026-09-11  
**Status**: Final validation pending

## Conclusion

The V3 Execution Graph implementation is functionally converged. It composes the V1 deterministic task planner and V2 portable `ContextPackage` into a revision-bound local execution lifecycle with conflict-safe waves, isolated Git worktrees, fresh agent handoffs and derived local leases.

The implementation delivers:

- versioned deterministic `ExecutionManifest`;
- READY/BLOCKED/cycle/conflict/wave evidence from the existing V1 planner;
- semantic manifest reproducibility independent of generation timestamp;
- deterministic task branch/worktree naming;
- real Git worktree create/resume/remove boundary;
- dirty-worktree destructive-cleanup protection;
- versioned repository-scoped local lease registry;
- task/branch/path lease collision prevention;
- source-revision drift protection;
- strict V2 ContextPackage freshness per selected task;
- Codex/Claude handoff generation over the same package;
- dry-run preparation with no active lease/worktree mutation;
- plan/prepare/status/release CLI surfaces;
- Engineering Graph CI coverage against ephemeral Neo4j plus real temporary Git repositories.

No V4 scope was pulled forward. GraphRAG/embeddings/semantic inference, distributed scheduling, long-running agent supervision, automatic canonical task mutation and autonomous commit/push/PR/merge remain separate future features.

## Source-of-truth convergence

PASS.

```text
Git / Markdown / code / tests / Git history
                  │
                  ▼
        Engineering Graph projection
                  │
          ┌───────┴────────┐
          ▼                ▼
      V1 planner      V2 ContextPackage
          │                │
          └───────┬────────┘
                  ▼
          ExecutionManifest
                  │
                  ▼
        selected safe wave/task
                  │
                  ▼
       worktree + derived lease
                  │
                  ▼
          ExecutionAllocation
                  │
                  ▼
            agent handoff
                  │
                  ▼
        canonical repository edits
```

A lease means local allocation only. Canonical Task state still changes only through checked-in task Markdown followed by graph sync.

## SC convergence matrix

| Criterion | Result | Evidence |
|---|---|---|
| SC-001 deterministic manifests | PASS | unit semantic comparison + same-HEAD two-plan CI assertion |
| SC-002 V1 planner parity | PASS | V3 manifest is built directly from existing `ExecutionPlan` |
| SC-003 conflict-safe waves | PASS | existing planner tests + explicit CI conflict/wave assertion |
| SC-004 isolated worktrees | PASS | real temporary Git tests create/resume/remove one worktree per task |
| SC-005 lease collisions | PASS | duplicate task/branch/path lease tests |
| SC-006 revision drift | PASS | stale-manifest orchestrator test + runtime revision checks |
| SC-007 fresh context/handoff | PASS | strict V2 freshness in orchestrator + ephemeral-Neo4j V3 dry-run smoke |
| SC-008 safe release | PASS | real Git clean release and dirty worktree refusal/force tests |
| SC-009 CI layers | PRE-FREEZE PASS | validation anchor passed Engineering Graph and Spec Kit; final reconciled HEAD must repeat Engineering Graph + Spec Kit + Product CI |
| SC-010 runtime independence | PASS | application graph-dependency guard remains green |
| SC-011 documented lifecycle | PASS | quickstart, AGENTS, README, architecture and development guide |

## Validation anchor before closeout

Implementation/CI anchor `c2f5d0d97638a538f0edfe80278359e2b98ae024` passed:

### Engineering Graph — PASS

- installation and full offline Python suite;
- real temporary Git repository worktree integration tests;
- application runtime dependency guard;
- ephemeral Neo4j readiness/schema;
- full sync + logical stats + repeated sync idempotency;
- architecture validation;
- all V1/V2 fundamental query/context/freshness/adapter/reproducibility/disposability smokes;
- V3 `execution-plan` generation for `SPEC-011-EXECUTION-GRAPH`;
- V3 manifest semantic reproducibility;
- V3 conflict-safe wave assertion;
- V3 `execution-prepare --dry-run` against real ephemeral graph/context with proof that no active lease was written.

### Spec Kit — PASS

Spec Kit integration/status validation passed on the same validation anchor.

The final closeout adds CLI parser coverage and documentation/task-ledger reconciliation only. Product CI and all graph/spec gates must be green on the final reconciled HEAD before freeze.

## Analyze/converge findings resolved

### Dry-run allocation state

`planned` is now explicitly documented as a transient dry-run allocation status; it is not persisted as an active lease.

### Existing deterministic task work

The implementation/docs now distinguish safe resume from collision:

- exact expected path + exact expected task branch may resume without reset;
- expected branch checked out elsewhere fails;
- foreign filesystem path fails;
- existing branch history is never reset silently.

No new implementation task remains from these findings.

## Deferred by design

The following are intentionally not convergence gaps:

- GraphRAG, embeddings and vector search;
- LLM-inferred authoritative edges;
- distributed/multi-host leases or scheduler consensus;
- long-running coding-agent process supervision;
- automatic Task status mutation;
- automatic commit/push/PR creation/merge;
- automatic deletion of dirty user worktrees;
- product runtime integration.

## Freeze state

Not frozen yet. T001–T067 are implementation/convergence-complete after task-ledger reconciliation. T068 remains open until **Engineering Graph + Spec Kit + Product CI** are green on the final reconciled HEAD. Only then may PR #17 be marked Ready for Review.