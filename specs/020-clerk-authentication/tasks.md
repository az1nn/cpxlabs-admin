# Tasks: Clerk Authentication Provider Migration

**Input**: Design documents from `specs/020-clerk-authentication/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/session-api.md`, `quickstart.md`

## Phase 1: Setup and dependency resolution

- [ ] T001 Resolve current npm `latest` for `@clerk/react` and add exact pin to `apps/web/package.json`
- [ ] T002 Resolve current npm `latest` for `@clerk/fastify` and add exact pin to `apps/api/package.json`
- [ ] T003 Remove `better-auth` from `apps/web/package.json` and `better-auth` + `@better-auth/prisma-adapter` from `apps/api/package.json` (depends: T001,T002)
- [ ] T004 Regenerate `pnpm-lock.yaml` with the exact resolved dependency graph (depends: T001,T002,T003)
- [ ] T005 [P] Add Clerk server/web environment contract to `apps/api/.env.example`, `apps/web/.env.example`, and `apps/web/src/config/env.ts`
- [ ] T006 [P] Add ADR-0028 at `docs/adr/0028-clerk-authentication-provider-boundary.md`

## Phase 2: Foundational provider-neutral API boundary

- [ ] T007 Define provider-neutral `AuthenticatedIdentity` / `IdentityProvider` in `apps/api/src/platform/authentication/identity-provider.ts`
- [ ] T008 [P] Add pure unit tests for identity-to-Principal request-context behavior
- [ ] T009 Refactor `apps/api/src/platform/authentication/session.ts` to depend on `IdentityProvider` + current `AccessProfileRepository` (depends: T007)
- [ ] T010 Preserve `401 AUTHENTICATION_REQUIRED`, `403 ACCESS_DISABLED`, and current Principal DTO semantics in `session.ts` (depends: T009)
- [ ] T011 [P] Preserve capability guard semantics in `apps/api/src/platform/authorization/guards.ts`
- [ ] T012 Add Bearer-header enforcement tests for protected application requests (depends: T009)

## Phase 3: User Story 2 — Clerk Fastify authentication (Priority P1)

- [ ] T013 [US2] Implement `apps/api/src/platform/authentication/clerk-identity-provider.ts` with `@clerk/fastify`
- [ ] T014 [US2] Register Clerk Fastify plugin only in authenticated server runtime and keep env loading before Clerk imports (depends: T013)
- [ ] T015 [US2] Normalize Clerk user ID/email/name to `AuthenticatedIdentity` without exporting Clerk SDK types (depends: T013)
- [ ] T016 [P] [US2] Add adapter tests for authenticated, unauthenticated, missing-email/name fallback, and provider failure behavior
- [ ] T017 [US2] Update `apps/api/src/server.ts` startup validation for `CLERK_PUBLISHABLE_KEY` / `CLERK_SECRET_KEY` and remove Better Auth startup config (depends: T014)
- [ ] T018 [US2] Remove Better Auth `/api/auth/*` route bridge and dead runtime files (depends: T014)

## Phase 4: Persistence migration

- [ ] T019 Remove Better Auth `User`, `Session`, `Account`, `Verification` models from `apps/api/prisma/schema.prisma`
- [ ] T020 Remove the `AccessProfile.user` relation/FK while preserving unique external `userId` (depends: T019)
- [ ] T021 Add Prisma migration dropping only Better Auth provider tables/FK and preserving `access_profiles` (depends: T019,T020)
- [ ] T022 Update `PrismaAccessProfileRepository` tests so external Clerk-like user IDs require no local User row (depends: T020)
- [ ] T023 Update `apps/api/src/platform/database/seed.ts` to stop creating Better Auth identities and optionally seed access profiles from explicit Clerk user IDs (depends: T020)

## Phase 5: User Story 1 — Clerk web sign-in/session (Priority P1)

- [ ] T024 [US1] Add conditional Clerk server-auth bootstrap/provider in `apps/web/src/main.tsx` without requiring Clerk in demo mode
- [ ] T025 [US1] Replace custom password form with Clerk `<SignIn />` in `apps/web/src/features/auth/sign-in-page.tsx` (depends: T024)
- [ ] T026 [US1] Preserve safe return-target behavior in `apps/web/src/router.tsx`
- [ ] T027 [US1] Introduce token provider/adapter based on Clerk `useAuth().getToken()`
- [ ] T028 [US1] Implement shared authenticated fetch that attaches Bearer token and never persists it (depends: T027)
- [ ] T029 [US1] Update application session provider to use Clerk auth state/sign-out while continuing to bootstrap Principal from `/api/session` (depends: T027,T028)
- [ ] T030 [US1] Update customer `DataProvider` HTTP construction to use authenticated fetch (depends: T028)
- [ ] T031 [US1] Update Opportunity HTTP service construction to use authenticated fetch (depends: T028)
- [ ] T032 [US1] Update any remaining protected HTTP adapters to use authenticated fetch (depends: T028)
- [ ] T033 [P] [US1] Add web unit tests for token injection, missing-token failure, session bootstrap, and sign-out clearing

## Phase 6: User Story 3 — Revocation/fail-closed behavior (Priority P2)

- [ ] T034 [US3] Ensure Clerk unauthenticated/token-refresh failure clears application Principal and cached authority
- [ ] T035 [US3] Verify disabled/missing AccessProfile rejects the next request independently of Clerk session validity
- [ ] T036 [P] [US3] Add tests for invalid/expired provider identity, disabled profile, role change, and no blind retry
- [ ] T037 [US3] Preserve secret-safe security events and remove provider credential/token logging risk

## Phase 7: User Story 4 — Better Auth cleanup (Priority P2)

- [ ] T038 [US4] Remove Better Auth-specific source files/imports/env names and update authentication/deployment docs
- [ ] T039 [US4] Verify no active source/package/Prisma model references Better Auth
- [ ] T040 [US4] Update `docs/adr/0013-authentication-session-boundary.md` status/cross-reference to ADR-0028 without erasing historical rationale
- [ ] T041 [US4] Update `specs/README.md` feature index/current state

## Phase 8: Validation and live Clerk gate

- [ ] T042 Run Prisma generate/migration checks, strict TypeScript, unit/integration tests, and production build
- [ ] T043 Run Storybook component/accessibility regression
- [ ] T044 Run deterministic Playwright product regression without requiring external Clerk secrets
- [ ] T045 Add/document Clerk-supported Playwright live auth journey gated by Clerk development credentials
- [ ] T046 Run Spec Kit validation and Engineering Graph gates
- [ ] T047 Record exact resolved Clerk package versions and same-HEAD automated gate evidence in `convergence.md`
- [ ] T048 Record `CLERK-LIVE-INTEGRATION` as PENDING/PASSED from explicit external evidence; agent MUST NOT self-pass it
- [ ] T049 Produce `analysis.md` traceability review and close all implementation-derived gaps
- [ ] T050 Freeze final candidate HEAD only after all repository-automatable gates are green

## Dependencies & Execution Order

```text
Spec/Research
   ↓
Dependencies + ADR
   ↓
Provider-neutral API boundary
   ├── Clerk Fastify adapter
   └── Persistence migration
             ↓
       Clerk web bootstrap
             ↓
       Authenticated fetch
             ↓
      Protected feature adapters
             ↓
    Revocation / cleanup / tests
             ↓
       Repository convergence
             ↓
 CLERK-LIVE-INTEGRATION (human/external)
```

## Parallel Opportunities

- T005/T006 can proceed independently after spec freeze.
- T008/T011 can be authored while T009 is implemented.
- Prisma model/migration work and Clerk web component work can proceed after dependency resolution, but converge before browser tests.
- T030/T031/T032 target separate HTTP adapter files after authenticated fetch exists.
- Documentation and Storybook regression can proceed independently after behavior stabilizes.

## Definition of Done

The feature is implementation-converged when T001–T050 are checked with evidence, except that production readiness remains explicitly blocked while required Human Async Gate `CLERK-LIVE-INTEGRATION` is PENDING.
