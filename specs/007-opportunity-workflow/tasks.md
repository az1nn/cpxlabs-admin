# Tasks: Opportunity Workflow

**Input**: `specs/007-opportunity-workflow/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/opportunity-api.md`, `quickstart.md`

## Phase 1: Setup and Shared Contracts

- [x] T001 Add Opportunity DTO/input/list/transition contract types and stable workflow error codes in `packages/contracts/`
- [x] T002 Add `opportunities.read`, `opportunities.create`, `opportunities.transition` to the role capability policy and matrix tests
- [x] T003 [P] Add ADR-0015 documenting explicit domain commands, optimistic concurrency, and DataProvider non-extension
- [x] T004 Generalize audit contracts to support safe Customer and Opportunity snapshots/action/subject namespaces without weakening existing customer types
- [x] T005 [P] Add contract/audit regression tests proving customer and opportunity snapshots remain typed/allowlisted

## Phase 2: PostgreSQL Opportunity Foundation

- [x] T006 Add `OpportunityStage` and `Opportunity` to Prisma schema with BIGINT amount, date close field, version, indexes, and terminal loss reason field
- [x] T007 Add committed PostgreSQL migration for Opportunity persistence
- [x] T008 Add Opportunity domain types/mappers with safe bigint↔number and date transport conversion
- [x] T009 [P] Add Opportunity input/list/params JSON schemas with strict server validation
- [x] T010 Add read-only `OpportunityRepository` interface with in-memory reference implementation
- [x] T011 Add Prisma Opportunity repository for bounded list/detail queries
- [x] T012 [P] Add PostgreSQL repository tests for list/search/stage/sort/detail and safe amount/date mapping

## Phase 3: User Story 3/4 — Domain Workflow Engine

- [x] T013 [US3] Implement pure reference lifecycle transition matrix in `apps/api/src/modules/opportunities/opportunity.workflow.ts`
- [x] T014 [P] [US3] Add unit tests accepting all documented valid transitions and rejecting skipped/backward/terminal transitions
- [x] T015 [P] [US3] Add loss-reason validation unit tests
- [x] T016 [US4] Define `OpportunityWorkflowService` with create/transition command context and expectedVersion
- [x] T017 [US3] Add in-memory workflow service preserving version and audit semantics for lightweight API tests
- [x] T018 [US3] Add explicit Opportunity audit snapshot mapper and opportunity audit input helpers
- [x] T019 [US4] Add Prisma workflow service using one transaction and conditional `id + version` compare-and-swap
- [x] T020 [US4] Map stale version to `WORKFLOW_CONFLICT`, invalid lifecycle to `WORKFLOW_INVALID_TRANSITION`, and preserve existing not-found/infrastructure envelopes
- [x] T021 [P] [US4] Add PostgreSQL concurrency test proving two commands with one expectedVersion yield at most one committed transition
- [x] T022 [P] [US3] Add PostgreSQL tests for create qualification/version 1 and every valid forward/lost/won transition
- [x] T023 [P] [US3] Add tests proving invalid/terminal transitions leave stage/version unchanged

## Phase 4: User Story 5 — Reuse Durable Audit

- [x] T024 [US5] Append `opportunities.create` inside the same transaction as Opportunity creation
- [x] T025 [US5] Append `opportunities.stage.change` inside the same transaction as a successful transition
- [x] T026 [P] [US5] Add tests proving exactly one opportunity audit event per committed create/transition with safe before/after snapshots and request correlation
- [x] T027 [P] [US5] Add injected audit-failure test proving Opportunity create/transition rolls back atomically
- [x] T028 [P] [US5] Add tests proving forbidden/validation/invalid-transition/stale/not-found commands append zero successful opportunity audit events
- [x] T029 [US5] Ensure `GET /api/audit-events` filters support `subjectType=opportunity` without customer regression

## Phase 5: User Story 1/2/3 — Fastify API

- [x] T030 [US1] Add `GET /api/opportunities` and `GET /api/opportunities/:id` guarded by `opportunities.read`
- [x] T031 [US2] Add `POST /api/opportunities` guarded by `opportunities.create`; server assigns stage/version
- [x] T032 [US3] Add `POST /api/opportunities/:id/commands/transition` guarded by `opportunities.transition`
- [x] T033 [US3] Ensure there is no generic Opportunity PATCH/PUT/DELETE route
- [x] T034 [P] [US1] Add Fastify authorization/list/detail/create tests for Admin/Manager/Viewer
- [x] T035 [P] [US3] Add Fastify command tests for valid transition, invalid transition, stale conflict and request-id/error-envelope correlation
- [x] T036 Wire Opportunity repository/workflow service into `buildApp()` and production `server.ts`

## Phase 6: 007A Backend Gate / PR #12

- [x] T037 Run/fix Prisma generate, migrations, strict typecheck, API/unit/PostgreSQL tests, build, Storybook/axe and existing Playwright regression
- [x] T038 Re-run Spec Kit analysis and confirm backend tasks cover FR-001..FR-020 plus backend portions of FR-021..FR-025
- [x] T039 Freeze PR #12 after green CI; all frontend work continues in a new MR

## Phase 7: User Story 1/2/3/4 — Web Domain Service and UI (007B)

- [ ] T040 [US1] Add domain-specific `OpportunityService` and HTTP implementation; do not modify generic DataProvider with workflow commands
- [ ] T041 [P] [US1] Add service serialization/error tests including `WORKFLOW_CONFLICT`
- [ ] T042 [US1] Add opportunity TanStack Query keys/list/detail hooks and bounded URL-controlled list state
- [ ] T043 [US1] Register Opportunity resource with list/show/create routes and no edit/delete route
- [ ] T044 [US1] Add opportunity list and detail pages using owned UI primitives with stage/version/value/date presentation
- [ ] T045 [US2] Add create form with RHF/Zod and capability-aware visibility
- [ ] T046 [US3] Add workflow action panel deriving valid next actions from state/capability while treating API as authoritative
- [ ] T047 [US3] Add lost-reason interaction and terminal-state action suppression
- [ ] T048 [US4] On workflow conflict, refresh authoritative detail/list state and surface a stable stale-state message
- [ ] T049 [US3] Invalidate opportunity query caches after successful create/transition
- [ ] T050 [P] Add component/unit tests proving workflow actions are outside DataProvider and Viewer receives no mutation controls

## Phase 8: Browser, Accessibility and Convergence (007B)

- [ ] T051 [P] Add Storybook/axe coverage for Opportunity stage badge, action panel, loss-reason state and conflict message
- [ ] T052 [P] Add Playwright Viewer read-only Opportunity journey
- [ ] T053 [P] Add Playwright Manager/Admin create + valid transition + lost/won terminal journey
- [ ] T054 [P] Add Playwright/API stale-version recovery journey
- [ ] T055 Add explicit architecture test/assertion that generic DataProvider contains no opportunity transition method
- [ ] T056 Update developer documentation for extending the reference workflow without turning it into a generic engine
- [ ] T057 Run/fix frozen install, migrations, strict typecheck, tests, build, Storybook/axe and Playwright
- [ ] T058 Re-run `$speckit-analyze` against FR-001..FR-025 and constitution
- [ ] T059 Execute `$speckit-converge` against SC-001..SC-009; append tasks only for real uncovered gaps

## Dependencies

```text
Shared contracts
      ↓
PostgreSQL foundation
      ↓
Workflow engine + concurrency
      ↓
Atomic audit reuse
      ↓
Fastify API
      ↓
007A backend gate / PR #12
      ↓
Web OpportunityService + UI
      ↓
Browser/a11y/convergence / new MR
```

Backend workflow and audit correctness are blocking gates before frontend workflow actions are implemented. The frontend can never compensate for a missing server transition rule.

## Format Validation

All 59 tasks use Spec Kit checkbox/task identifiers. User-story work is labeled `[US1]`–`[US5]`; independently executable tasks use `[P]` where applicable.
