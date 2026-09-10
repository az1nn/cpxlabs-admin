# Convergence: Graph Engineering Control Plane

**Feature**: `SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE`  
**Date**: 2026-09-10  
**Status**: Pending final post-convergence gates

## Conclusion

The deterministic Engineering Graph control plane satisfies the intended feature scope after one convergence gap was identified and corrected: SC-004 required `drift` to execute as one of the five fundamental query surfaces, while the first implementation exposed drift evidence only indirectly through the validator. The convergence fix adds `graph-engineering drift` and executes it explicitly in the Neo4j CI smoke suite.

No other material implementation gap was found. V2/V3/V4 extensions remain future feature work and must use new Spec Kit specs/branches/MRs rather than expanding this PR.

## Source-of-truth convergence

PASS. The implementation preserves the foundational invariant:

```text
Git / Markdown / code / tests / Git history
                  │
                  ▼
        deterministic extraction
                  │
                  ▼
          validated GraphModel
                  │
                  ▼
                Neo4j
        rebuildable projection
```

Evidence:

- Constitution v1.1.0 makes Git authority and graph disposability non-negotiable.
- ADR-0017 records the control-plane boundary.
- `AGENTS.md` requires agents to follow graph-returned paths back to canonical files before editing.
- application packages are checked in CI for Neo4j/`engineering_graph` dependencies.
- reset + rebuild are documented and tested through ephemeral CI reconstruction.

## SC convergence matrix

| Criterion | Result | Evidence |
|---|---|---|
| SC-001 repeated sync is logically idempotent | PASS | extraction logical-signature test and two CI syncs with identical stats |
| SC-002 seven labels/eight relationships versioned | PASS | YAML schema, schema tests, Neo4j constraints/index initialization |
| SC-003 Spec/FR/SC/Task/ADR/code/test/PR extraction | PASS | parser/extractor fixtures plus GitHub PR event ingestion in CI |
| SC-004 impact/ready/conflicts/drift/context execute | PASS after convergence fix | first-class CLI commands and explicit Neo4j smoke calls for all five |
| SC-005 deterministic DAG/cycle/conflict-free waves | PASS | planner unit tests and `waves` Neo4j smoke |
| SC-006 bounded Markdown/JSON context packages | PASS | Context Builder tests, configured budget, CI JSON context smoke |
| SC-007 validator error/warning behavior | PASS | validator fixtures cover error/warning/off/cycle; clean repository validation passes |
| SC-008 ephemeral CI graph rebuild | PASS | `neo4j:2026.07.1` service, schema init, full sync, no persistent external graph |
| SC-009 existing product + Spec Kit gates remain authoritative | PASS | independent CI workflows; product quality/browser and Spec Kit green before convergence |
| SC-010 delete/rebuild + runtime independence documented | PASS | README/development/architecture docs and product dependency guard |

## Functional requirement convergence

`analysis.md` maps FR-001..FR-034 to implementation/tasks. Final convergence found no missing functional behavior beyond the SC-004 CLI/smoke gap described above. The fix does not expand the schema, data model or architecture boundary.

## Real Neo4j validation

Before this convergence document was created, the Engineering Graph workflow completed successfully against a real ephemeral Neo4j 2026.07.1 service, including:

- Python package installation;
- offline unit suite;
- application dependency isolation check;
- Neo4j readiness;
- versioned schema initialization;
- full repository sync;
- second full sync/idempotency stats comparison;
- graph validation;
- impact/ready/conflicts/context/waves/stats smoke queries.

The final post-convergence run additionally must prove the new `drift` command against Neo4j before PR freeze.

## Deferred by design

The following are intentionally not convergence gaps because the feature spec marks them as non-goals/future evolution:

- AST-wide semantic dependency inference;
- embeddings/vector indexes;
- GraphRAG;
- AI-authored authoritative relationships;
- distributed scheduler;
- autonomous merging;
- direct canonical authoring into Neo4j.

Those correspond to later Graph Engineering roadmap stages and require separate MRs.

## Freeze rule

The feature becomes `Converged` only when the final HEAD containing this document, the explicit drift CLI/smoke fix and task reconciliation passes all three independent gates:

1. Engineering Graph / Neo4j;
2. Spec Kit;
3. existing product CI (`quality` + `browser-tests`).

Until then T071 remains open and PR #15 remains draft.
