# Convergence: Graph Engineering Control Plane

**Feature**: `SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE`  
**Date**: 2026-09-10  
**Status**: Converged

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
| SC-009 existing product + Spec Kit gates remain authoritative | PASS | independent CI workflows; product quality/browser and Spec Kit green on the converged HEAD |
| SC-010 delete/rebuild + runtime independence documented | PASS | README/development/architecture docs and product dependency guard |

## Functional requirement convergence

`analysis.md` maps FR-001..FR-034 to implementation/tasks. Final convergence found no missing functional behavior beyond the SC-004 CLI/smoke gap described above. The fix does not expand the schema, data model or architecture boundary.

## Final validation evidence

The final converged HEAD passed all three independent gates:

1. **Engineering Graph / Neo4j** — PASS
   - Python package installation;
   - offline unit suite;
   - application dependency isolation check;
   - Neo4j readiness;
   - versioned schema initialization;
   - full repository sync;
   - second full sync/idempotency stats comparison;
   - graph validation;
   - explicit impact/ready/conflicts/drift/context/waves/stats smoke queries.
2. **Spec Kit** — PASS.
3. **Existing product CI** — PASS, including quality, PostgreSQL migration/seed, typecheck, tests, build, Storybook accessibility checks and Playwright E2E.

T071 is complete and the feature branch is frozen for review.

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

## Freeze state

`SPEC-009-GRAPH-ENGINEERING-CONTROL-PLANE` is converged. T001–T072 are complete, the final architecture/product/spec gates passed, and PR #15 is ready for review. Further scope changes must be implemented through a new Spec Kit feature branch and PR rather than appended to this frozen change set.
