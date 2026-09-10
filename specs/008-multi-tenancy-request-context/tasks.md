# Tasks: Multi-Tenancy and Request Isolation

**Input**: `specs/008-multi-tenancy-request-context/`

**Prerequisites**: `spec.md`, `research.md`, `data-model.md`, `contracts/session-tenancy-api.md`, `plan.md`, `quickstart.md`

## Phase 1: Design Gate / PR #14

- [x] T001 Specify tenant isolation, tenant-local authorization, switching, audit ownership, demo behavior and measurable security outcomes
- [x] T002 [P] Validate specification quality checklist and resolve clarification defaults
- [x] T003 [P] Research tenant selector validation, cache isolation, shared-table persistence and RLS tradeoffs
- [x] T004 Define data model, migration invariants and session/tenant transport contracts
- [x] T005 Add ADR-0016 for stateless URL selection, server-validated RequestContext and mandatory repository scoping
- [x] T006 Run `$speckit-analyze` across FR-001..FR-029, SC-001..SC-009 and constitution; freeze design PR after green Spec Kit/CI

## Phase 2: Shared Contracts and Persistence Foundation (008A / new PR #15)

- [ ] T007 Add Tenant/TenantMembership/session discovery/context DTOs and stable tenant error codes to shared contracts
- [ ] T008 Add required `TenantScope`/TenantContext application types without exposing Prisma types
- [ ] T009 Add TenantStatus and MembershipStatus plus Tenant/TenantMembership Prisma models
- [ ] T010 Add non-null target `tenantId` ownership to Customer and Opportunity models
- [ ] T011 Change Customer email uniqueness to `(tenantId, email)` and tenant-leading indexes
- [ ] T012 Add tenant-leading Opportunity indexes preserving workflow query behavior
- [ ] T013 Make tenant-owned AuditEvent tenant identity mandatory in the target schema and add tenant-leading indexes
- [ ] T014 Create one migration that backfills a deterministic reference tenant/memberships and existing Customer/Opportunity/Audit rows before NOT NULL constraints
- [ ] T015 Remove the global AccessProfile role persistence authority after membership backfill while preserving AccessProfile status
- [ ] T016 [P] Add migration/schema tests for reference backfill, tenant-local customer email uniqueness and required ownership
- [ ] T017 Update explicit seed data with Alpha/Beta/disabled tenants, multi-role memberships and clearly separated tenant-owned domain fixtures

## Phase 3: Session Discovery and Tenant RequestContext (008A)

- [ ] T018 Add Tenant/TenantMembership repository boundary and Prisma implementation
- [ ] T019 [P] Add repository tests for active membership discovery, disabled membership and disabled tenant filtering
- [ ] T020 Refactor global session resolver to authenticate identity + enforce AccessProfile status without deriving one global role
- [ ] T021 Implement `GET /api/session` identity + active membership discovery contract
- [ ] T022 Implement required tenant selector parser with `TENANT_CONTEXT_REQUIRED`
- [ ] T023 Implement tenant RequestContext resolver that revalidates Tenant + membership every request and returns generic `TENANT_ACCESS_DENIED`
- [ ] T024 Resolve Principal role/capabilities exclusively from the validated TenantMembership
- [ ] T025 Implement `GET /api/session/context` using the same request-time resolver as protected routes
- [ ] T026 [P] Add Fastify tests for missing/random/disabled/non-member tenant context and global AccessProfile disablement
- [ ] T027 [P] Add same-identity Manager-in-Alpha/Viewer-in-Beta authorization tests
- [ ] T028 [P] Add membership-revocation and tenant-disable-after-login tests proving denial on the next request
- [ ] T029 Attach only verified tenant id to security/telemetry context while preserving request correlation and secret redaction

## Phase 4: Customer Tenant Isolation (008A)

- [ ] T030 Make every CustomerRepository method require TenantScope
- [ ] T031 Update in-memory and Prisma Customer repositories so list/get/create/update/delete use tenant scope at the repository query boundary
- [ ] T032 Update Customer mutation/audit service so record ownership and AuditEvent tenant id come only from RequestContext
- [ ] T033 Ensure Customer create/update contracts expose no ownership field and spoofed tenant-shaped inputs cannot set ownership
- [ ] T034 Map cross-tenant Customer detail/update/delete to ordinary not-found after tenant validation
- [ ] T035 [P] Add PostgreSQL Customer two-tenant list/detail/create/update/delete isolation tests
- [ ] T036 [P] Add same-email-across-tenants and duplicate-email-within-tenant tests
- [ ] T037 [P] Add cross-tenant Customer attack tests proving zero foreign mutation and zero successful foreign audit

## Phase 5: Opportunity and Audit Tenant Isolation (008A)

- [ ] T038 Make every OpportunityRepository method require TenantScope
- [ ] T039 Scope Prisma Opportunity list/detail predicates by tenant
- [ ] T040 Update Opportunity workflow create/transition to derive tenant from RequestContext and include tenant in CAS predicate
- [ ] T041 Preserve Opportunity create/transition + AuditEvent atomicity with the same verified tenant id
- [ ] T042 Map cross-tenant Opportunity detail/workflow commands to ordinary not-found after tenant validation
- [ ] T043 [P] Add PostgreSQL two-tenant Opportunity list/detail/create/workflow isolation tests
- [ ] T044 [P] Add cross-tenant stale/transition attacks proving zero foreign mutation/audit and unchanged version
- [ ] T045 Make AuditRepository list/read require TenantScope and add tenant predicate to every audit query
- [ ] T046 Ensure committed Customer/Opportunity domain audit rows have non-null RequestContext tenant id
- [ ] T047 [P] Add tenant-scoped audit read tests proving Alpha cannot read Beta events and correlation remains intact
- [ ] T048 Add architecture tests that tenant-owned repository interfaces cannot be called without TenantScope

## Phase 6: 008A Backend Gate / new PR #15

- [ ] T049 Run/fix frozen install, migration/backfill, seed, strict typecheck, unit/API/PostgreSQL tests, build and existing browser regression
- [ ] T050 Re-run Spec Kit analysis for backend coverage of FR-001..FR-018 and FR-025..FR-029
- [ ] T051 Freeze backend PR after all isolation/security gates are green; do not add web tenancy code to that MR

## Phase 7: Web Session, Routing and Tenant Transport (008B / new PR #16)

- [ ] T052 Refactor web SessionProvider to identity + active membership discovery rather than one global Principal
- [ ] T053 Add tenant session-context client for `/api/session/context`
- [ ] T054 Add `/tenants` selection/no-membership experience and deterministic post-sign-in routing
- [ ] T055 Move tenant-owned Customer and Opportunity routes under `/t/$tenantSlug/...`
- [ ] T056 Resolve route slug only against discovered active memberships before rendering protected tenant pages
- [ ] T057 Supply tenant-local Principal to AuthorizationProvider from scoped session context
- [ ] T058 Create one tenant-bound HTTP transport/fetch that injects canonical `X-Tenant-Id`
- [ ] T059 Bind HttpDataProvider and HttpOpportunityService through the tenant transport; feature components must not set tenant headers
- [ ] T060 Include canonical tenant id in Customer list/detail TanStack Query keys
- [ ] T061 Include canonical tenant id in Opportunity list/detail TanStack Query keys
- [ ] T062 Ensure tenant switching cannot reuse unscoped prior-tenant Query data and add cache-isolation tests
- [ ] T063 Update Resource Registry/navigation URL generation to preserve explicit tenant slug without embedding tenant authority in resource definitions
- [ ] T064 Add visible current-tenant identity and deterministic membership switcher to the application shell
- [ ] T065 Handle invalid/revoked/disabled tenant route without rendering protected domain content

## Phase 8: Demo, Browser and Accessibility (008B)

- [ ] T066 Model deterministic Alpha/Beta memberships and isolated Customer/Opportunity datasets in demo auth/data services
- [ ] T067 [P] Add demo tenant switch/isolation unit tests
- [ ] T068 Update existing authenticated Customer/Opportunity Playwright journeys to tenant-prefixed routes
- [ ] T069 [P] Add browser journey proving one identity is Manager in Alpha and Viewer in Beta with matching controls/API outcomes
- [ ] T070 [P] Add browser tenant-switch journey proving URL, visible tenant, capability controls and datasets switch without stale rows
- [ ] T071 [P] Add HTTP E2E cross-tenant id probing/mutation checks against PostgreSQL
- [ ] T072 [P] Add browser membership-revocation/tenant-disable next-request denial journey
- [ ] T073 [P] Add Storybook/axe coverage for tenant selector/switcher, zero-membership and tenant-access-denied states
- [ ] T074 Add web architecture tests proving tenant id is present in tenant-owned query keys and injected only through owned transport
- [ ] T075 Update local/deployment docs with tenant seed, URL/header boundary and no-client-authority rule

## Phase 9: 008B Gate and Convergence

- [ ] T076 Run/fix frozen install, migrations/seed, strict typecheck, tests, build, Storybook/axe and full Playwright
- [ ] T077 Re-run `$speckit-analyze` across FR-001..FR-029 and constitution after web integration
- [ ] T078 Execute `$speckit-converge` against SC-001..SC-009 and append tasks only for real uncovered isolation gaps
- [ ] T079 If convergence is clean, freeze 008B PR; if material security/migration gaps remain, create a **new** 008C branch/MR rather than reusing prior MRs

## Dependencies

```text
008 design / PR #14
      ↓
shared contracts + migration
      ↓
session discovery + RequestContext
      ↓
Customer isolation
      ↓
Opportunity + Audit isolation
      ↓
008A backend gate / new PR #15
      ↓
web tenant routes + transport + cache isolation
      ↓
demo/browser/a11y
      ↓
008B gate / new PR #16
      ↓
optional 008C only if convergence discovers material gaps
```

The security boundary is server/repository-side. Frontend tenant visibility, URL routing, and cache isolation are required correctness/UX defenses but never substitute for request-time membership validation.

## Format Validation

All 79 tasks use Spec Kit checkbox/task identifiers. Independently executable tasks use `[P]` where applicable. PR/MR slice boundaries are explicit to preserve the project rule that each stage receives a new MR.
