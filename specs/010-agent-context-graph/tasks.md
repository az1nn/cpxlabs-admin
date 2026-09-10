# Tasks: Agent Context Graph

**Input**: `specs/010-agent-context-graph/`

**Prerequisites**: `spec.md`, `research.md`, `data-model.md`, `plan.md`

## Phase 1 — Design Gate

- [x] T001 Specify V2 Agent Context Graph scenarios, boundaries, FRs and SCs
- [x] T002 [P] Research current Codex/Claude context integration constraints
- [x] T003 Define portable ContextPackage/freshness/manifest data model
- [x] T004 Define implementation architecture and V2/V3/V4 boundaries
- [ ] T005 [P] Add requirements checklist and quickstart
- [ ] T006 Add ADR-0018 for portable agent context package boundary

## Phase 2 — Context Package Contract

- [ ] T007 Extend ContextBudget with maxBytes
- [ ] T008 Extend ContextPackage with packageVersion/repository/sourceRevision/generatedAt/freshness metadata
- [ ] T009 Add ContextPackageSummary included/truncated/rendered byte fields
- [ ] T010 Add deterministic ContextProvenance model
- [ ] T011 Rename portable `code` output to `codeArtifacts` while retaining compatibility where needed
- [ ] T012 Add semantic canonicalization helper excluding operational metadata
- [ ] T013 Add deterministic byte-budget enforcement
- [ ] T014 [P] Add package-contract/reproducibility/budget unit tests

## Phase 3 — Freshness Validation

- [ ] T015 Implement current Git revision resolver using repository root
- [ ] T016 Implement ContextPackage JSON loader/schema validation
- [ ] T017 Implement current/stale/unknown FreshnessReport
- [ ] T018 Implement strict vs inspect validation semantics
- [ ] T019 Add `context-validate` CLI command with JSON/human output
- [ ] T020 [P] Add malformed/current/stale/unknown validation tests

## Phase 4 — Agent Adapters

- [ ] T021 Implement pure shared agent-handoff model over ContextPackage
- [ ] T022 Implement Codex Markdown adapter aligned with `AGENTS.md` + canonical path navigation
- [ ] T023 Implement Claude Code portable Markdown adapter
- [ ] T024 Include validation commands and source-of-truth notice in both adapters
- [ ] T025 Ensure adapters perform zero Neo4j queries
- [ ] T026 Add `context-adapt --agent codex|claude` CLI command
- [ ] T027 [P] Add deterministic adapter tests and parity assertions

## Phase 5 — Automatic / Batch Packages

- [ ] T028 Implement READY-task selector using existing `ready-tasks.cypher`
- [ ] T029 Exclude BLOCKED tasks in default READY mode
- [ ] T030 Implement explicit repeated `--task` selection
- [ ] T031 Implement deterministic per-task output directory naming
- [ ] T032 Write `context.json`, `context.md`, `codex.md`, `claude.md` per selected task
- [ ] T033 Implement top-level deterministic PackageManifest
- [ ] T034 Implement derived-output cleanup/regeneration safety
- [ ] T035 Add `context-batch --spec` and `context-batch --task` CLI surfaces
- [ ] T036 Emit machine-readable generation statistics
- [ ] T037 [P] Add READY/BLOCKED/explicit-selection/manifest tests

## Phase 6 — Documentation / Agent Integration

- [ ] T038 Update `AGENTS.md` with generate → validate → canonical-file workflow
- [ ] T039 Update Engineering Graph README with V2 commands and package lifecycle
- [ ] T040 Add Agent Context Graph architecture documentation
- [ ] T041 Add V2 operator/development quickstart
- [ ] T042 Ensure generated package directories remain Git-ignored
- [ ] T043 Preserve application-runtime graph dependency guard

## Phase 7 — CI Integration

- [ ] T044 Extend Engineering Graph workflow with single-task package generation
- [ ] T045 Add strict freshness validation smoke
- [ ] T046 Add READY batch generation smoke
- [ ] T047 Add Codex/Claude adapter smoke
- [ ] T048 Add delete/regenerate disposable-package smoke
- [ ] T049 Add semantic reproducibility assertion
- [ ] T050 Run offline V2 unit suite in existing Engineering Graph job
- [ ] T051 Keep product CI and Spec Kit authority unchanged

## Phase 8 — Analysis / Convergence

- [ ] T052 Run `$speckit-analyze` against FR-001..FR-034 and Constitution
- [ ] T053 Execute V2 package workflow against ephemeral Neo4j and fix error-level gaps
- [ ] T054 Verify package artifacts contain provenance and bounded context for a real task
- [ ] T055 Verify Codex/Claude handoffs point to canonical files and do not duplicate source authority
- [ ] T056 Verify app/packages remain independent of graph tooling
- [ ] T057 Run `$speckit-converge` against SC-001..SC-010 and append only real uncovered work
- [ ] T058 Retarget PR to `master` after #15 merges and rerun all gates
- [ ] T059 Freeze PR only after Engineering Graph + Spec Kit + product CI are green on final HEAD

## Dependencies

```text
V1 Engineering Graph
       ↓
package contract + budgets
       ↓
freshness validation
       ↓
adapters ──────┐
       │        │
       └── batch packages
               ↓
          docs/AGENTS
               ↓
               CI
               ↓
        analyze/converge
```

## Parallelization

- T021–T027 adapters can proceed after the portable package contract stabilizes.
- T028–T037 batch generation can proceed in parallel with adapters after ContextPackage serialization stabilizes.
- Documentation T038–T043 can proceed after CLI names are stable.
- CI T044–T051 follows implementation but can be developed independently of product code because the graph toolchain remains isolated.

## Format Validation

All tasks use stable Spec Kit task IDs. `[P]` denotes independently executable work; explicit dependency edges should use `depends:` metadata rather than inferred phase ordering.
