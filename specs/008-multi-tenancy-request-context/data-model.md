# Data Model: Multi-Tenancy and Request Isolation

## Tenant

```text
Tenant
  id        String         PK
  slug      String         UNIQUE, stable route identifier
  name      String
  status    TenantStatus   active | disabled
  createdAt DateTime
  updatedAt DateTime
```

Indexes: unique `slug`; status index only if later operational queries justify it.

## TenantMembership

```text
TenantMembership
  id        String             PK
  tenantId  String             FK -> Tenant
  userId    String             FK -> User
  role      ApplicationRole    admin | manager | viewer
  status    MembershipStatus   active | disabled
  createdAt DateTime
  updatedAt DateTime
```

Constraints/indexes:

- UNIQUE `(tenantId, userId)`;
- index `(userId, status)` for session discovery;
- index `(tenantId, status)` for tenant membership operations/tests.

Membership role is the sole tenant-local role authority.

## AccessProfile

Target reference shape:

```text
AccessProfile
  id        String        PK
  userId    String        UNIQUE FK -> User
  status    AccessStatus  active | disabled
  createdAt DateTime
  updatedAt DateTime
```

The existing global `role` column is migrated into TenantMembership during backfill and then removed from authorization authority. The implementation should remove the persistence column in the same feature once all code reads membership role, avoiding a durable dual-source state.

## Customer

Target changes:

```text
Customer
  tenantId  String  NOT NULL FK -> Tenant
  ...existing fields

UNIQUE (tenantId, email)
INDEX  (tenantId, name)
INDEX  (tenantId, status)
```

The former global unique email constraint is removed.

Every repository operation receives mandatory TenantScope and queries by tenant. Detail/update/delete use both tenant id and resource id rather than loading by id and checking ownership afterwards.

## Opportunity

Target changes:

```text
Opportunity
  tenantId  String  NOT NULL FK -> Tenant
  ...existing fields

INDEX (tenantId, stage)
INDEX (tenantId, expectedCloseDate)
INDEX (tenantId, updatedAt)
INDEX (tenantId, accountName)
```

Workflow compare-and-swap becomes tenant-aware:

```text
WHERE tenant_id = context.tenant.id
  AND id = :opportunityId
  AND version = :expectedVersion
```

The state-machine rules remain unchanged.

## AuditEvent

The existing nullable `tenantId` becomes mandatory for tenant-owned Customer/Opportunity domain audit rows in the reference application.

```text
AuditEvent
  tenantId String NOT NULL FK/logical reference -> Tenant
  ...existing fields

INDEX (tenantId, occurredAt, id)
INDEX (tenantId, subjectType, subjectId, occurredAt)
INDEX (tenantId, actorId, occurredAt)
```

Audit snapshots remain resource-specific allowlists. Tenant id is metadata supplied by verified RequestContext, not copied from a request body.

A physical FK from historical audit to Tenant is optional; preserving audit evidence across future tenant deletion may favor no cascade. Feature 008 does not implement tenant deletion, so the implementation plan should use restrictive/no-cascade semantics if a FK is introduced.

## Application value objects

### TenantContext

```ts
{
  id: string
  slug: string
  name: string
}
```

Only active, membership-validated tenants become TenantContext.

### TenantScope

Repository boundary value:

```ts
{ tenantId: string }
```

It is mandatory, never optional. It contains only the canonical persistence/security id, not user-controlled slug text.

### Principal

Existing shape remains conceptually stable:

```text
Principal
  id
  email
  name
  role
  capabilities
```

But `role` and `capabilities` are now derived from the validated TenantMembership for the current RequestContext. A Principal used for tenant-owned operations is therefore tenant-contextual rather than global.

### RequestContext

Target shape:

```text
RequestContext
  principal: Principal
  tenant: TenantContext
```

`tenant` is required for protected tenant-owned domain requests. Authentication-only/global discovery routes use a separate identity/session resolver rather than manufacturing an optional tenant.

## Session discovery DTOs

```text
SessionIdentityDto
  id
  email
  name

TenantSummaryDto
  id
  slug
  name

TenantMembershipSummaryDto
  tenant: TenantSummaryDto
  role: ApplicationRole

SessionDiscoveryResponse
  identity: SessionIdentityDto
  tenants: TenantMembershipSummaryDto[]

TenantContextResponse
  tenant: TenantSummaryDto
  principal: SessionPrincipalDto
```

Only active tenants + active memberships appear in discovery. Request-time context resolution still revalidates them.

## Migration invariants

- no existing Customer/Opportunity/AuditEvent row is left without tenant ownership before NOT NULL is applied;
- reference data receives one deterministic legacy/reference tenant;
- existing AccessProfile role becomes the reference membership role during migration/backfill;
- disabled global profiles do not imply deleted/disabled memberships; global status remains a separate gate;
- customer duplicate emails across different tenants are legal after migration;
- duplicate emails inside one tenant remain rejected;
- no cross-tenant foreign key relationship is inferred from globally unique resource ids.
