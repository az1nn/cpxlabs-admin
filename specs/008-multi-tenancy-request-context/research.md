# Research: Multi-Tenancy and Request Isolation

## Decision 1 — Tenant identifiers are selectors, never authorization proof

The browser may select a tenant, but every tenant-scoped request must bind that selection to the currently authenticated identity and an active membership before domain code executes. This matches OWASP multi-tenant guidance: client-supplied tenant identifiers are selectors and must be verified against server-side membership/authorization.

**Decision**: use a project-owned `X-Tenant-Id` request header for tenant-scoped API calls. The server resolves the authenticated identity first, then validates active Tenant + active TenantMembership, then constructs RequestContext. No body/query `tenantId` can establish ownership.

**Rejected**: trusting a tenant header because it came from an authenticated browser; encoding tenant authority only in frontend state; deriving ownership from mutation payloads.

## Decision 2 — Tenant selection is visible and stateless

The canonical web route shape is:

```text
/t/:tenantSlug/customers
/t/:tenantSlug/customers/:id
/t/:tenantSlug/opportunities
/t/:tenantSlug/opportunities/:id
```

The slug is operator-visible routing state. The browser maps the slug to an active membership discovered from the server and sends that membership's canonical tenant id through the owned HTTP transport.

No `activeTenant` cookie/database/session field is introduced in this feature. A URL and validated request header avoid hidden cross-tab state, make deep links understandable, and prevent a stale server-side "last tenant" from changing the meaning of a visible URL.

## Decision 3 — Split identity discovery from tenant-scoped Principal resolution

`GET /api/session` remains unscoped and becomes identity/membership discovery. It returns the authenticated identity plus active selectable tenant memberships.

`GET /api/session/context` is tenant-scoped and requires `X-Tenant-Id`. It returns the current Tenant plus a server-derived Principal whose role/capabilities come from that membership.

This preserves one global authentication session while making authorization tenant-local and request-time validated.

## Decision 4 — Global AccessProfile is an application kill switch, not a role source

Existing `AccessProfile.status` remains the global application enable/disable authority. Its role stops being authoritative and is removed from the reference persistence model after membership backfill. `TenantMembership.role` is the sole role source for tenant-scoped operations.

This prevents two competing role authorities.

## Decision 5 — Shared-table PostgreSQL with mandatory tenant ownership

Tenant-owned tables use mandatory `tenant_id` and composite/indexed access patterns. Customer, Opportunity, and tenant-owned AuditEvent records become non-null tenant-owned rows.

All repository contracts require tenant scope. Prisma queries include tenant scope in list and id lookups; cross-tenant resource ids therefore naturally resolve as not-found.

### RLS consideration

PostgreSQL Row-Level Security can provide strong defense in depth and defaults to deny when RLS is enabled without a matching policy. OWASP also recommends RLS as one viable shared-table isolation control when the ordinary request role cannot bypass it and tenant context is transaction-local.

RLS is **not** the primary isolation mechanism in 008. The current Prisma/pool architecture would require disciplined transaction-local database context for every request path, special request-path database roles, and connection-reuse verification. Introducing those mechanics simultaneously with the first tenant model would materially increase complexity and create a second implicit tenant context.

The reference gate therefore uses explicit RequestContext + mandatory repository scope + database ownership constraints/tests. RLS remains a future defense-in-depth specification, not an excuse for unscoped repository APIs.

## Decision 6 — Tenant-local uniqueness

Customer email uniqueness changes from global `email` uniqueness to `(tenant_id, email)`. The same external person/company identifier may legitimately exist in separate organizations.

Tenant slug remains globally unique because it is a routing/discovery identifier in the reference deployment.

## Decision 7 — Tenant is part of every remote cache identity

OWASP recommends including tenant identity in tenant-scoped cache keys. TanStack Query keys therefore include canonical tenant id for Customer and Opportunity list/detail state. Tenant switch either changes keys naturally or invalidates tenant-owned queries before rendering the new route.

No query key containing tenant-owned data may remain globally keyed only by resource/id.

## Decision 8 — Cross-tenant probing returns not-found after membership validation

There are two distinct failures:

1. caller is not allowed to enter the selected tenant → stable tenant-access denial;
2. caller is valid in Tenant A but requests an id owned by Tenant B → normal `not_found`.

This avoids revealing the existence of foreign resources while preserving clear feedback for invalid tenant selection.

## Decision 9 — Migration backfills a reference tenant before constraints become non-null

The reference migration must preserve existing starter data:

1. create Tenant/TenantMembership structures;
2. create a deterministic reference tenant;
3. backfill memberships from current AccessProfile roles;
4. add nullable tenant ids to Customer/Opportunity/AuditEvent;
5. backfill existing rows to the reference tenant;
6. replace Customer global email unique index with tenant-local unique constraint;
7. make tenant ownership non-null;
8. stop/remove the global AccessProfile role source.

Seed logic then creates at least two deterministic tenants and a cross-role user fixture for isolation tests.

## Decision 10 — Audit and telemetry consume only verified RequestContext

Domain audit receives tenant id from the already validated RequestContext and persists it in the same transaction as the domain mutation. Audit reads require the same tenant scope.

Operational/security telemetry may attach the verified stable tenant id as metadata, but never uses raw tenant request input and never includes authentication/session secrets.

## Primary references

- OWASP Multi Tenant Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html
- OWASP Authorization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- PostgreSQL 17 Row Security Policies: https://www.postgresql.org/docs/17/ddl-rowsecurity.html
