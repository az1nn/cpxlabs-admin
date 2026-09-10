# Implementation Plan: Multi-Tenancy and Request Isolation

**Branch**: `feat/008-multi-tenancy-request-context`  
**Spec**: `specs/008-multi-tenancy-request-context/spec.md`

## Summary

Introduce shared-table multi-tenancy as a first-class security boundary. The implementation adds Tenant and TenantMembership persistence, moves role authority from global AccessProfile to tenant-local membership, requires server-validated tenant RequestContext for Customer/Opportunity/Audit paths, scopes repositories and audit by tenant, exposes session membership discovery, and makes tenant selection explicit in web URLs and TanStack Query cache keys.

The design deliberately keeps tenant selection stateless: `/t/:tenantSlug/...` is visible navigation state; a tenant-bound HTTP transport sends `X-Tenant-Id`; the API treats that header only as a selector and revalidates tenant + membership on every request.

## Technical Context

- **Frontend**: React 19 + Vite + TypeScript strict + TanStack Router/Query/Table + RHF/Zod.
- **Backend**: Fastify 5 modular monolith.
- **Persistence**: PostgreSQL 17 + Prisma 7.10.0 behind repositories.
- **Authentication**: Better Auth identity/session only.
- **Authorization**: project-owned Principal/capability policy; membership role is tenant-local authority.
- **Audit**: durable append-only PostgreSQL audit from feature 006.
- **Workflow**: explicit Opportunity commands from feature 007.
- **Testing**: Vitest, Fastify inject, PostgreSQL integration, Storybook/axe, Playwright.

No unresolved `NEEDS CLARIFICATION` items remain.

## Constitution Check — Pre-design

### I. Spec before implementation
PASS. PR #14 is design-only and freezes specify/clarify/plan/tasks/analyze before production code begins.

### II. Backend-agnostic frontend
PASS. The browser consumes shared tenant/session contracts and an owned tenant transport. Prisma/Fastify membership internals do not cross the boundary.

### III. Server authority and typed authorization
PASS. Tenant selection is client-visible but never authoritative. Membership, role and capabilities are server-derived on every tenant-scoped RequestContext resolution.

### IV. Strict types/tests/CI
PASS. Tenant scope becomes a required type at repository and query-key boundaries. PostgreSQL cross-tenant tests are mandatory.

### V. Simplicity/evolvability
PASS. Shared-table ownership + explicit repository scoping is preferred over introducing a new tenancy framework, service, workflow, or hidden active-tenant session state.

## Request Architecture

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

The raw header is never passed down as trusted context; downstream code receives the validated RequestContext/TenantScope value.

## Session Model

### Global discovery

`GET /api/session`:

- authenticates the existing Better Auth session;
- enforces global AccessProfile active status;
- returns identity + active TenantMembership summaries;
- does not manufacture one global Principal role.

### Tenant context

`GET /api/session/context` + `X-Tenant-Id`:

- revalidates Tenant and TenantMembership;
- returns the selected Tenant plus tenant-local Principal;
- uses stable `TENANT_CONTEXT_REQUIRED` / `TENANT_ACCESS_DENIED` errors.

Protected tenant-owned routes use the same resolver directly and do not trust a previously fetched context response.

## Persistence Migration

One committed migration must preserve existing reference data safely:

1. add TenantStatus and MembershipStatus enums;
2. create Tenant and TenantMembership;
3. insert deterministic legacy/reference tenant;
4. backfill one membership per current AccessProfile using its existing role;
5. add nullable tenantId to Customer, Opportunity, AuditEvent;
6. backfill existing rows to reference tenant;
7. replace Customer global email unique with `(tenantId,email)` unique;
8. replace useful Customer/Opportunity indexes with tenant-leading indexes;
9. make tenant ownership non-null;
10. update application code to read role from membership only;
11. remove global AccessProfile role column so there is no second role authority.

The migration is schema/data migration only. Demo/reference fixtures beyond required backfill remain in explicit seed code.

## Repository Boundary

Introduce a stable required value:

```ts
type TenantScope = { tenantId: string }
```

Every tenant-owned repository method requires it. Examples:

```ts
customerRepository.list(scope, params)
customerRepository.get(scope, id)
customerRepository.create(scope, input)
opportunityRepository.get(scope, id)
opportunityWorkflow.transition(context, id, input)
auditRepository.list(scope, filters)
```

Prisma `get/update/delete` paths include tenant id in the database predicate, not a post-fetch ownership check.

This is the primary reference isolation boundary. PostgreSQL RLS is explicitly deferred as future defense in depth; it must not be used to justify unscoped application repository APIs.

## Domain Mutation and Audit

Customer and Opportunity mutation services receive full RequestContext. The validated `context.tenant.id` supplies both domain ownership and AuditEvent tenant id inside the same Prisma transaction.

For create:

```text
RequestContext tenant
   ├── record.tenantId
   └── audit.tenantId
```

No caller-provided ownership field is admitted to Customer/Opportunity create input contracts.

Cross-tenant ids resolve as not-found because repository/mutation predicates include current tenant id.

## Authorization Model

Current role-capability matrix stays unchanged, but role source changes:

```text
Global AccessProfile.status
        ↓ active?
TenantMembership.role
        ↓
capabilitiesForRole(role)
        ↓
Principal
```

The same User may therefore be:

```text
Alpha → manager
Beta  → viewer
```

without multiple Better Auth accounts or sessions.

No global super-admin bypass is introduced.

## Frontend Architecture

### Routing

Tenant-owned pages move under:

```text
/t/$tenantSlug/customers
/t/$tenantSlug/customers/new
/t/$tenantSlug/customers/$customerId
/t/$tenantSlug/customers/$customerId/edit
/t/$tenantSlug/opportunities
/t/$tenantSlug/opportunities/new
/t/$tenantSlug/opportunities/$opportunityId
```

`/tenants` is the deterministic selection surface for users with multiple memberships or no selected tenant. After sign-in:

- one active membership → redirect to its tenant home/resource route;
- multiple memberships → `/tenants`;
- zero memberships → `/tenants` with no-access state.

Legacy unscoped domain routes must not silently pick a hidden tenant; they redirect to tenant selection or an explicit sole membership only when deterministic.

### Tenant transport

Create one project-owned tenant-bound fetch/transport factory. It adds `X-Tenant-Id` to tenant-owned HTTP calls and is injected into:

- HttpDataProvider;
- HttpOpportunityService;
- tenant-scoped session context client;
- future tenant-owned services.

Feature components never set tenant headers directly.

### Cache isolation

Customer and Opportunity query keys include canonical tenant id. Tenant switch changes query namespaces before the new route renders. A defensive clear/invalidate of tenant-owned queries may supplement this, but correctness cannot depend solely on imperative invalidation.

### Authorization provider

The global SessionProvider owns identity + membership discovery. A tenant route boundary resolves `/api/session/context` and supplies the returned tenant-local Principal to AuthorizationProvider. No role is inferred from the discovery payload alone for protected operations.

### Shell

The shell visibly displays current tenant and provides a switcher over active memberships. Switching navigates to the corresponding `/t/:slug/...` route rather than mutating hidden session state.

## Demo Mode

Demo auth/session exposes deterministic Tenant Alpha and Tenant Beta memberships. Demo Customer and Opportunity services partition rows by canonical tenant id and use the same tenant-aware query-key/transport-facing interfaces where practical.

Demo isolation is for product usability/testing. It is never treated as proof of server security; HTTP E2E remains the security gate.

## Testing Strategy

### Contracts/unit

- membership→Principal role/capability mapping;
- tenant route parsing/membership matching;
- tenant-bound fetch header injection;
- tenant included in all resource query keys;
- demo datasets isolated;
- missing/invalid selector error mapping.

### API/Fastify

- missing tenant context;
- invalid/disabled/non-member tenant generic denial;
- same user manager in Alpha/viewer in Beta;
- global disabled AccessProfile blocks both;
- membership disabled blocks only its tenant;
- session discovery excludes inactive membership/tenant;
- context route revalidates membership each request.

### PostgreSQL isolation

For Customer and Opportunity:

- list only current tenant;
- same id probing in foreign tenant resolves not-found;
- create ownership server-derived;
- update/delete/workflow cannot cross tenant;
- same customer email allowed across tenants, rejected within tenant;
- Opportunity CAS remains tenant-scoped;
- failed cross-tenant operations append zero audit;
- committed audit tenant id correct/non-null;
- audit list cannot cross tenant.

### Browser

- sign-in → tenant selection;
- current tenant visibly shown;
- switch changes URL, role controls and datasets;
- query cache never displays prior-tenant records;
- Manager in Alpha can mutate; same identity Viewer in Beta cannot;
- revoked membership/disabled tenant fails on next request;
- existing auth/customer/opportunity journeys updated to tenant URLs.

## Delivery Slices / MR Policy

### PR #14 — 008 Design only

- spec/checklist;
- research;
- data model;
- session/transport contract;
- plan;
- tasks;
- analysis;
- ADR-0016.

No production code.

### New PR #15 — 008A Backend isolation

- shared contracts;
- Prisma migration/backfill;
- Tenant/TenantMembership repositories;
- session discovery/context resolver;
- RequestContext required tenant;
- Customer/Opportunity/Audit repository scoping;
- mutation/audit atomic tenant ownership;
- PostgreSQL/API isolation gates.

### New PR #16 — 008B Web tenancy

- tenant discovery/session provider changes;
- tenant route tree;
- tenant-bound transport;
- tenant-aware DataProvider/OpportunityService wiring;
- query-key isolation;
- tenant selector/shell;
- demo tenant behavior;
- browser/a11y gates.

### Optional new PR #17 — 008C convergence

Only create if analyze/converge after 008B discovers material uncovered security or migration work. Do not create an empty process-only PR.

## Complexity Tracking

No constitution exception is requested. Explicit repository scoping duplicates a small `TenantScope` parameter across repositories by design; this duplication is preferable to hidden global context or an early bespoke tenancy framework.

RLS is deferred deliberately. If later introduced, it must be additive defense in depth with transaction-local tenant context, a non-bypass request role, pooling tests, and schema-derived RLS coverage gates.

## Constitution Check — Post-design

PASS. The plan makes tenant authority server-derived, scopes data at repository/database predicates, keeps browser state explicit in Router/Query, retains Better Auth and Prisma behind owned boundaries, adds no new infrastructure service, and strengthens rather than weakens existing auth/audit/CI guarantees.
