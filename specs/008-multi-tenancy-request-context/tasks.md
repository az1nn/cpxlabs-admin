# Tasks: Multi-Tenancy and Request Isolation

**Input**: `specs/008-multi-tenancy-request-context/`

**Prerequisites**: `spec.md`, `research.md`, `data-model.md`, `contracts/session-tenancy-api.md`, `plan.md`, `quickstart.md`

## Phase 1: Design Gate / PR #14

- [x] T001 Specify tenant isolation, tenant-local authorization, switching, audit ownership, demo behavior and measurable security outcomes
- [x] T002 [P] Validate specification quality checklist and resolve clarification defaults
- [x] T003 [P] Research tenant selector validation, cache isolation, shared-table persistence and RLS tradeoffs
- [x] T004 Define final data model, migration invariants and session/tenant transport contracts
- [x] T005 Add ADR-0016 for stateless URL selection, server-validated RequestContext and mandatory repository scoping
- [x] T006 Run `$speckit-analyze` across FR-001..FR-029, SC-001..SC-009 and constitution; freeze design after green Spec Kit/CI

## Phase 2: 008A Additive Tenant Identity Foundation / new PR #15

- [ ] T007 Add Tenant/TenantMembership/session-context DTOs, TenantScope and stable tenant error codes as additive shared contracts without removing legacy SessionResponse
- [ ] T008 Add TenantStatus and MembershipStatus plus Tenant/TenantMembership Prisma models only; do not add domain tenant ownership yet
- [ ] T009 Create additive migration A with deterministic reference Tenant and membership backfill from existing AccessProfile roles while retaining AccessProfile.role compatibility
- [ ] T010 Update explicit seed data with Alpha, Beta and Disabled tenants plus multi-role user memberships
- [ ] T011 Add Tenant/TenantMembership repository boundary and Prisma implementation
- [ ] T012 [P] Add repository tests for active membership discovery, disabled membership, disabled tenant and uniqueness
- [ ] T013 Implement tenant selector parsing with `TENANT_CONTEXT_REQUIRED`
- [ ] T014 Implement additive tenant RequestContext resolver that authenticates identity, enforces global AccessProfile status, validates active Tenant/membership, and derives tenant-local Principal
- [ ] T015 Implement additive `GET /api/session/context` while leaving existing `/api/session` and domain route behavior unchanged in #15
- [ ] T016 [P] Add Fastify tests for valid, missing, random, disabled and non-member tenant context
- [ ] T017 [P] Add same-identity Manager-in-Alpha/Viewer-in-Beta context/capability tests
- [ ] T018 [P] Add membership-revocation, tenant-disable and global AccessProfile-disable next-request tests
- [ ] T019 Attach only verified tenant id to security/telemetry context and retain secret redaction/request correlation
- [ ] T020 Add architecture/regression assertion that #15 does not activate tenant-looking domain UX or require tenant headers on legacy domain routes
- [ ] T021 Run/fix frozen install, migration A/backfill, seed, strict typecheck, unit/API/PostgreSQL tests, build, Storybook/axe and current Playwright
- [ ] T022 Re-run Spec Kit analysis for additive-foundation coverage and freeze #15; all activation work goes to a new MR

## Phase 3: 008B Activation Migration and Final Session Model / new PR #16

- [ ] T023 Add non-null target `tenantId` ownership fields/relations for Customer, Opportunity and tenant-owned AuditEvent
- [ ] T024 Replace Customer global email uniqueness with `(tenantId,email)` and tenant-leading Customer indexes
- [ ] T025 Add tenant-leading Opportunity and Audit indexes preserving workflow/audit query behavior
- [ ] T026 Create migration B: add nullable ownership, backfill existing rows to reference tenant, apply uniqueness/index changes, then enforce NOT NULL
- [ ] T027 Change final AccessProfile model to global status only and remove `role` after all authorization code is membership-derived
- [ ] T028 [P] Add migration-B/schema tests for non-null ownership, reference backfill, tenant-local email uniqueness and removed global role authority
- [ ] T029 Change `GET /api/session` to final identity + active membership discovery contract in the same MR as the matching web SessionProvider update
- [ ] T030 Ensure final protected RequestContext requires tenant and has no optional tenant field
- [ ] T031 [P] Add session discovery tests excluding disabled memberships/tenants and preserving global AccessProfile denial

## Phase 4: 008B Customer Tenant Isolation

- [ ] T032 Make every CustomerRepository method require TenantScope
- [ ] T033 Update in-memory and Prisma Customer list/get/create/update/delete queries to use tenant scope in persistence predicates
- [ ] T034 Update Customer mutation/audit service so record ownership and AuditEvent tenant id derive only from RequestContext
- [ ] T035 Ensure Customer mutation contracts expose no ownership field and spoofed tenant-shaped body/query data cannot set ownership
- [ ] T036 Map cross-tenant Customer detail/update/delete to ordinary not-found after selected-tenant validation
- [ ] T037 [P] Add PostgreSQL Customer two-tenant list/detail/create/update/delete isolation tests
- [ ] T038 [P] Add same-email-across-tenants and duplicate-email-within-tenant tests
- [ ] T039 [P] Add cross-tenant Customer attack tests proving zero foreign mutation and zero successful foreign audit

## Phase 5: 008B Opportunity and Audit Tenant Isolation

- [ ] T040 Make every OpportunityRepository method require TenantScope and scope Prisma list/detail predicates by tenant
- [ ] T041 Update Opportunity workflow create/transition to derive tenant from RequestContext and include tenant in compare-and-swap predicate
- [ ] T042 Preserve Opportunity create/transition + AuditEvent atomicity with the same verified tenant id
- [ ] T043 Map cross-tenant Opportunity detail/workflow commands to ordinary not-found
- [ ] T044 [P] Add PostgreSQL two-tenant Opportunity list/detail/create/workflow isolation tests
- [ ] T045 [P] Add cross-tenant stale/transition attacks proving zero foreign mutation/audit and unchanged version
- [ ] T046 Make AuditRepository append/list tenant-scoped for tenant-owned domain evidence and add tenant predicates to reads
- [ ] T047 Ensure committed Customer/Opportunity domain audit rows have non-null RequestContext tenant id
- [ ] T048 [P] Add tenant-scoped audit read tests proving Alpha cannot read Beta events and correlation remains intact
- [ ] T049 Add architecture tests that tenant-owned repository interfaces cannot be invoked without TenantScope

## Phase 6: 008B Web Session, Routing, Transport and Cache Isolation

- [ ] T050 Refactor web SessionProvider to final identity + active membership discovery rather than one global Principal
- [ ] T051 Add tenant session-context client for `/api/session/context`
- [ ] T052 Add `/tenants` selection/no-membership experience and deterministic post-sign-in routing
- [ ] T053 Move tenant-owned Customer and Opportunity routes under `/t/$tenantSlug/...`
- [ ] T054 Resolve route slug only against discovered active memberships before rendering protected tenant pages
- [ ] T055 Supply tenant-local Principal to AuthorizationProvider from scoped session context
- [ ] T056 Create one tenant-bound HTTP transport/fetch that injects canonical `X-Tenant-Id`
- [ ] T057 Bind HttpDataProvider and HttpOpportunityService through the tenant transport; feature components never set tenant headers
- [ ] T058 Include canonical tenant id in every Customer list/detail query key
- [ ] T059 Include canonical tenant id in every Opportunity list/detail query key
- [ ] T060 Ensure tenant switching naturally segregates cached data and add no-stale-row cache tests
- [ ] T061 Update Resource Registry/navigation URL generation to preserve tenant slug without embedding authorization in resource definitions
- [ ] T062 Add visible current-tenant identity and deterministic membership switcher to shell
- [ ] T063 Handle invalid/revoked/disabled tenant routes without rendering protected Customer/Opportunity/Audit/workflow state

## Phase 7: 008B Demo, Browser and Accessibility

- [ ] T064 Model deterministic Alpha/Beta memberships and isolated Customer/Opportunity datasets in demo services
- [ ] T065 [P] Add demo tenant switch/isolation unit tests
- [ ] T066 Update all existing authenticated Customer/Opportunity Playwright journeys to tenant-prefixed routes
- [ ] T067 [P] Add browser journey proving one identity is Manager in Alpha and Viewer in Beta with corresponding controls/API outcomes
- [ ] T068 [P] Add browser tenant-switch journey proving URL, visible tenant, capabilities and datasets switch without prior-tenant rows
- [ ] T069 [P] Add HTTP E2E cross-tenant id probing/mutation checks against PostgreSQL
- [ ] T070 [P] Add browser membership-revocation/tenant-disable next-request denial journey
- [ ] T071 [P] Add Storybook/axe coverage for tenant selector/switcher, zero-membership and access-denied states
- [ ] T072 Add web architecture tests proving tenant id is in tenant-owned query keys and tenant header injection exists only in the owned transport
- [ ] T073 Update local/deployment docs with migration/seed, URL/header selector boundary and no-client-authority rule

## Phase 8: 008B Gate and Convergence

- [ ] T074 Run/fix frozen install, migrations A+B, seed, strict typecheck, tests, build, Storybook/axe and full Playwright
- [ ] T075 Re-run `$speckit-analyze` across FR-001..FR-029 and constitution after activation
- [ ] T076 Execute `$speckit-converge` against SC-001..SC-009 and append tasks only for real uncovered isolation gaps
- [ ] T077 If convergence is clean, freeze #16; if material security/migration gaps remain, create a **new** 008C branch/MR rather than reusing prior MRs

## Dependencies

```text
008 design / #14
      ↓
008A additive Tenant/Membership/Context foundation / new #15
      ↓
008B migration B + server isolation + web activation / new #16
      ↓
optional 008C only for material convergence gaps / new #17
```

The additive #15 deliberately does not expose tenant-scoped domain UX or change existing domain request requirements. The security boundary becomes active atomically with the matching web client in #16, avoiding both permissive feature flags and independently broken merges.

## Format Validation

All 77 tasks use Spec Kit checkbox/task identifiers. Independently executable tasks use `[P]` where applicable. MR boundaries explicitly preserve the project rule that each stage receives a new MR.
