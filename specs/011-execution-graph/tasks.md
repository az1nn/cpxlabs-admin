# Tasks: Execution Graph

**Input**: `specs/011-execution-graph/`

**Prerequisites**: `spec.md`, `research.md`, `data-model.md`, `plan.md`

## Phase 1 — Design Gate

- [x] T001 Specify V3 Execution Graph scenarios, FRs and SCs
- [x] T002 [P] Research Git worktree/lease lifecycle constraints
- [x] T003 Define execution manifest/allocation/lease data model
- [x] T004 Define implementation architecture and V3/V4 boundary
- [ ] T005 [P] Add requirements checklist and quickstart
- [ ] T006 Add ADR-0019 for Execution Graph/worktree lease boundary

## Phase 2 — Execution Manifest Contract

- [ ] T007 Implement `ExecutionWave`
- [ ] T008 Implement `ExecutionManifest`
- [ ] T009 Add semantic manifest canonicalization excluding generated timestamp/output path
- [ ] T010 Build manifest from existing V1 `ExecutionPlan`
- [ ] T011 Add deterministic JSON serialization
- [ ] T012 Implement manifest loader/schema validation
- [ ] T013 Validate supported agent adapter without changing plan semantics
- [ ] T014 [P] Add manifest determinism/schema unit tests

## Phase 3 — Worktree Boundary

- [ ] T015 Implement stable task → branch/path normalization
- [ ] T016 Implement Git command wrapper scoped to repository root
- [ ] T017 Implement `git worktree list --porcelain` parser
- [ ] T018 Detect existing branch collisions
- [ ] T019 Detect existing worktree-path collisions
- [ ] T020 Implement real worktree creation at exact source revision
- [ ] T021 Implement dirty-state detection
- [ ] T022 Implement safe worktree removal
- [ ] T023 Require explicit force for dirty removal
- [ ] T024 [P] Add temporary-Git-repository worktree integration tests

## Phase 4 — Lease Registry

- [ ] T025 Implement registry/load/save contract and versioning
- [ ] T026 Fail closed on malformed registry/repository mismatch
- [ ] T027 Implement active task/branch/path collision checks
- [ ] T028 Implement acquire lease
- [ ] T029 Implement release lease without canonical Task mutation
- [ ] T030 Implement temp-file + replace persistence
- [ ] T031 [P] Add lease lifecycle/collision tests

## Phase 5 — Orchestrator

- [ ] T032 Implement source-revision validation before mutation
- [ ] T033 Implement wave selection validation
- [ ] T034 Implement explicit task selection constrained to one valid wave
- [ ] T035 Generate V2 `ContextPackage` per selected task
- [ ] T036 Strictly validate context freshness during preparation
- [ ] T037 Generate selected Codex/Claude handoff from portable package
- [ ] T038 Compose worktree + context + handoff into `ExecutionAllocation`
- [ ] T039 Acquire active lease only after successful preparation
- [ ] T040 Implement dry-run preparation without Git/lease mutation
- [ ] T041 Roll back only newly created clean derived state on preparation failure
- [ ] T042 [P] Add orchestrator selection/revision/freshness tests

## Phase 6 — CLI

- [ ] T043 Add `execution-plan`
- [ ] T044 Add `execution-prepare`
- [ ] T045 Add `execution-status`
- [ ] T046 Add `execution-release`
- [ ] T047 Add machine-readable `--json` output
- [ ] T048 Ensure cycle/revision/lease collisions return non-zero
- [ ] T049 [P] Add CLI parser/behavior tests

## Phase 7 — Documentation / Agent Integration

- [ ] T050 Add `docs/architecture/EXECUTION_GRAPH.md`
- [ ] T051 Update Engineering Graph README with V3 lifecycle
- [ ] T052 Update development guide with plan → prepare → validate → release
- [ ] T053 Update `AGENTS.md` for prepared worktree/handoff consumption
- [ ] T054 Add `.execution/` to ignored derived outputs
- [ ] T055 Preserve application-runtime graph dependency guard

## Phase 8 — CI Integration

- [ ] T056 Extend Engineering Graph workflow with V3 execution-plan smoke
- [ ] T057 Add semantic manifest reproducibility assertion
- [ ] T058 Add conflict-free wave assertion
- [ ] T059 Run worktree/lease integration suite in CI
- [ ] T060 Preserve V1/V2 context/freshness/adapters smokes
- [ ] T061 Keep product CI and Spec Kit authority unchanged

## Phase 9 — Analysis / Convergence

- [ ] T062 Run `$speckit-analyze` against FR-001..FR-035 and Constitution
- [ ] T063 Execute V3 workflow against ephemeral Neo4j and fix error-level gaps
- [ ] T064 Verify real temporary Git worktree lifecycle end-to-end
- [ ] T065 Verify allocations always point to fresh V2 package + canonical files
- [ ] T066 Verify no app/package runtime dependency on execution tooling
- [ ] T067 Run `$speckit-converge` against SC-001..SC-011
- [ ] T068 Freeze only after Engineering Graph + Spec Kit + product CI are green on final HEAD

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