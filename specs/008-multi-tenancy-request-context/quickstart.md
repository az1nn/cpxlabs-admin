# Quickstart: Implementing Multi-Tenant Request Isolation

This feature is delivered in separate MRs. PR #14 contains design only. Do not add production tenancy code to the design branch.

## 008A backend implementation order

1. Add tenant/session DTOs and `TenantScope` contracts.
2. Add Tenant/TenantMembership Prisma models and tenant ownership columns.
3. Create the migration with deterministic legacy/reference backfill before applying NOT NULL constraints.
4. Move role authority from AccessProfile to TenantMembership; keep AccessProfile status global.
5. Implement TenantMembership repository/session discovery.
6. Split global session discovery from tenant-scoped RequestContext resolution.
7. Require TenantScope in Customer, Opportunity, Audit repositories.
8. Derive mutation/audit tenant ownership from RequestContext only.
9. Add two-tenant PostgreSQL isolation fixtures and tests.
10. Run all existing auth/audit/workflow gates before freezing the backend MR.

## 008B web implementation order

1. Update SessionProvider to hold identity + active membership discovery rather than one global Principal.
2. Add `/tenants` selection state and `/t/$tenantSlug/...` route tree.
3. Resolve the URL slug against discovered memberships and fetch `/api/session/context`.
4. Supply scoped Principal to AuthorizationProvider inside the tenant route boundary.
5. Create one tenant-bound HTTP transport that injects `X-Tenant-Id`.
6. Bind HttpDataProvider and HttpOpportunityService through that transport.
7. Include tenant id in Customer/Opportunity query keys.
8. Add visible tenant label/switcher to the shell.
9. Model deterministic Alpha/Beta tenants in demo mode.
10. Update Playwright auth/customer/opportunity journeys to tenant routes and add tenant-switch isolation coverage.

## Reference request flow

```text
GET /api/session
  -> identity + memberships

URL /t/alpha/customers
  -> resolve slug alpha to ten_alpha from discovery

GET /api/session/context
X-Tenant-Id: ten_alpha
  -> server revalidates active Tenant + active membership
  -> returns tenant + tenant-local Principal

GET /api/customers
X-Tenant-Id: ten_alpha
  -> same resolver runs again
  -> repository receives TenantScope { tenantId: ten_alpha }
```

## Required test fixtures

At minimum, seed/reference tests need:

```text
Tenant Alpha (active)
Tenant Beta  (active)
Tenant Disabled (disabled)

Multi-role user:
  Alpha -> manager
  Beta  -> viewer

Admin user:
  Alpha -> admin
  Beta  -> admin

Viewer user:
  Alpha -> viewer
```

Create similarly named Customer/Opportunity rows in Alpha and Beta so list/cache leakage is visually obvious.

## Required attack/regression checks

- no tenant header → fail closed;
- random/non-member/disabled tenant header → generic tenant access denial;
- Alpha context + Beta resource id → `not_found`;
- client body containing Beta tenant id while Alpha context active → cannot set ownership;
- Alpha manager mutation succeeds; same identity in Beta viewer context is forbidden;
- membership disabled after login → next request denied;
- tenant disabled after login → next request denied;
- Alpha customer/opportunity never renders after switch to Beta;
- same customer email may exist once in Alpha and once in Beta;
- AuditEvent tenant id always matches verified RequestContext for successful domain mutations.

## Local validation

After 008A introduces the migration:

```bash
docker compose up -d postgres
cp apps/api/.env.example apps/api/.env
pnpm --filter @cpxlabs-admin/api db:migrate
pnpm --filter @cpxlabs-admin/api db:seed
pnpm typecheck
pnpm test
pnpm build
```

Then run the browser gates after 008B:

```bash
pnpm --filter @cpxlabs-admin/storybook test:stories
pnpm --filter @cpxlabs-admin/web e2e
```

CI remains the authoritative full PostgreSQL + browser gate.
