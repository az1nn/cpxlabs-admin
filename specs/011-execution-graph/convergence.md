# Convergence: Execution Graph

**Feature**: `SPEC-011-EXECUTION-GRAPH`  
**Date**: 2026-09-11  
**Status**: Converged

## Conclusion

The V3 Execution Graph is converged. It composes the V1 deterministic task planner and V2 portable `ContextPackage` into a revision-bound local execution lifecycle with conflict-safe waves, isolated Git worktrees, fresh agent handoffs and derived local leases.

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
| SC-007 fresh context/handoff | PASS | strict V2 freshness in orchestrator + canonical-path handoff test + ephemeral-Neo4j V3 dry-run smoke |
| SC-008 safe release | PASS | real Git clean release and dirty worktree refusal/force tests |
| SC-009 CI layers | PASS | Engineering Graph, Spec Kit and Product CI all passed on convergence anchor `dfdfbf24…` |
| SC-010 runtime independence | PASS | application graph-dependency guard remains green |
| SC-011 documented lifecycle | PASS | quickstart, AGENTS, README, architecture and development guide |

## Final convergence validation anchor

Reconciled implementation/head `dfdfbf240d1259badbc7073e009ecc911fc46d77` passed all independent gates before the documentation-only freeze closeout:

### Engineering Graph — PASS (run #171)

- full offline Python suite, including Execution Graph CLI tests;
- real temporary Git repository worktree integration tests;
- active lease collision / release tests;
- fresh ContextPackage + canonical-file handoff allocation test;
- application runtime dependency guard;
- ephemeral Neo4j readiness/schema;
- full sync + logical stats + repeated sync idempotency;
- architecture validation;
- all V1/V2 query/context/freshness/adapter/reproducibility/disposability smokes;
- V3 `execution-plan` generation for `SPEC-011-EXECUTION-GRAPH`;
- V3 manifest semantic reproducibility;
- V3 conflict-safe wave assertion;
- V3 `execution-prepare --dry-run` against real ephemeral graph/context with proof that no active lease was written.

### Spec Kit — PASS (run #279)

Spec Kit integration/status and historical artifact-shape gates passed.

### Product CI — PASS (run #558)

- PostgreSQL-backed migrations + seed;
- typecheck;
- tests;
- production build;
- Storybook component/accessibility tests;
- Playwright E2E.

The freeze closeout changes only `tasks.md` / `convergence.md`. Those documentation-only commits must repeat the same three independent gates before PR #17 is marked Ready for Review.

## Analyze/converge findings resolved

### Dry-run allocation state

`planned` is explicitly documented as a transient dry-run allocation status; it is not persisted as an active lease.

### Existing deterministic task work

The implementation/docs distinguish safe resume from collision:

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

`SPEC-011-EXECUTION-GRAPH` is converged and T001–T068 are complete. The branch is a freeze candidate. After the documentation-only closeout HEAD repeats **Engineering Graph + Spec Kit + Product CI** successfully, PR #17 may be marked Ready for Review. Any V4 work must start in a new Spec Kit feature branch and a new PR rather than expanding this frozen scope.