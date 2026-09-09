# Tasks: Observability and Audit

**Input**: `specs/006-observability-audit/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/audit-api.md`, `quickstart.md`

## Phase 1: Setup

- [x] T001 Pin `@fastify/otel` and selected OpenTelemetry 0.222.0 dependencies in `apps/api/package.json`
- [x] T002 [P] Add telemetry environment placeholders to `apps/api/.env.example`
- [x] T003 [P] Add ADR-0014 for correlation, OTel boundary, and atomic durable audit in `docs/adr/0014-observability-audit-boundary.md`

## Phase 2: Foundational

- [x] T004 Add `audit.read` to the project-owned Admin capability policy and tests in `packages/authorization/src/index.ts` and `index.test.ts`
- [x] T005 [P] Add transport-safe audit DTO/list contracts in `packages/contracts/src/audit.ts`
- [x] T006 Add generic `AuditEvent` Prisma model and indexes in `apps/api/prisma/schema.prisma`
- [x] T007 Add committed PostgreSQL migration for audit persistence under `apps/api/prisma/migrations/`
- [x] T008 Add audit domain/repository interfaces and safe mapping under `apps/api/src/platform/audit/`
- [x] T009 Add Prisma audit repository with bounded opaque cursor pagination under `apps/api/src/platform/audit/`
- [x] T010 [P] Add PostgreSQL integration tests for append/list/cursor/subject persistence after deletion in `apps/api/src/platform/audit/`
- [x] T011 Add UUID request-id generation and `x-request-id` response propagation in `apps/api/src/platform/observability/correlation.ts` and `apps/api/src/app.ts`
- [x] T012 Ensure error envelopes and security events use the same request id in `apps/api/src/platform/errors.ts` and authentication/security-event tests

## Phase 3: User Story 1 — Correlate an API Interaction

- [x] T013 [P] [US1] Add API tests proving success/error responses expose correlation ids and error envelope equality
- [x] T014 [P] [US1] Add security-event correlation assertions for authentication/authorization failures
- [x] T015 [US1] Add optional server telemetry bootstrap isolated under `apps/api/src/platform/observability/telemetry.ts`
- [x] T016 [US1] Integrate telemetry startup/shutdown before Fastify loading in `apps/api/src/server.ts`
- [x] T017 [US1] Add tests proving telemetry disabled/enabled configuration does not change domain/error behavior

## Phase 4: User Story 2 — Audit Successful Customer Mutations

- [x] T018 [US2] Add allowlisted customer audit snapshot mapper in `apps/api/src/modules/customers/customer.audit.ts`
- [x] T019 [US2] Define `CustomerMutationService` application boundary with actor/correlation context in `apps/api/src/modules/customers/customer.mutation-service.ts`
- [x] T020 [US2] Add in-memory mutation implementation for lightweight/demo tests without changing production authority semantics
- [x] T021 [US2] Add Prisma mutation service that performs customer create/update/delete plus audit append inside one `$transaction`
- [x] T022 [US2] Update customer mutation routes to use server Principal + request id through `CustomerMutationService`
- [x] T023 [P] [US2] Add PostgreSQL integration tests proving exactly one audit event for create/update/delete with safe snapshots
- [x] T024 [US2] Add Admin-only read-only `GET /api/audit-events` endpoint with filters/cursor and no mutation endpoints
- [x] T025 [P] [US2] Add authorization matrix tests proving Admin can read audit history while Manager/Viewer cannot

## Phase 5: User Story 3 — Prevent Audit Gaps and False Records

- [x] T026 [P] [US3] Add injected audit-failure integration test proving customer mutation rolls back atomically
- [x] T027 [P] [US3] Add tests proving forbidden/unauthenticated/invalid/not-found mutations append no successful domain audit event
- [x] T028 [US3] Ensure audit repository surface exposes no update/delete operation and audit routes remain read-only
- [x] T029 [US3] Ensure failed audit persistence maps to a safe infrastructure error without leaking database details

## Phase 6: User Story 4 — Separate Operational Telemetry from Audit

- [x] T030 [US4] Keep Fastify/Pino security events independent from durable audit and document the concern matrix
- [x] T031 [P] [US4] Add tests proving read/forbidden requests can emit operational evidence without appending customer audit
- [x] T032 [US4] Add correlation id to durable audit independently of OTel exporter state

## Phase 7: Polish & Convergence

- [x] T033 [P] Update development documentation for audit inspection and optional telemetry in `docs/development/observability.md`
- [x] T034 [P] Update deployment documentation for OTLP environment/configuration and request-id propagation
- [x] T035 Update CI migration/test environment and lockfile without weakening existing gates
- [x] T036 Run/fix frozen install, typecheck, tests, build, Storybook/axe, and Playwright
- [x] T037 Re-run Spec Kit analysis against constitution and resolve any uncovered requirement/task mismatch
- [x] T038 Execute `$speckit-converge` against FR-001..FR-020 and SC-001..SC-008; append convergence tasks only if real gaps remain

## Dependencies

```text
Setup
  ↓
Foundational
  ├────────────→ US1 Correlation/Telemetry
  └────────────→ US2 Atomic Audit
                    ↓
                 US3 Rollback
                    ↓
                 US4 Separation
                    ↓
                 Polish/Converge
```

US1 correlation tests and US2 audit data modeling can proceed independently after foundational contracts settle. PostgreSQL mutation/audit atomicity is the blocking gate before audit is considered production-correct.

## Format Validation

All 38 tasks use the Spec Kit checkbox/task identifier format; user-story tasks are labeled `[US1]`–`[US4]`, and independently executable tasks are labeled `[P]` where appropriate.

## Convergence Evidence

`$speckit-analyze` and `$speckit-converge` were re-run after the 006B implementation. The final implementation covers FR-001 through FR-020 and SC-001 through SC-008 without a constitution violation or an uncovered requirement that requires another convergence task.

Final evidence includes:

- UUID request correlation on success and error responses;
- header/error-envelope request-id equality;
- security-event correlation and secret filtering;
- optional OpenTelemetry bootstrap isolated from domain correctness;
- exactly one durable audit event for committed customer create/update/delete;
- allowlisted audit snapshots with no reusable authentication secrets;
- atomic rollback when audit persistence fails;
- zero successful customer audit for unauthenticated, forbidden, validation, not-found, and conflict failures;
- zero customer mutation audit for read-only requests;
- Admin-only bounded audit history retrieval;
- telemetry enabled, disabled, and bootstrap-failure scenarios preserving customer/audit behavior;
- green CI run `34367977710` for frozen install, PostgreSQL migrations/seed, strict typecheck, tests, build, Storybook/axe, and Playwright.

No additional convergence tasks were required.
