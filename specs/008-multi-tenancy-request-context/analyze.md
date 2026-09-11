# Analyze: Multi-Tenancy and Request Isolation

**Feature**: `008-multi-tenancy-request-context`  
**Date**: 2026-09-10  
**Phase**: pre-implementation design analysis

## Result

PASS. No requirement/plan/task contradiction or Constitution violation was found. FR-001..FR-029 and SC-001..SC-009 have explicit implementation/test coverage in T007..T079. No production code should begin in PR #14.

## Requirement coverage

| Requirement group | Planned evidence | Result |
|---|---|---|
| FR-001..FR-003 | Tenant/TenantMembership contracts, Prisma schema, uniqueness and repository tests | Covered |
| FR-004..FR-005 | AccessProfile global status refactor, membership-only role authority, same-user cross-tenant role tests | Covered |
| FR-006..FR-008 | required tenant RequestContext, selector parser, membership validation and spoofing tests | Covered |
| FR-009..FR-013 | mandatory Customer/Opportunity TenantScope, tenant predicates, server-derived ownership and cross-tenant 404 tests | Covered |
| FR-014..FR-015 | mandatory audit tenant ownership and tenant-scoped AuditRepository/list tests | Covered |
| FR-016..FR-018 | membership role resolution, session discovery, scoped session context | Covered |
| FR-019..FR-024 | tenant-prefixed Router tree, owned transport, query-key isolation, shell switcher and denied-route states | Covered |
| FR-025 | revocation/tenant-disable next-request integration/browser tests | Covered |
| FR-026 | deterministic demo tenants and isolated demo datasets | Covered |
| FR-027..FR-028 | verified tenant metadata integrated with existing security/telemetry correlation/redaction | Covered |
| FR-029 | full existing quality/browser/PostgreSQL regression gates | Covered |

## Success criteria coverage

| Criterion | Planned gate | Result |
|---|---|---|
| SC-001 | two-tenant PostgreSQL Customer/Opportunity read/write isolation matrix | Covered |
| SC-002 | cross-tenant id read/update/delete/workflow attack tests + audit assertions | Covered |
| SC-003 | one identity Manager in Alpha / Viewer in Beta API + browser matrix | Covered |
| SC-004 | tenant-id audit atomicity + tenant-scoped audit read tests | Covered |
| SC-005 | browser tenant-switch URL/data/capability/cache isolation journey | Covered |
| SC-006 | repository type/architecture tests requiring TenantScope | Covered |
| SC-007 | membership revocation + tenant disable next-request tests | Covered |
| SC-008 | demo journey plus real HTTP/PostgreSQL enforcement journey | Covered |
| SC-009 | existing CI + Spec Kit gates | Covered |

## Constitution analysis

### I. Spec Before Implementation

PASS. Design artifacts are isolated in PR #14. Implementation is explicitly delegated to new PRs #15/#16 (and #17 only if convergence requires material additional work).

### II. Backend-Agnostic Frontend and Explicit Boundaries

PASS. The web consumes shared session/tenant DTOs and a tenant-bound transport, not Prisma/Fastify types. Router owns tenant slug navigation; Query owns tenant-scoped remote state. The generic DataProvider remains generic and receives tenant context via transport binding rather than new business methods.

### III. Server Authority and Typed Authorization

PASS. The selected tenant is not trusted. Better Auth identity + AccessProfile status + current TenantMembership are resolved before Principal/capabilities. Repository TenantScope is mandatory and server-created.

### IV. Strict Types, Tests, and CI

PASS. The plan strengthens types by making tenant required instead of optional at protected repository/context boundaries. PostgreSQL two-tenant and browser attack/regression matrices are blocking gates.

### V. Simplicity, Ownership, and Evolvability

PASS. No external tenancy framework, hidden session tenant, second state manager, cache, queue, or service is introduced. RLS is consciously deferred as additive defense in depth rather than mixed into the first tenant-context change.

## High-risk implementation points

### 1. Migration/backfill sequencing

Risk: applying NOT NULL or dropping global role before existing records/memberships are backfilled.

Control: T014/T015/T016 require deterministic backfill and schema assertions before application cutover.

### 2. Optional tenant scope leaking back into repositories

Risk: `tenantId?:` or post-fetch authorization creates unscoped paths.

Control: TenantScope is required by repository interfaces; T048 architecture tests enforce call-shape expectations and PostgreSQL tests exercise every operation.

### 3. Dual role authority

Risk: AccessProfile.role and TenantMembership.role diverge.

Control: membership becomes sole tenant role source; the legacy global role is removed from persistence authority after backfill.

### 4. Cache bleed during tenant switch

Risk: Customer/Opportunity query keys currently lack tenant identity.

Control: T060/T061 make canonical tenant id part of every tenant-owned key and T062/T070 prove no prior-tenant data renders after switching.

### 5. Header treated as trusted context downstream

Risk: callers manually set or consume `X-Tenant-Id` without membership validation.

Control: one transport factory injects it; one server RequestContext resolver validates it; downstream repositories receive only validated TenantScope.

### 6. Audit becomes partially tenant-scoped

Risk: domain rows are isolated but audit list or new audit rows omit tenant.

Control: AuditRepository scope is mandatory and Customer/Opportunity mutation services derive both domain/audit tenant from the same RequestContext.

### 7. RLS false confidence

Risk: partial RLS or pool context creates a second isolation model that tests do not actually exercise.

Control: RLS is outside 008. A future RLS spec must add transaction-local context, least-privileged request DB role, pool-reuse tests, and coverage inventory while retaining application TenantScope.

## Design conclusion

The feature is ready for implementation after PR #14 is merged. The next production change must start in a new branch/MR for 008A backend isolation. No material clarification remains and no task needs to be appended before implementation.
