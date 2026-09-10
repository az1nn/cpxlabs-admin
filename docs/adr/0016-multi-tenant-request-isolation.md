# ADR-0016: Server-Validated Tenant Request Context with Shared-Table Isolation

**Status**: Accepted  
**Date**: 2026-09-10

## Context

CPXLabs Admin now has authentication, tenant-agnostic role capabilities, Customer CRUD, Opportunity workflow, transactional audit, and request correlation. The next architecture gate must support multiple organizations without allowing tenant identity to become an unverified client attribute, hidden session state, UI-only filter, or optional repository concern.

The existing `RequestContext` already anticipates tenant context but the persisted domain is globally scoped: Customer and Opportunity have no tenant owner, Customer email is globally unique, AuditEvent tenant id is nullable, and AccessProfile currently carries one global role. This cannot express one identity with different privileges in different organizations and cannot provide durable cross-tenant isolation.

## Decision

We will use shared-table PostgreSQL tenancy with explicit server-validated RequestContext and mandatory repository scope.

### Identity and authorization

- Better Auth remains identity/session infrastructure only.
- AccessProfile remains the application-wide active/disabled switch.
- `TenantMembership` becomes the sole role source for tenant-owned operations.
- The same User may have different `admin`, `manager`, or `viewer` roles in different tenants.
- RequestContext contains a required validated Tenant plus a Principal derived from the active membership.

### Tenant selection

- Browser URLs use `/t/:tenantSlug/...` so operator context is visible/shareable.
- Tenant-owned API calls use `X-Tenant-Id` through one project-owned transport boundary.
- The header is only a selector. Authentication + global access + active Tenant + active membership are revalidated before tenant-owned handlers/repositories execute.
- We do not persist an `activeTenant` in Better Auth session, cookie, or database in this reference feature.

### Persistence

- Customer and Opportunity receive mandatory `tenant_id`.
- Customer uniqueness becomes `(tenant_id, email)`.
- AuditEvent tenant ownership becomes mandatory for Customer/Opportunity domain audit flows.
- Tenant-owned repository methods require `TenantScope`; Prisma predicates include tenant id for list/detail/mutation/workflow paths.
- Cross-tenant resource ids resolve as normal not-found after the selected tenant has been validated.
- Domain ownership and AuditEvent tenant id are derived only from RequestContext.

### Cache isolation

- TanStack Query keys for tenant-owned state include canonical tenant id.
- Router owns visible tenant slug state.
- Tenant switching changes query namespaces before tenant-owned data renders.

## Alternatives considered

### Trust a tenant header after login

Rejected. Authentication proves user identity, not membership in an arbitrary tenant supplied by the client.

### Store active tenant in the auth session

Rejected for the reference implementation. Hidden active-tenant state complicates deep links, multiple tabs, switching, revocation, and makes visible URL context less authoritative to the operator. Stateless URL/header selection with request-time validation is simpler.

### Schema-per-tenant or database-per-tenant

Rejected for the reference starter because it adds provisioning, migration, connection-pool, and operational complexity not required to prove isolation. These models remain valid for stronger regulatory/physical-isolation requirements.

### PostgreSQL Row-Level Security as the first isolation authority

Deferred, not rejected. RLS can provide valuable defense in depth, but the current Prisma/connection-pool path would require transaction-local tenant settings, a non-superuser/non-BYPASSRLS request role, connection-reuse verification, and RLS policy coverage for every tenant-owned table. Introducing this simultaneously with the first tenant model creates a second implicit context and materially increases the first migration's risk.

The application must therefore remain correct with explicit mandatory repository scope. A future RLS feature may add defense in depth without weakening those contracts.

## Consequences

### Positive

- tenant authority is server-derived and request-time current;
- one auth identity can hold different roles per organization;
- cross-tenant data access is constrained at repository/database predicates, not UI filtering;
- tenant context is visible in URLs and deterministic across tabs/deep links;
- cache identities cannot accidentally collide across tenants when contracts are followed;
- existing Better Auth, capability, audit, Prisma and Fastify boundaries remain replaceable;
- future RLS can be layered underneath the same RequestContext/TenantScope design.

### Costs

- every tenant-owned repository method gains explicit TenantScope;
- existing data requires a careful reference-tenant backfill migration;
- all current browser routes/tests must become tenant-aware;
- session handling splits identity discovery from tenant-scoped Principal resolution;
- future tenant-owned modules must classify their storage/cache/audit ownership explicitly.

## Security invariants

1. Client tenant ids are selectors, never authorization proof.
2. Missing or invalid tenant context fails closed.
3. TenantMembership is revalidated on every protected tenant-scoped request.
4. Tenant-owned repository operations cannot be invoked without TenantScope.
5. Cross-tenant id probing cannot reveal/mutate foreign tenant rows.
6. Required domain audit tenant id equals the verified RequestContext tenant.
7. Tenant-owned cache keys include tenant identity.
8. No global super-admin bypass exists in this reference feature.

## References

- `specs/008-multi-tenancy-request-context/`
- OWASP Multi Tenant Security Cheat Sheet
- OWASP Authorization Cheat Sheet
- PostgreSQL Row Security Policies
