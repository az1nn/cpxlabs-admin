# Convergence: Agent Context Graph

**Feature**: `SPEC-010-AGENT-CONTEXT-GRAPH`  
**Date**: 2026-09-11  
**Status**: Final validation pending

## Conclusion

The V2 Agent Context Graph implementation is functionally converged. The feature now turns the V1 Engineering Graph into a deterministic operational context interface for Codex and Claude Code without changing the repository authority model or introducing autonomous execution.

The implementation delivers:

- portable deterministic `ContextPackage` JSON/Markdown;
- depth, node and byte budgets with explicit truncation accounting;
- provenance for every selected related entity;
- source-revision freshness validation with strict/non-strict modes;
- pure Codex and Claude Code adapters over the same package;
- explicit and READY-task batch generation with manifests;
- disposable regeneration semantics;
- CI coverage against ephemeral Neo4j;
- documentation/AGENTS workflow from task selection to canonical-file navigation.

No V3/V4 scope was pulled forward. Agent execution, worktree scheduling, GraphRAG, embeddings and semantic inference remain separate future features.

## Source-of-truth convergence

PASS. The feature preserves the invariant:

```text
Git / Markdown / code / tests / Git history
                  │
                  ▼
        deterministic graph projection
                  │
                  ▼
        bounded ContextPackage
                  │
          ┌───────┴────────┐
          ▼                ▼
      Codex handoff   Claude handoff
          │                │
          └───────┬────────┘
                  ▼
       canonical repository files
```

Generated packages and handoffs are navigation artifacts only. They never replace canonical source files and can be deleted/regenerated at any time.

## SC convergence matrix

| Criterion | Result | Evidence |
|---|---|---|
| SC-001 semantic reproducibility | PASS | `semantic_json()` plus repeated-generation unit/CI assertions |
| SC-002 complete linked task context | PASS | `agent-context.cypher` + portable package groups/provenance |
| SC-003 READY batch behavior | PASS | READY selector, explicit task mode, manifest tests and CI batch smoke |
| SC-004 strict freshness | PASS | package schema loader + current/stale/unknown freshness report + strict CLI behavior |
| SC-005 deterministic budgets | PASS | maxDepth/maxNodes/maxBytes enforcement, deterministic pruning and summary tests |
| SC-006 shared Codex/Claude package | PASS | pure adapter renderers consume `ContextPackage`; parity/adapter tests |
| SC-007 disposable outputs | PASS | task-directory replacement semantics + CI delete/regenerate smoke |
| SC-008 independent green gates | PRE-FREEZE PASS | pre-retarget V2 HEAD passed Engineering Graph, Spec Kit and product CI; final retargeted HEAD must rerun |
| SC-009 runtime independence | PASS | existing application dependency guard retained and V2 code remains under `engineering-graph/` |
| SC-010 documented full flow | PASS | AGENTS, README, architecture/development docs and Spec quickstart |

## Functional requirement convergence

`analysis.md` maps FR-001..FR-034 to implementation and verification evidence. No missing functional behavior was identified during the final review.

One process gap remained after implementation: `tasks.md` still reflected the early implementation state even though the branch contained the completed contract, validation, adapters, batch generation, docs and CI work. Convergence reconciles the Spec Kit task ledger with the implemented branch rather than inventing new scope.

## Validation evidence before retarget

The implementation HEAD `245f38561c9ddd98ab2a63b3b3e44e2f11df547b` passed all three independent GitHub Actions gates while stacked on the converged V1 head:

1. **Engineering Graph** — PASS
   - offline Python unit suite;
   - product dependency isolation guard;
   - ephemeral Neo4j readiness/schema/sync/validation;
   - V1 query smokes;
   - single portable context generation;
   - strict freshness validation;
   - Codex/Claude adapter smoke;
   - semantic reproducibility assertion;
   - READY batch generation;
   - delete/regenerate disposable-package smoke.
2. **Spec Kit** — PASS.
3. **Product CI** — PASS.

PR #15 is now merged and PR #16 has been retargeted to `master`. The remaining freeze condition is a green rerun on the reconciled final branch.

## Deferred by design

The following are intentionally not convergence gaps:

- embeddings/vector search;
- GraphRAG;
- LLM-inferred authoritative edges;
- autonomous agent spawning;
- worktree allocation/reservations;
- task scheduling/execution graph;
- autonomous commits, pushes or merges;
- canonical authoring into Neo4j.

These belong to later Graph Engineering roadmap stages and require new Spec Kit features and new PRs.

## Freeze state

Not frozen yet. T058 is satisfied by retargeting PR #16 to `master`. T059 remains open until Engineering Graph, Spec Kit and product CI are green on the final reconciled HEAD. After that, this document must be updated to `Converged`, T059 checked, and the PR marked Ready for Review.