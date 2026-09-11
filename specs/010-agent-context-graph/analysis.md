# Spec Kit Analysis: Agent Context Graph

**Feature**: `SPEC-010-AGENT-CONTEXT-GRAPH`  
**Date**: 2026-09-11  
**Scope**: FR-001..FR-034, SC-001..SC-010, Constitution v1.1.0

## Result

PASS — no unresolved requirement, constitution conflict, or implementation-boundary contradiction remains before final convergence. The implementation stays within V2: deterministic portable context packages, freshness validation, agent adapters, READY-task batch generation, and CI coverage. V3 execution orchestration and V4 semantic/GraphRAG capabilities remain explicitly deferred.

## Constitution analysis

| Principle | Result | Evidence |
|---|---|---|
| Spec before implementation | PASS | `spec.md`, `research.md`, `data-model.md`, `plan.md`, `tasks.md`, requirements checklist and ADR-0018 define the feature boundary |
| Explicit application boundaries | PASS | all runtime code lives under `engineering-graph/`; `apps/*` and product `packages/*` remain free of Neo4j/`engineering_graph` imports |
| Strict types/tests/CI are gates | PASS | Python unit tests and ephemeral Neo4j validation supplement unchanged Spec Kit and product CI |
| Simplicity/evolvability | PASS | one portable `ContextPackage` feeds Codex/Claude adapters; adapters do not query Neo4j independently |
| Git-authoritative Engineering Graph | PASS | package/Neo4j outputs remain disposable derived context; canonical edits stay in Git-backed files |

No Complexity Tracking exception is required.

## Functional requirement coverage

| Requirement | Primary evidence | Status |
|---|---|---|
| FR-001 | ADR-0018, AGENTS/docs source-of-truth rules, disposable output lifecycle | Covered |
| FR-002 | engineering-only Python package + CI dependency guard | Covered |
| FR-003 | `ContextPackage` packageVersion/repository/sourceRevision/task/generatedAt/freshness/budget fields | Covered |
| FR-004 | task + parent spec contract/query | Covered |
| FR-005 | requirement + ADR groups in context query/package | Covered |
| FR-006 | dependency group with task status metadata | Covered |
| FR-007 | `codeArtifacts` + tests in portable contract | Covered |
| FR-008 | deterministic PR evidence from V1 graph projection | Covered |
| FR-009 | `ContextProvenance` relation/via/sourcePath entries | Covered |
| FR-010 | depth/node budget validation and deterministic selection | Covered |
| FR-011 | deterministic JSON + human-readable Markdown serializers | Covered |
| FR-012 | `semantic_dict`/`semantic_json` exclude operational metadata; reproducibility CI smoke | Covered |
| FR-013 | ignored/disposable context-package output directories | Covered |
| FR-014 | single-task `context` / explicit `context-batch --task` | Covered |
| FR-015 | READY-task `context-batch --spec` | Covered |
| FR-016 | READY selector includes only rows with `ready == true` by default | Covered |
| FR-017 | repeated explicit task selection is sorted/deduplicated deterministically | Covered |
| FR-018 | `ContextPackage.from_dict`, contract validation, repository/revision checks | Covered |
| FR-019 | strict freshness report validity requires `current` | Covered |
| FR-020 | non-strict freshness inspection reports stale/unknown without mandatory failure | Covered |
| FR-021 | adapters consume `ContextPackage`; no store/Neo4j dependency in adapter module | Covered |
| FR-022 | Codex handoff explicitly follows repository `AGENTS.md` and canonical paths | Covered |
| FR-023 | Claude portable Markdown handoff over same package | Covered |
| FR-024 | handoffs include task, repository, source revision, package path, canonical files and validation commands | Covered |
| FR-025 | adapters only render/write handoffs; no spawn/worktree/commit/push/merge behavior | Covered |
| FR-026 | package summary + manifest expose included/truncated/rendered byte statistics | Covered |
| FR-027 | deterministic byte-budget trimming with explicit truncation summary | Covered |
| FR-028 | context query projects allowlisted graph properties/path metadata only; no secret-store integration | Covered |
| FR-029 | Engineering Graph workflow exercises single/batch/freshness/adapters/reproducibility/disposability | Covered |
| FR-030 | application dependency isolation grep retained in Graph CI | Covered |
| FR-031 | `AGENTS.md` documents generate → validate → inspect canonical files workflow | Covered |
| FR-032 | README/development/architecture docs explain sync → validate → generate → validate freshness → consume → discard | Covered |
| FR-033 | spec/ADR/docs explicitly exclude embeddings, semantic retrieval and autonomous execution | Covered |
| FR-034 | package/manifest interfaces form a clean V3 consumer seam without scheduler coupling | Covered |

## Success criteria coverage

| Criterion | Verification |
|---|---|
| SC-001 | unit tests + CI regenerate a package at the same revision and compare `semantic_json()` |
| SC-002 | context query/package contract includes Spec, Requirements, ADRs, dependencies, CodeArtifacts, Tests and PR evidence when linked |
| SC-003 | batch tests + CI READY generation select one package per READY task; explicit task mode is independently tested |
| SC-004 | freshness-validation tests cover current/stale/unknown/malformed; CI runs strict current validation |
| SC-005 | context tests cover deterministic depth/node/byte truncation and summary accounting |
| SC-006 | adapter unit tests assert Codex/Claude parity over one portable package and zero independent graph traversal |
| SC-007 | batch writer replaces derived task directories safely; CI deletes and regenerates packages |
| SC-008 | Engineering Graph workflow uses ephemeral Neo4j and runs all V2 smokes while product/Spec Kit workflows remain separate |
| SC-009 | application dependency guard proves product packages do not import graph tooling |
| SC-010 | AGENTS, README, architecture, development docs and quickstart describe the complete Task → package → validation → canonical-files flow |

## Risk review

### Generated context becoming a second source of truth
Mitigated by ADR-0018, AGENTS guidance, package authority notices, ignored output paths and disposable regeneration semantics.

### Stale package consumption
Mitigated by source revision stamping, current Git revision resolution and strict freshness validation that fails closed unless status is `current`.

### Context explosion
Mitigated by bounded depth, node count and semantic byte budgets; deterministic pruning reports included/truncated counts and rendered bytes.

### Adapter divergence
Mitigated by one portable package model and pure renderers for both Codex and Claude Code. Neither adapter imports the graph store or executes queries.

### Hidden orchestration scope creep
Mitigated by explicit V2 non-goals: no agent spawning, worktree allocation, autonomous commit/push/merge, embeddings or GraphRAG.

## Analyze conclusion

No additional implementation tasks are required from `$speckit-analyze`. The remaining convergence action is operational: retarget the stacked PR to `master`, rerun the independent Engineering Graph / Spec Kit / product gates on the reconciled final branch, and freeze only when they are green.