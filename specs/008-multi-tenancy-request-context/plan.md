# Implementation Plan: Multi-Tenancy and Request Isolation

**Branch**: `feat/008-multi-tenancy-request-context`  
**Spec**: `specs/008-multi-tenancy-request-context/spec.md`

## Summary

Introduce shared-table multi-tenancy as a first-class security boundary. The final architecture adds Tenant and TenantMembership persistence, moves role authority from global AccessProfile to tenant-local membership, requires server-validated tenant RequestContext for Customer/Opportunity/Audit paths, scopes repositories and audit by tenant, exposes session membership discovery, and makes tenant selection explicit in web URLs and TanStack Query cache keys.

Tenant selection is stateless: `/t/:tenantSlug/...` is visible navigation state; a tenant-bound HTTP transport sends `X-Tenant-Id`; the API treats that header only as a selector and revalidates tenant + membership on every protected request.

## Technical Context

- **Frontend**: React 19 + Vite + TypeScript strict + TanStack Router/Query/Table + RHF/Zod.
- **Backend**: Fastify 5 modular monolith.
- **Persistence**: PostgreSQL 17 + Prisma 7.10.0 behind repositories.
- **Authentication**: Better Auth identity/session only.
- **Authorization**: project-owned Principal/capability policy; membership role is the final tenant-local authority.
- **Audit**: durable append-only PostgreSQL audit from feature 006.
- **Workflow**: explicit Opportunity commands from feature 007.
- **Testing**: Vitest, Fastify inject, PostgreSQL integration, Storybook/axe, Playwright.

No unresolved `NEEDS CLARIFICATION` items remain.

## Constitution Check — Pre-design

- **Spec before implementation**: PASS. PR #14 is design-only.
- **Backend-agnostic frontend**: PASS. Browser consumes shared tenant/session contracts and owned transport.
- **Server-authoritative authorization**: PASS. Tenant selector is never authority; membership is request-time validated.
- **Strict types/tests/CI**: PASS. Tenant becomes required at protected repository/query boundaries and two-tenant PostgreSQL tests are blocking gates.
- **Simplicity/evolvability**: PASS. No tenancy framework, hidden active-tenant session state, extra service, queue, or cache is introduced.

## Final Request Architecture

```text
Browser URL /t/:tenantSlug/...
         ↓
Session discovery (/api/session)
         ↓ slug must match active membership
canonical tenant id
         ↓
Tenant-bound transport adds X-Tenant-Id
         ↓
Fastify tenant RequestContext resolver
  1. authenticate Better Auth session
  2. enforce global AccessProfile.status
  3. require selector
  4. load active Tenant
  5. load active TenantMembership(user, tenant)
  6. derive membership role/capabilities
         ↓
RequestContext { tenant, principal }
         ↓
capability guard
         ↓
tenant-scoped repository / mutation service
         ↓
PostgreSQL tenant_id predicates + constraints
```

The raw header is never passed downstream as trusted context; repositories receive validated RequestContext/TenantScope.

## Merge-Safe Rollout Strategy

The final tenant boundary changes both server contracts and browser routing. Landing a server-only breaking change would make the existing web client fail every Customer/Opportunity request; landing tenant-looking routes before server isolation would be worse because the UI could imply security that does not exist.

We therefore use two merge-safe implementation slices rather than a feature flag or permissive fallback.

### 008A — additive foundation (#15)

008A may be merged without changing existing domain behavior:

- add shared **new** tenant DTO/value types without removing legacy SessionResponse yet;
- add Tenant/TenantMembership persistence and backfill memberships from current AccessProfile roles;
- keep AccessProfile.role temporarily only as backward-compatibility authority for the existing unscoped application path;
- add TenantMembership repository and request-time tenant resolver;
- add `/api/session/context` as an additive endpoint;
- test tenant/membership/revocation semantics independently;
- do **not** add required tenant ownership to Customer/Opportunity/Audit yet;
- do **not** require `X-Tenant-Id` on existing domain routes yet;
- do **not** change browser routes in #15.

This is a deliberate migration bridge, not the final authorization model. No new tenant-looking domain UX is exposed in this phase.

### 008B — atomic activation vertical slice (#16)

008B switches the product to the final model in one green MR:

- change `/api/session` to identity + membership discovery;
- remove AccessProfile.role authority/column;
- migrate/backfill mandatory tenant ownership on Customer/Opportunity/Audit;
- make repository TenantScope required and activate domain enforcement;
- derive all mutation/audit ownership from RequestContext;
- add tenant-prefixed browser routes, tenant-bound transport, tenant query keys, scoped Principal, visible switcher and demo isolation;
- update all existing browser journeys to tenant-aware URLs/transport;
- run the full two-tenant PostgreSQL + browser security matrix.

There is no interval after #16 merge where the UI shows tenant boundaries while the API remains global, or where the API requires tenant context the shipped web cannot provide.

### 008C — convergence only if needed (#17)

Create a third implementation MR only if post-activation analyze/converge finds a material security/migration/accessibility gap. Do not create an empty process-only MR.

## Session Model — Final State

### Global discovery

`GET /api/session` authenticates Better Auth, enforces global AccessProfile active status, and returns identity + active TenantMembership summaries. It no longer manufactures a global role.

### Tenant context

`GET /api/session/context` + `X-Tenant-Id` revalidates Tenant/TenantMembership and returns Tenant + tenant-local Principal. Protected domain routes use the same resolver directly.

During additive #15, the existing `/api/session` response remains unchanged solely to keep current master behavior green; `/api/session/context` is already available and tested. #16 removes that compatibility state.

## Persistence — Final State

Final target:

1. Tenant/TenantMembership exist and membership role is authoritative;
2. Customer/Opportunity/AuditEvent have non-null tenant ownership;
3. Customer uniqueness is `(tenantId,email)`;
4. tenant-leading indexes support scoped queries;
5. AccessProfile contains global status only.

### Migration A (#15)

- create TenantStatus/MembershipStatus;
- create Tenant/TenantMembership;
- insert deterministic reference tenant;
- backfill one membership per existing AccessProfile using existing role;
- retain AccessProfile.role temporarily;
- add deterministic Alpha/Beta/disabled reference fixtures through explicit seed.

### Migration B (#16)

- add nullable tenant ids to Customer/Opportunity/AuditEvent;
- backfill legacy rows to the reference tenant;
- change Customer unique index to `(tenantId,email)`;
- add tenant-leading Customer/Opportunity/Audit indexes;
- make tenant ownership non-null;
- update code to membership-only role authority;
- drop AccessProfile.role.

This two-migration rollout is intentional because each merged commit remains executable with its matching web client.

## Repository Boundary — Final State

```ts
type TenantScope = { tenantId: string }
```

Every tenant-owned repository method requires it:

```ts
customerRepository.list(scope, params)
customerRepository.get(scope, id)
customerRepository.create(scope, input)
opportunityRepository.get(scope, id)
opportunityWorkflow.transition(context, id, input)
auditRepository.list(scope, filters)
```

Prisma detail/update/delete/CAS predicates include tenant id rather than loading globally and checking afterwards.

This is the primary reference isolation boundary. PostgreSQL RLS is deferred as future defense in depth and may never justify unscoped repository APIs.

## Domain Mutation and Audit — Final State

Customer and Opportunity mutation services receive RequestContext. `context.tenant.id` supplies both domain ownership and AuditEvent tenant id inside one transaction. Client ownership fields are not admitted.

Cross-tenant ids resolve as normal not-found because current tenant id is part of the persistence predicate.

## Authorization Model — Final State

```text
Global AccessProfile.status
        ↓ active?
TenantMembership.role
        ↓
capabilitiesForRole(role)
        ↓
Principal
```

The same User can be Manager in Alpha and Viewer in Beta without multiple Better Auth identities or sessions. No global super-admin bypass is introduced.

## Frontend Architecture — Final State

### Routing

```text
/tenants
/t/$tenantSlug/customers
/t/$tenantSlug/customers/new
/t/$tenantSlug/customers/$customerId
/t/$tenantSlug/customers/$customerId/edit
/t/$tenantSlug/opportunities
/t/$tenantSlug/opportunities/new
/t/$tenantSlug/opportunities/$opportunityId
```

After sign-in: one active membership may redirect deterministically to it; multiple/zero memberships use `/tenants`. Legacy unscoped domain URLs must not silently choose a hidden tenant.

### Tenant transport

One project-owned tenant-bound fetch adds `X-Tenant-Id` and is injected into HttpDataProvider, HttpOpportunityService, scoped session context, and future tenant-owned clients. Feature components never set the header.

### Cache isolation

Customer/Opportunity query keys include canonical tenant id. Correctness depends on namespaced keys; imperative invalidation is only defense in depth.

### Authorization provider

Global SessionProvider owns identity/membership discovery. The tenant route boundary resolves `/api/session/context` and provides the returned tenant-local Principal to AuthorizationProvider.

### Shell

The current tenant is always visible. Switching navigates to another `/t/:slug/...` URL; it does not mutate hidden server session state.

## Demo Mode

Demo auth/data models deterministic Alpha/Beta memberships and datasets. Demo isolation exercises UX/contracts, but real HTTP/PostgreSQL E2E remains the security proof.

## Testing Strategy

### 008A additive foundation

- migration/backfill of Tenant/TenantMembership;
- active discovery filtering in repository;
- context resolution for valid/invalid/disabled/non-member tenants;
- same identity different membership roles;
- membership/tenant revocation reflected on next context request;
- global AccessProfile disablement still blocks context;
- existing unscoped web/browser behavior remains green because activation has not occurred.

### 008B activation

- every Customer/Opportunity repository operation tenant-scoped;
- cross-tenant id read/update/delete/workflow returns not-found and never mutates;
- same customer email allowed across tenants, rejected within one tenant;
- Opportunity CAS contains tenant scope;
- domain/audit tenant ids identical and atomic;
- audit reads tenant-scoped;
- session discovery final contract;
- tenant-bound transport and query-key architecture tests;
- browser switch changes URL/data/capabilities without stale cache;
- membership/tenant revocation blocks next tenant-owned request;
- full auth/customer/opportunity/audit/telemetry regression.

## Delivery Slices / MR Policy

### PR #14 — Design only
Spec/checklist/research/data model/contracts/plan/tasks/analyze/ADR-0016. No production code.

### New PR #15 — 008A additive tenant identity foundation
Tenant/TenantMembership persistence/backfill, membership repository, additive tenant context endpoint/resolver, tests, existing regression green. No domain tenancy activation.

### New PR #16 — 008B tenant isolation activation
Mandatory domain ownership + repository scoping + membership-only role authority + final session discovery + web tenant routes/transport/query keys/switcher/demo + full isolation E2E.

### Optional new PR #17 — 008C convergence hardening
Only when final convergence discovers material uncovered work.

## Complexity Tracking

No constitution exception is requested. The temporary AccessProfile.role compatibility column exists only across the #15→#16 migration boundary and is never introduced as a second *new* role source. #15 does not expose tenant-scoped domain UX, and #16 removes the compatibility state atomically with activation.

RLS is deferred deliberately. If introduced later it must use transaction-local context, a non-bypass request role, pooling/reuse tests, and schema-derived RLS coverage while retaining application TenantScope.

## Constitution Check — Post-design

PASS. The final design makes tenant authority server-derived and repository-scoped, while the revised rollout ensures every independently merged MR remains executable and does not require a temporary authorization bypass or misleading tenant UI.
