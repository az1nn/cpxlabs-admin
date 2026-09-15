# Analysis: Agent Supervisor V6

## Scope result

V6 implements deterministic, local, tick-based coordination over one already-prepared V3 execution wave and V5 Agent Runner processes. The implementation does not add a new canonical task state, graph vocabulary, product runtime dependency, Git publication path, lease mutation path or remote scheduler.

## Functional requirement evidence

| Requirements | Evidence |
| --- | --- |
| FR-001–FR-006 manifest/wave/allocation identity | `supervisor.py::_validate_manifest_for_supervision`, `_validate_active_allocations`; V3 `select_manifest_tasks` remains the wave selector. |
| FR-007 active ownership collision | `create_supervisor_job`; `test_active_supervisors_cannot_claim_same_task`. |
| FR-008–FR-011 versioned job/task policy and bounds | `SupervisorJob`, `SupervisorTask`, validators, atomic JSON job files. |
| FR-012–FR-018 reconcile/concurrency/retry policy | `_reconcile_job`, `supervisor_tick`; concurrency/order/retry/stopped tests in `test_supervisor.py` and `test_supervisor_parallel.py`. |
| FR-019–FR-021 authority boundary | ADR-0022 and `AGENT_SUPERVISOR.md`; no Task, lease, Git or Neo4j mutation API is imported by the supervisor. |
| FR-022–FR-024 status/tick/start semantics | `supervisor_cli.py`, `status_supervisor_jobs`, `start_supervisor_job`, `supervisor_tick`. |
| FR-025–FR-027 stop semantics | `stop_supervisor_job` verifies exact latest job-owned `runId`, then delegates termination to V5 `stop_run`; it never releases V3 leases. |
| FR-028–FR-029 atomic/disposable state | `_atomic_json`; `.execution/supervisor/jobs/<job-id>.json`; no canonical information is stored there. |
| FR-030 CLI JSON automation surface | `supervisor-start`, `supervisor-tick`, `supervisor-status`, `supervisor-stop` with `--json`. |
| FR-031 runtime isolation | Existing Engineering Graph CI application-dependency guard remained green. |
| FR-032 V1–V5 compatibility | Engineering Graph workflow #314 succeeded on implementation candidate `d4d9ad4c9918047bc9f4071e3d85dacc1e4ab42f`. |

## Success criteria evidence

- **SC-001**: `test_tick_respects_parallel_limit_and_wave_order` proves one available slot launches one task in manifest-wave order and later advances to the next task.
- **SC-002**: `test_supervisor_parallel.py` proves `maxParallel=2` starts exactly two eligible tasks and does not exceed the bound.
- **SC-003**: failed/orphaned retry and stopped no-retry tests prove attempt-bound semantics.
- **SC-004**: `test_supervisor_parallel.py` repeats a tick while both slots are occupied and proves no duplicate process is launched.
- **SC-005**: the parallel-success path reconciles the job to `settled`; implementation contains no V3 release or canonical Task mutation call.
- **SC-006**: active overlapping supervisor creation raises `SupervisorCollisionError`.
- **SC-007**: stop ownership mismatch test proves fail-closed behavior before delegating to V5.
- **SC-008**: supervisor job files are isolated under the ignored `.execution/supervisor/` subtree and have no canonical inbound dependency.
- **SC-009**: Engineering Graph #314 passed the full pre-existing and V6 unittest/integration discovery suite on the implementation candidate; the freeze-candidate run additionally includes `test_supervisor_parallel.py`.
- **SC-010**: on implementation candidate `d4d9ad4c9918047bc9f4071e3d85dacc1e4ab42f`, Spec Kit #382, Engineering Graph #314 and Product CI #715 all succeeded. The freeze candidate commit that adds this closure evidence must rerun the same three gates before PR readiness.

## Boundary review

The supervisor imports V3/V5 read/execute primitives but no canonical-authoring or publication primitive. `succeeded`, `exhausted`, `stopped`, `active`, `settled` remain local orchestration observations. A future validation/publication layer requires a new spec/ADR rather than extending these meanings implicitly.
