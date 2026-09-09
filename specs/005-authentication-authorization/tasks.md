# Tasks: Authentication and Authorization

**Input**: Design documents from `specs/005-authentication-authorization/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/session-api.md`, `quickstart.md`

## Phase 1: Setup

**Purpose**: Pin the authentication dependency, declare environment inputs, and record the cross-cutting provider decision before implementation.

- [x] T001 Add exact `better-auth` 1.7.3 dependency and required scripts/config support in `apps/api/package.json`
- [x] T002 [P] Add authentication/session environment placeholders and seed credential placeholders in `apps/api/.env.example`
- [x] T003 [P] Add ADR-0013 documenting Better Auth identity/session boundary and app-owned authorization in `docs/adr/0013-authentication-session-boundary.md`

---

## Phase 2: Foundational

**Purpose**: Build shared contracts, authorization policy, persistence schema, identity adapter, and server guards that block all user stories.

- [x] T004 [P] Add `ApplicationRole`, `SessionPrincipalDto`, and `SessionResponse` transport contracts in `packages/contracts/src/session.ts` and export them from `packages/contracts/src/index.ts`
- [x] T005 Extend `Principal` with display identity/role and add canonical `RequestContext` plus role-to-capability policy in `packages/authorization/src/index.ts`
- [x] T006 [P] Add unit coverage for Admin/Manager/Viewer capability mapping and deny-by-default behavior in `packages/authorization/src/index.test.ts`
- [x] T007 Add Better Auth identity/session/account/verification models plus `AccessProfile`, `ApplicationRole`, and `AccessStatus` to `apps/api/prisma/schema.prisma`
- [x] T008 Create the auth/access PostgreSQL migration under `apps/api/prisma/migrations/`
- [x] T009 Add application access repository operations (`getByUserId`, `upsert`, `setStatus`) in `apps/api/src/platform/authorization/access-profile.repository.ts`
- [x] T010 [P] Add PostgreSQL integration tests for access profile role/status transitions in `apps/api/src/platform/authorization/access-profile.repository.test.ts`
- [x] T011 Create Better Auth factory/configuration with Prisma adapter, cookie/session policy, disabled runtime sign-up, rate limiting, and seed override in `apps/api/src/platform/authentication/auth.ts`
- [x] T012 Add Fastify Better Auth bridge for `/api/auth/*` in `apps/api/src/platform/authentication/fastify-auth.ts`
- [x] T013 Add identity-session-to-Principal resolution and application-owned `/api/session` handler in `apps/api/src/platform/authentication/session.ts`
- [x] T014 Add `requirePrincipal` and `requireCapability` server guards with 401/403 error mapping in `apps/api/src/platform/authorization/guards.ts`
- [x] T015 Wire auth, session, access repository, and guards into `buildApp` in `apps/api/src/app.ts` and runtime startup in `apps/api/src/server.ts`
- [x] T016 Update controlled database seed to create reference Admin/Manager/Viewer identities through the seed-only auth path and access profiles in `apps/api/src/platform/database/seed.ts`

**Checkpoint**: Identity/session mechanics and current authorization state can resolve a Principal without any customer route or UI changes.

---

## Phase 3: User Story 1 — Sign In and Maintain a Secure Session (Priority: P1) 🎯 MVP

**Goal**: A pre-provisioned user can sign in, reload with a valid session, and sign out; unauthenticated users cannot access protected app/API surfaces.

**Independent Test**: Sign in with an active seeded user, request `/api/session`, reload the web app, sign out, and confirm the next protected request returns 401.

### Tests for User Story 1

- [x] T017 [P] [US1] Add Fastify integration tests for sign-in, `/api/session`, invalid credentials, and sign-out in `apps/api/src/platform/authentication/auth.integration.test.ts`
- [x] T018 [P] [US1] Add web authentication service tests for sign-in/sign-out/session error handling in `apps/web/src/features/authentication/api/auth-service.test.ts`
- [x] T019 [P] [US1] Add Playwright session journey covering redirect → sign-in → reload restore → sign-out and asserting no reusable auth secret is stored in browser storage in `apps/web/e2e/auth-session.spec.ts`

### Implementation for User Story 1

- [x] T020 [US1] Add provider-isolated web `AuthService` for sign-in/sign-out and app session fetch in `apps/web/src/features/authentication/api/auth-service.ts`
- [x] T021 [US1] Add TanStack Query-backed authentication/session provider in `apps/web/src/platform/authentication/auth-provider.tsx`
- [x] T022 [P] [US1] Add accessible sign-in form with RHF/Zod and non-enumerating error copy in `apps/web/src/features/authentication/components/sign-in-form.tsx`
- [x] T023 [US1] Add public sign-in page and safe return-target handling in `apps/web/src/features/authentication/views/sign-in-page.tsx`
- [x] T024 [US1] Replace demo principal bootstrap with authenticated session principal and route guards in `apps/web/src/main.tsx`, `apps/web/src/router.tsx`, and `apps/web/src/platform/authorization/authorization-provider.tsx`
- [x] T025 [US1] Add authenticated shell sign-out action and session-state clearing in `apps/web/src/platform/shell/app-shell.tsx`

**Checkpoint**: User Story 1 is deployable and independently demonstrates real authentication/session behavior.

---

## Phase 4: User Story 2 — Enforce Role Capabilities (Priority: P2)

**Goal**: Admin, Manager, and Viewer get the exact customer capability matrix, with server enforcement matching UI adaptation.

**Independent Test**: Execute list/show/create/edit/delete as each seeded role and compare UI affordances plus direct HTTP results to the matrix in `contracts/session-api.md`.

### Tests for User Story 2

- [x] T026 [P] [US2] Add API authorization matrix tests for customer routes in `apps/api/src/modules/customers/customer.authorization.test.ts`
- [x] T027 [P] [US2] Add web authorization tests proving session-derived capabilities control customer actions in `apps/web/src/platform/authorization/authorization-provider.test.tsx`
- [x] T028 [P] [US2] Add Playwright Admin/Manager/Viewer customer matrix coverage in `apps/web/e2e/auth-role-matrix.spec.ts`

### Implementation for User Story 2

- [x] T029 [US2] Apply `customers.read/create/edit/delete` server guards to every customer endpoint in `apps/api/src/modules/customers/customer.routes.ts`
- [x] T030 [US2] Remove `demoPrincipal` from runtime authorization flow and ensure customer navigation/actions derive exclusively from `/api/session` Principal in `apps/web/src/platform/authorization/` and `apps/web/src/features/customers/`
- [x] T031 [US2] Ensure direct forbidden mutations return existing API error envelope with `FORBIDDEN` and no repository mutation in `apps/api/src/platform/authorization/guards.ts`

**Checkpoint**: UI and API independently enforce the same role matrix; API remains authoritative.

---

## Phase 5: User Story 3 — Reject Invalid, Expired, or Disabled Access (Priority: P3)

**Goal**: Missing/revoked sessions and disabled/missing access profiles fail closed immediately on protected server interactions.

**Independent Test**: Establish a session, disable the access profile or revoke the session, then verify `/api/session` and protected customer calls reject access without returning/mutating protected data.

### Tests for User Story 3

- [x] T032 [P] [US3] Add API tests for missing access profile, disabled profile, revoked session, and 401-versus-403 semantics in `apps/api/src/platform/authentication/session.authorization.test.ts`
- [x] T033 [P] [US3] Add Playwright coverage for a session becoming unauthorized during a protected journey in `apps/web/e2e/auth-revocation.spec.ts`

### Implementation for User Story 3

- [x] T034 [US3] Make Principal resolution fail closed for missing/disabled access profiles and map disabled access to `ACCESS_DISABLED` in `apps/api/src/platform/authentication/session.ts`
- [x] T035 [US3] Make the web auth provider transition expired/revoked/disabled session results to an unauthenticated or access-denied state without retaining stale capabilities in `apps/web/src/platform/authentication/auth-provider.tsx`
- [x] T036 [US3] Ensure role/status changes are read from current server access state on each protected request and are not embedded as trusted client authority in `apps/api/src/platform/authorization/guards.ts`

**Checkpoint**: Revocation and access changes are reflected on the next authoritative request.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish accessibility, documentation, deterministic CI, security observability, and convergence evidence.

- [x] T037 [P] Add Storybook stories and axe coverage for sign-in states in `apps/storybook/stories/sign-in-form.stories.tsx`
- [x] T038 [P] Update local auth/PostgreSQL setup and security notes in `docs/development/postgresql.md` and `docs/development/authentication.md`
- [x] T039 Update Vercel/deployment documentation for same-origin auth proxy requirements and required secrets in `docs/deployment/vercel.md`
- [x] T040 Update CI seed/auth environment and ensure PostgreSQL-backed browser tests exercise Better Auth in `.github/workflows/ci.yml`
- [x] T041 Run and fix `pnpm typecheck`, `pnpm test`, `pnpm build`, `pnpm test:storybook`, and `pnpm e2e` without weakening existing gates
- [x] T042 Add structured security-event emission for failed authentication, disabled access, and forbidden authorization decisions without logging credentials/session secrets in `apps/api/src/platform/authentication/security-events.ts`, `apps/api/src/platform/authentication/session.ts`, and `apps/api/src/platform/authorization/guards.ts`, with assertions in auth/authorization tests
- [x] T043 Validate all SC-001 through SC-008 and record any remaining convergence gaps in `specs/005-authentication-authorization/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no feature dependencies.
- **Phase 2 (Foundational)**: depends on Phase 1; blocks all user stories.
- **US1 (P1)**: depends on Phase 2; establishes the authenticated application shell and is the MVP.
- **US2 (P2)**: depends on Phase 2 and consumes session Principal from US1 for the browser experience; API matrix can be developed in parallel once guards exist.
- **US3 (P3)**: depends on Phase 2; browser scenario benefits from US1 session UI.
- **Polish**: depends on completed target stories.

### User Story Dependency Graph

```text
Setup
  ↓
Foundational
  ↓
US1 Session MVP ─────┐
  ↓                  │
US2 Role Matrix      │
  ↓                  │
US3 Revocation ◀─────┘
  ↓
Polish / Convergence
```

US2 API enforcement and US3 server tests can proceed in parallel after Foundational, while their browser journeys consume US1.

## Parallel Opportunities

- T002/T003 can run in parallel with dependency setup.
- T004/T006/T010 target independent packages/test files.
- US1 API, web-service, and Playwright tests (T017–T019) can be authored in parallel.
- US2 test tasks (T026–T028) can be authored in parallel.
- US3 API and browser tests (T032–T033) can be authored in parallel.
- Documentation/Storybook work (T037–T039) can proceed in parallel after functional contracts settle.

## Parallel Example: User Story 2

```text
Task T026: API customer authorization matrix test
Task T027: web session-derived authorization test
Task T028: Playwright role matrix test
```

These touch separate test surfaces and converge on the same acceptance matrix.

## Implementation Strategy

### MVP First

1. Complete Setup + Foundational.
2. Complete US1 only.
3. Validate real Better Auth + PostgreSQL sign-in/session/sign-out end to end.
4. Only then add resource authorization matrix.

### Incremental Delivery

1. **MVP**: real identity/session and protected routing.
2. **Security slice**: server-enforced role capabilities.
3. **Operational slice**: disabled/revoked access behavior.
4. **Hardening**: Storybook/a11y, deployment docs, security events, full CI and convergence.

## Format Validation

All 43 implementation tasks use the required `- [ ] T### [P?] [US?] Description with file path` format. Story-specific tasks carry `[US1]`, `[US2]`, or `[US3]`; setup/foundational/polish tasks intentionally do not.
