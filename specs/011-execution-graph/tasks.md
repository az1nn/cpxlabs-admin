# Tasks: Execution Graph

**Input**: `specs/011-execution-graph/`

**Prerequisites**: `spec.md`, `research.md`, `data-model.md`, `plan.md`

## Phase 1 — Design Gate

- [x] T001 Specify V3 Execution Graph scenarios, FRs and SCs
- [x] T002 [P] Research Git worktree/lease lifecycle constraints
- [x] T003 Define execution manifest/allocation/lease data model
- [x] T004 Define implementation architecture and V3/V4 boundary
- [x] T005 [P] Add requirements checklist and quickstart
- [x] T006 Add ADR-0019 for Execution Graph/worktree lease boundary

## Phase 2 — Execution Manifest Contract

- [x] T007 Implement `ExecutionWave`
- [x] T008 Implement `ExecutionManifest`
- [x] T009 Add semantic manifest canonicalization excluding generated timestamp/output path
- [x] T010 Build manifest from existing V1 `ExecutionPlan`
- [x] T011 Add deterministic JSON serialization
- [x] T012 Implement manifest loader/schema validation
- [x] T013 Validate supported agent adapter without changing plan semantics
- [x] T014 [P] Add manifest determinism/schema unit tests

## Phase 3 — Worktree Boundary

- [x] T015 Implement stable task → branch/path normalization
- [x] T016 Implement Git command wrapper scoped to repository root
- [x] T017 Implement `git worktree list --porcelain` parser
- [x] T018 Detect existing branch collisions
- [x] T019 Detect existing worktree-path collisions
- [x] T020 Implement real worktree creation at exact source revision
- [x] T021 Implement dirty-state detection
- [x] T022 Implement safe worktree removal
- [x] T023 Require explicit force for dirty removal
- [x] T024 [P] Add temporary-Git-repository worktree integration tests

## Phase 4 — Lease Registry

- [x] T025 Implement registry/load/save contract and versioning
- [x] T026 Fail closed on malformed registry/repository mismatch
- [x] T027 Implement active task/branch/path collision checks
- [x] T028 Implement acquire lease
- [x] T029 Implement release lease without canonical Task mutation
- [x] T030 Implement temp-file + replace persistence
- [x] T031 [P] Add lease lifecycle/collision tests

## Phase 5 — Orchestrator

- [x] T032 Implement source-revision validation before mutation
- [x] T033 Implement wave selection validation
- [x] T034 Implement explicit task selection constrained to one valid wave
- [x] T035 Generate V2 `ContextPackage` per selected task
- [x] T036 Strictly validate context freshness during preparation
- [x] T037 Generate selected Codex/Claude handoff from portable package
- [x] T038 Compose worktree + context + handoff into `ExecutionAllocation`
- [x] T039 Acquire active lease only after successful preparation
- [x] T040 Implement dry-run preparation without Git/lease mutation
- [x] T041 Roll back only newly created clean derived state on preparation failure
- [x] T042 [P] Add orchestrator selection/revision/freshness tests

## Phase 6 — CLI

- [x] T043 Add `execution-plan`
- [x] T044 Add `execution-prepare`
- [x] T045 Add `execution-status`
- [x] T046 Add `execution-release`
- [x] T047 Add machine-readable `--json` output
- [x] T048 Ensure cycle/revision/lease collisions return non-zero
- [x] T049 [P] Add CLI parser/behavior tests

## Phase 7 — Documentation / Agent Integration

- [x] T050 Add `docs/architecture/EXECUTION_GRAPH.md`
- [x] T051 Update Engineering Graph README with V3 lifecycle
- [x] T052 Update development guide with plan → prepare → validate → release
- [x] T053 Update `AGENTS.md` for prepared worktree/handoff consumption
- [x] T054 Add `.execution/` to ignored derived outputs
- [x] T055 Preserve application-runtime graph dependency guard

## Phase 8 — CI Integration

- [x] T056 Extend Engineering Graph workflow with V3 execution-plan smoke
- [x] T057 Add semantic manifest reproducibility assertion
- [x] T058 Add conflict-free wave assertion
- [x] T059 Run worktree/lease integration suite in CI
- [x] T060 Preserve V1/V2 context/freshness/adapters smokes
- [x] T061 Keep product CI and Spec Kit authority unchanged

## Phase 9 — Analysis / Convergence

- [x] T062 Run `$speckit-analyze` against FR-001..FR-035 and Constitution
- [x] T063 Execute V3 workflow against ephemeral Neo4j and fix error-level gaps
- [x] T064 Verify real temporary Git worktree lifecycle end-to-end
- [x] T065 Verify allocations always point to fresh V2 package + canonical files
- [x] T066 Verify no app/package runtime dependency on execution tooling
- [x] T067 Run `$speckit-converge` against SC-001..SC-011
- [x] T068 Freeze only after Engineering Graph + Spec Kit + product CI are green on final HEAD

## Dependencies

```text
V1 planner + V2 ContextPackage
            ↓
      manifest contract
            ↓
   worktrees     leases
       \          /
        orchestrator
            ↓
           CLI
            ↓
       docs + CI
            ↓
    analyze/converge
```

## Parallelization

- T007–T014 manifest work can proceed independently of Git mutation code.
- T015–T024 worktree boundary and T025–T031 lease registry can proceed in parallel after the data model stabilizes.
- T032–T042 orchestrator composes the prior phases.
- T050–T055 documentation can proceed once CLI names are stable.

## Format Validation

Stable Spec Kit IDs are used throughout. `[P]` marks independently executable work; cross-task ordering is explicit in the phase dependency graph rather than inferred from prose.