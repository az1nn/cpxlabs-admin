# Spec Kit Analysis: Execution Graph

**Feature**: `SPEC-011-EXECUTION-GRAPH`  
**Date**: 2026-09-11  
**Scope**: FR-001..FR-035, SC-001..SC-011, Constitution v1.1.0

## Result

PASS — the V3 implementation is internally consistent with the specification and Constitution. No error-level requirement gap or source-of-truth inversion remains. V3 composes the existing deterministic V1 planner and V2 portable context contract into local execution planning/worktree orchestration while keeping Git canonical and GraphRAG/autonomous publication out of scope.

## Constitution analysis

| Principle | Result | Evidence |
|---|---|---|
| I. Spec Before Implementation | PASS | Spec 011, research, data model, plan and task ledger were created on the V3 branch before implementation modules |
| II. Explicit application boundaries | PASS | all V3 runtime code remains under `engineering-graph/`; application dependency guard still rejects Neo4j/`engineering_graph` imports under `apps/*` and product `packages/*` |
| III. Server authority / typed authorization | N/A | V3 is engineering tooling and does not change product authorization behavior |
| IV. Strict types/tests/CI are gates | PASS | Python unit + real temporary Git worktree integration tests supplement unchanged Product CI, Spec Kit and existing graph gates |
| V. Simplicity / ownership / evolvability | PASS | V3 reuses `planner.py`, `ContextPackage` and agent adapters; ADR-0019 records the new cross-cutting worktree/lease boundary |
| VI. Git-authoritative Engineering Graph | PASS | manifests/leases/context/worktree metadata are explicitly derived; canonical task state remains Markdown/Git; no inferred blocking edges are introduced |

No Complexity Tracking exception is required.

## Functional requirement coverage

| Requirement | Primary evidence | Status |
|---|---|---|
| FR-001 | ADR-0019, AGENTS source-of-truth rules, `.execution/` ignore | Covered |
| FR-002 | `orchestrator.py` reuses `build_execution_plan`, `load_tasks_from_store`, `build_context`, V2 handoff writers | Covered |
| FR-003 | `ExecutionManifest` version/repository/revision/spec/agent/timestamp contract | Covered |
| FR-004 | `ExecutionManifest` carries ready/blocked/cycles/conflicts/waves | Covered |
| FR-005 | existing deterministic planner + `semantic_json()` reproducibility CI assertion | Covered |
| FR-006 | V1 planner artifact-overlap wave exclusion + V3 CI conflict-safe assertion | Covered |
| FR-007 | cycle evidence in manifest; `select_manifest_tasks` rejects preparation when cycles exist; CLI planning returns non-zero | Covered |
| FR-008 | existing V1 unresolved dependency model treats non-done dependencies as blockers | Covered |
| FR-009 | `execution-prepare` requires explicit wave or explicit task set validated against the manifest | Covered |
| FR-010 | `_assert_manifest_revision` runs before preparation mutation and again during allocation | Covered |
| FR-011 | `branch_name_for_task()` deterministic `exec/<task-safe>` naming | Covered |
| FR-012 | `worktree_path_for_task()` under ignored `.execution/worktrees/` default root | Covered |
| FR-013 | `ensure_worktree()` uses `git worktree add`; real integration tests prove actual Git worktree lifecycle | Covered |
| FR-014 | expected deterministic resume is detected; branch-at-other-path and foreign filesystem path collide fail-closed; no branch reset | Covered |
| FR-015 | `LeaseRegistry` persists task/branch/path/revision/agent/status/timestamps/context/handoff metadata | Covered |
| FR-016 | `assert_allocation_available()` rejects active duplicate task/branch/path ownership | Covered |
| FR-017 | registry validation + temporary-file replacement; malformed state fails closed | Covered |
| FR-018 | registry lives below ignored `.execution/`; no Neo4j lease synchronization is implemented | Covered |
| FR-019 | `_build_current_packages()` invokes existing V2 `build_context()` for every selected task | Covered |
| FR-020 | strict `inspect_freshness(..., strict=True)` required before active preparation | Covered |
| FR-021 | existing `write_agent_handoff()` renders the manifest-selected V2 agent handoff | Covered |
| FR-022 | manifest agent only selects handoff; branch/path/wave logic is agent-neutral | Covered |
| FR-023 | `ExecutionAllocation` exposes task/spec/revision/branch/worktree/context/handoff/validation commands | Covered |
| FR-024 | allocation metadata is operator-facing; V3 performs no commit/push/merge/publication side effects | Covered |
| FR-025 | no coding-agent process supervisor/spawn implementation; `ExecutionAllocation` is the future runner seam | Covered |
| FR-026 | `release_lease()` changes local lease status only; no canonical Task mutation | Covered |
| FR-027 | `remove_worktree()` checks `git status --porcelain` and refuses dirty removal without force | Covered |
| FR-028 | destructive removal requires explicit `--force` and operates only on the selected registered worktree | Covered |
| FR-029 | manifest/allocation/registry have deterministic JSON contracts; CLI supports `--json` | Covered |
| FR-030 | `.execution/` is ignored/reconstructible metadata; docs explicitly exempt dirty worktree contents as user data | Covered |
| FR-031 | Engineering Graph CI runs Python suite containing real temporary Git worktree + lease lifecycle tests and V3 Neo4j smokes | Covered |
| FR-032 | existing application dependency-isolation guard remains enabled | Covered |
| FR-033 | AGENTS, README, development guide, architecture doc and quickstart document plan → prepare → work/validate → release | Covered |
| FR-034 | no embeddings/vector search/GraphRAG/LLM-inferred graph edges added | Covered |
| FR-035 | stable `ExecutionAllocation` contract exposes future runner inputs without changing V1/V2 interfaces | Covered |

## Success criteria coverage

| Criterion | Result | Verification |
|---|---|---|
| SC-001 manifest reproducibility | PASS | `ExecutionManifest.semantic_json()` tests + two same-HEAD `execution-plan` CI runs |
| SC-002 V1 planner parity | PASS | V3 manifest is constructed directly from existing `ExecutionPlan`; no parallel planner exists |
| SC-003 conflict-safe waves | PASS | planner tests plus V3 CI assertion that conflict pairs never share a wave |
| SC-004 isolated worktree per task | PASS | `test_worktrees.py` and `test_orchestrator.py` create/remove real Git worktrees in temporary repositories |
| SC-005 active lease collision | PASS | `test_leases.py` covers duplicate task, branch and path ownership |
| SC-006 revision drift fail-closed | PASS | orchestrator stale-manifest test + repeated `_assert_manifest_revision` |
| SC-007 fresh V2 package + handoff | PASS | preparation builds current package, strict freshness checks, writes context + handoff before active lease; CI dry-run exercises real Neo4j context |
| SC-008 safe release / dirty protection | PASS | real Git integration test refuses dirty removal without force and proves clean release/removal |
| SC-009 CI integration | PASS | Engineering Graph CI passes Spec 011 plan/reproducibility/conflict/dry-run against ephemeral Neo4j; Git worktree integration runs in same job |
| SC-010 runtime independence | PASS | app/product package graph-dependency guard remains green |
| SC-011 operator documentation | PASS | quickstart + AGENTS + README + architecture/development docs describe complete lifecycle |

## Contract / implementation reconciliation

Two documentation details were reconciled during analyze rather than treated as code gaps:

1. dry-run returns `ExecutionAllocation.leaseStatus = planned` but does not persist an active lease; the data model now explicitly includes `planned | active | released`;
2. deterministic prior task state can be resumed without reset when the exact expected worktree/branch is observed and no active lease owns it. Foreign branch/path ownership remains fail-closed. This is resume semantics, not silent overwrite.

## Risk review

### Lease interpreted as canonical task state
Mitigated by ADR-0019, AGENTS and code: lease acquire/release never edits `tasks.md` or graph Task status.

### Destructive cleanup of agent/user work
Mitigated by real Git dirty-state inspection, opt-in worktree removal and explicit `--force` for destructive cleanup.

### Stale planning/context
Mitigated by revision-bound manifest generation, graph projection revision checks and strict V2 context freshness before allocation.

### Conflict bypass through explicit CLI tasks
Mitigated by requiring every explicit selection to be a subset of one existing manifest wave.

### Vendor-specific scheduling drift
Mitigated by binding agent selection only to handoff rendering; planner, branch and worktree semantics are agent-independent.

### Local lease mistaken for distributed lock
Mitigated by explicit non-goal/documentation. V3 supports one local checkout/orchestrator domain only.

## Analyze conclusion

No new implementation task is required by `$speckit-analyze`. The remaining convergence operation is to reconcile the completed task ledger, record final SC evidence, then freeze only after Engineering Graph, Spec Kit and Product CI are green on the reconciled final HEAD.