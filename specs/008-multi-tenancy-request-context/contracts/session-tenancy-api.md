# Contract: Tenant Session Discovery and Request Context

## Tenant transport

Every tenant-owned API request carries exactly one selector header:

```http
X-Tenant-Id: <canonical tenant id>
```

The header is **not authorization proof**. The API must authenticate the user, verify global application access, load the selected active tenant, verify active membership, derive membership role/capabilities, and only then create RequestContext.

Client-supplied tenant ids/slugs in request bodies or domain query parameters are not accepted as ownership fields.

## `GET /api/session`

Purpose: global authenticated identity + active membership discovery. No tenant header is required.

### 200

```json
{
  "identity": {
    "id": "usr_123",
    "email": "operator@example.com",
    "name": "Operator"
  },
  "tenants": [
    {
      "tenant": {
        "id": "ten_alpha",
        "slug": "alpha",
        "name": "Alpha"
      },
      "role": "manager"
    },
    {
      "tenant": {
        "id": "ten_beta",
        "slug": "beta",
        "name": "Beta"
      },
      "role": "viewer"
    }
  ]
}
```

Only active memberships whose Tenant is active are returned. A globally disabled AccessProfile still returns `403 ACCESS_DISABLED` as today.

This response enables tenant selection but is not the authorization source for later domain requests; membership is revalidated request-time.

## `GET /api/session/context`

Purpose: resolve the selected tenant into the canonical tenant-scoped Principal used by the web application.

Required header:

```http
X-Tenant-Id: ten_alpha
```

### 200

```json
{
  "tenant": {
    "id": "ten_alpha",
    "slug": "alpha",
    "name": "Alpha"
  },
  "principal": {
    "id": "usr_123",
    "email": "operator@example.com",
    "name": "Operator",
    "role": "manager",
    "capabilities": [
      "customers.read",
      "customers.create",
      "customers.update",
      "opportunities.read",
      "opportunities.create",
      "opportunities.transition"
    ]
  }
}
```

The capability list is generated from the current active membership role on every resolution.

## Stable tenant-context errors

### Missing tenant selector

HTTP `400`:

```json
{
  "error": {
    "code": "TENANT_CONTEXT_REQUIRED",
    "message": "A tenant context is required",
    "requestId": "..."
  }
}
```

### Invalid, disabled, or unauthorized tenant selector

HTTP `403`:

```json
{
  "error": {
    "code": "TENANT_ACCESS_DENIED",
    "message": "Tenant access is not available",
    "requestId": "..."
  }
}
```

The same public error is used for nonexistent, disabled, or non-member tenant selection so the API does not provide a tenant-enumeration oracle.

Global `401 AUTHENTICATION_REQUIRED` and `403 ACCESS_DISABLED` retain their existing meaning and occur before tenant-local authorization.

## Cross-tenant resource semantics

After a valid Tenant A RequestContext exists, asking for a resource id owned by Tenant B returns the ordinary resource `404 not_found` envelope. It must not return `TENANT_ACCESS_DENIED`, because the caller is valid in Tenant A and the foreign resource is outside the scoped repository result set.

## Tenant-owned domain APIs

The existing Customer, Opportunity, and Audit URLs remain API-resource relative:

```text
/api/customers
/api/customers/:id
/api/opportunities
/api/opportunities/:id
/api/opportunities/:id/commands/transition
/api/audit-events
```

They all require `X-Tenant-Id`. Tenant identity does not need to be duplicated in every API path because the project-owned transport boundary supplies it consistently and Fastify resolves it before handlers execute.

The browser URL is independently explicit:

```text
/t/:tenantSlug/customers
/t/:tenantSlug/customers/:id
/t/:tenantSlug/opportunities
/t/:tenantSlug/opportunities/:id
```

## Web transport boundary

The web application binds an HTTP client/provider to one validated membership:

```text
Tenant route slug
    ↓ resolve against session discovery
canonical tenant id
    ↓
TenantTransport / tenant-bound fetch
    ├── HttpDataProvider
    └── HttpOpportunityService
```

All tenant-owned clients receive the same bound fetch/transport. No feature component manually sets `X-Tenant-Id`.

## Cache contract

All Customer and Opportunity TanStack Query keys must include canonical tenant id before any resource/list/detail identity. Examples:

```text
['tenant', tenantId, 'customers', 'list', params]
['tenant', tenantId, 'customers', 'detail', customerId]
['tenant', tenantId, 'opportunities', 'list', params]
['tenant', tenantId, 'opportunities', 'detail', opportunityId]
```

Audit query keys, when surfaced in web UI later, follow the same rule.
