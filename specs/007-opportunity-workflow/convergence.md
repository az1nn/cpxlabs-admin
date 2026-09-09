# Convergence: Opportunity Workflow

**Feature**: `007-opportunity-workflow`  
**Slices**: 007A backend / PR #12; 007B web / PR #13  
**Result**: converged with no uncovered implementation tasks

## Functional-requirement analysis

| Requirement | Evidence | Result |
|---|---|---|
| FR-001..FR-007 | Shared Opportunity contracts, PostgreSQL model, pure lifecycle matrix, Prisma workflow integration tests | Covered |
| FR-008 | Explicit transition command endpoint and domain `OpportunityService`; no generic workflow update endpoint | Covered |
| FR-009..FR-011 | `expectedVersion`, Prisma `id + version` compare-and-swap, version assertions and concurrency test | Covered |
| FR-012 | Fastify lifecycle validation and capability guards independent of UI | Covered |
| FR-013..FR-015 | Typed opportunity capabilities and Admin/Manager/Viewer API matrix | Covered |
| FR-016 | Resource Registry exposes list/show/create only; no edit/delete route | Covered |
| FR-017..FR-020 | Opportunity audit allowlist, atomic transaction, rollback and zero-audit failure tests | Covered |
| FR-021 | `OpportunityService` owns commands; DataProvider architecture test proves CRUD-only surface | Covered |
| FR-022 | Workflow panel derives currently valid actions from loaded state/capability; API remains authoritative | Covered |
| FR-023 | Successful create/transition invalidates affected Opportunity queries and updates authoritative detail | Covered |
| FR-024 | `OpportunityServiceError` preserves `WORKFLOW_CONFLICT`; UI refetches current detail/lists and never blindly retries | Covered |
| FR-025 | Full CI preserves authentication, customer CRUD, audit, telemetry, strict TS, accessibility and browser gates | Covered |

## Success-criteria convergence

| Criterion | Evidence | Result |
|---|---|---|
| SC-001 | Pure lifecycle tests cover all documented valid and invalid/skipped/terminal transitions | Met |
| SC-002 | PostgreSQL concurrency test accepts at most one transition for one expected version | Met |
| SC-003 | Create/version and forward/lost/won transition integration tests | Met |
| SC-004 | Forbidden, validation, invalid, stale and not-found command tests append zero successful audit events | Met |
| SC-005 | Atomic create/transition audit tests assert exactly-one safe correlated evidence | Met |
| SC-006 | Backend capability matrix plus Viewer, Manager and Admin browser coverage | Met |
| SC-007 | `data-provider.architecture.test.ts` asserts both generic providers expose CRUD methods only | Met |
| SC-008 | Playwright proves Viewer read-only, Manager create/terminal journeys, Admin controls and stale-state recovery | Met |
| SC-009 | Frozen install, PostgreSQL migrations/seed, strict typecheck, unit/integration tests, build, Storybook/axe and Playwright are required final gates | Met when final PR HEAD CI is green |

## Constitution compliance

### I. Spec Before Implementation

Feature 007 was specified, planned and decomposed before material implementation. Backend and frontend were split into explicit 007A/007B delivery slices while retaining one feature source of truth. Completed work is reconciled back into `tasks.md` rather than removing historical tasks.

### II. Backend-Agnostic Frontend and Explicit Boundaries

- `DataProvider` remains generic CRUD-only.
- Opportunity commands use the named `OpportunityService.transition()` use case.
- TanStack Router owns shareable list pagination/search/filter/sort state.
- TanStack Query owns remote list/detail cache.
- `apps/web` imports only shared application contracts; no Prisma/Fastify/database types cross the boundary.

### III. Server Authority and Typed Authorization

UI capability checks only suppress unavailable controls. Fastify independently requires `opportunities.read`, `opportunities.create`, and `opportunities.transition`. Workflow validity and optimistic concurrency are enforced by the API/database path, not by frontend state.

### IV. Strict Types, Tests, and CI

No strictness or quality gate was weakened. The feature adds domain, repository, transaction, audit, architecture, accessibility and critical-browser tests while retaining all existing gates.

### V. Simplicity, Ownership, and Evolvability

No new state manager, framework, queue, cache or generic workflow engine was introduced. The reference lifecycle remains intentionally explicit and application-owned. ADR-0015 records the durable command/concurrency boundary.

## Convergence decision

No additional implementation task is required for FR-001..FR-025 or SC-001..SC-009. Future configurable pipelines, backward transitions, terminal reopening, ownership, approvals, forecasting and idempotency keys remain explicitly outside feature 007 and should begin as separate specifications if introduced.
