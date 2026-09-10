# Feature Specification: Multi-Tenancy and Request Isolation

**Feature Branch**: `feat/008-multi-tenancy-request-context`

**Created**: 2026-09-10

**Status**: Ready for Implementation

**Input**: Add a reference multi-tenant architecture that makes tenant membership, tenant-scoped authorization, repository isolation, audit ownership, session discovery, and frontend tenant selection explicit without coupling tenancy to Better Auth or relying on UI filtering for security.

## Clarifications

- Tenant selection is explicit in browser URLs as `/t/:tenantSlug/...`; no hidden active-tenant session/cookie state is introduced.
- Tenant-scoped API calls use `X-Tenant-Id` only as a selector; the server validates active Tenant + active TenantMembership on every request.
- `GET /api/session` becomes global identity/membership discovery; `GET /api/session/context` resolves the selected tenant into a server-derived Principal.
- Global AccessProfile remains the application active/disabled gate; tenant-local role/capabilities come only from TenantMembership.
- Shared-table PostgreSQL with mandatory tenant ownership and mandatory repository scope is the reference isolation model. PostgreSQL RLS is deferred as additive defense in depth.
- Unauthorized/disabled/nonexistent tenant selection returns one generic tenant-access denial; cross-tenant resource ids within an otherwise valid tenant context return normal not-found.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Work Inside One Tenant Without Seeing Another Tenant's Data (Priority: P1)

As an authenticated user who belongs to multiple tenants, I can enter one tenant context and work with its customers and opportunities without seeing records owned by another tenant.

**Why this priority**: Data isolation is the defining security property of multi-tenancy. Tenant switching has no value if reads or writes can cross the boundary.

**Independent Test**: Seed two tenants with overlapping-looking data, sign in as a user who belongs to both, select Tenant A, and verify customer/opportunity list, detail, mutation and workflow operations cannot read or mutate Tenant B records.

**Acceptance Scenarios**:

1. **Given** an authenticated member of Tenant A and Tenant B, **When** Tenant A is the validated request context, **Then** customer and opportunity list queries return only Tenant A rows.
2. **Given** a Tenant B resource id, **When** it is requested while Tenant A is active, **Then** the API returns not-found and does not reveal that the resource exists in another tenant.
3. **Given** a Tenant B resource id, **When** an update/delete/workflow command is attempted while Tenant A is active, **Then** no Tenant B state or audit record changes.
4. **Given** a create request in Tenant A, **When** it succeeds, **Then** the created record and audit evidence are owned by Tenant A regardless of any tenant-shaped fields supplied by the client.

---

### User Story 2 - Resolve Role and Capabilities Per Tenant Membership (Priority: P1)

As a user whose responsibilities differ by tenant, I receive the role and capabilities of my membership in the current tenant rather than one global application role.

**Why this priority**: A global role is incompatible with real tenant boundaries; an operator may administer one organization while being read-only in another.

**Independent Test**: Give the same user Manager membership in Tenant A and Viewer membership in Tenant B; verify create/transition succeeds in A and is denied in B using the same authenticated identity/session.

**Acceptance Scenarios**:

1. **Given** a globally enabled user with Manager membership in Tenant A, **When** Tenant A context is resolved, **Then** the Principal contains Manager capabilities for Tenant A.
2. **Given** the same user with Viewer membership in Tenant B, **When** Tenant B context is resolved, **Then** the Principal contains Viewer capabilities for Tenant B.
3. **Given** an authenticated user without an active membership in a requested tenant, **When** tenant context is resolved, **Then** access is denied before any domain repository operation executes.
4. **Given** a globally disabled AccessProfile, **When** any tenant is requested, **Then** application access remains disabled regardless of tenant membership.

---

### User Story 3 - Discover and Switch Tenant Context Safely (Priority: P1)

As an authenticated multi-tenant user, I can discover the tenants I may access and switch between them through explicit application navigation so that the active tenant is visible, shareable, and never inferred from stale client cache.

**Why this priority**: Hidden or implicit tenant state creates dangerous operator mistakes and cache leaks. Tenant context must be obvious in navigation and request transport.

**Independent Test**: Sign in as a user with two memberships, navigate from a Tenant A URL to Tenant B, and verify route state, API requests, capability UI, customer/opportunity data and query cache all change to Tenant B without displaying Tenant A server state.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** session discovery is loaded, **Then** the response lists only active tenant memberships the user may select.
2. **Given** a selected tenant, **When** navigating customer/opportunity pages, **Then** the tenant slug remains explicit in the application URL.
3. **Given** a tenant switch, **When** the new tenant route becomes active, **Then** subsequent API requests identify the new tenant and TanStack Query does not reuse unscoped data from the previous tenant.
4. **Given** an invalid or unauthorized tenant slug, **When** the user navigates to it, **Then** a stable tenant-access error/selection experience is shown without rendering protected domain data.

---

### User Story 4 - Preserve Tenant Ownership in Durable Audit (Priority: P1)

As an auditor, I can prove which tenant owned every successful customer or opportunity mutation so that audit evidence cannot be confused across organizations.

**Why this priority**: Durable audit is already an application invariant; introducing tenancy without making audit tenant ownership mandatory would weaken that invariant.

**Independent Test**: Perform equivalent mutations in Tenant A and Tenant B and verify each audit row has exactly one non-null tenant id, tenant-scoped audit reads cannot cross boundaries, and correlation still matches the originating request.

**Acceptance Scenarios**:

1. **Given** a committed tenant-owned mutation, **When** its audit event is persisted, **Then** `tenantId` is non-null and equals the validated RequestContext tenant.
2. **Given** Tenant A audit read access, **When** audit history is queried, **Then** only Tenant A audit rows are visible.
3. **Given** a client payload containing a different tenant id, **When** a mutation succeeds, **Then** the audit and domain record still use the server-resolved tenant id.

---

### User Story 5 - Preserve Zero-Infrastructure Demo and Explicit Production Boundaries (Priority: P2)

As a starter adopter, I can still run the demo without PostgreSQL while the reference HTTP deployment demonstrates real tenant isolation.

**Why this priority**: The starter intentionally supports a lightweight demo path, but that path must not create a security bypass in HTTP/server mode.

**Independent Test**: Run demo mode with deterministic reference tenants and switch between them; separately run HTTP mode against PostgreSQL and verify server-side tenant enforcement remains mandatory.

**Acceptance Scenarios**:

1. **Given** demo mode, **When** the app starts, **Then** deterministic demo tenants/memberships allow the tenant navigation experience without external infrastructure.
2. **Given** HTTP/server-auth mode, **When** a tenant-scoped endpoint is called without a valid tenant context, **Then** the API fails closed.
3. **Given** HTTP/server-auth mode, **When** the client attempts to spoof tenant ownership in body/query data, **Then** the server ignores/rejects the spoofed ownership and uses only validated RequestContext.

### Edge Cases

- A user can be globally enabled but have zero active tenant memberships; authentication succeeds but no tenant-scoped domain access is available.
- A membership can be disabled independently from the global AccessProfile.
- The same user may have different roles in different tenants.
- Tenant slugs are unique and stable routing identifiers; tenant ids remain canonical persistence/security identifiers.
- Customer email uniqueness becomes tenant-local rather than global, allowing the same email value in two tenants.
- Resource ids remain globally unique, but repositories still require tenant scoping for every tenant-owned operation.
- Cross-tenant resource probing returns not-found after the caller's tenant membership is validated to reduce existence disclosure.
- Client-supplied tenant ids in mutation bodies never define ownership.
- A stale tenant URL after membership revocation must fail closed on the next server request.
- Query/cache keys that omit tenant identity are considered a correctness and confidentiality bug.
- Global platform/super-admin bypass is outside this reference feature.
- Tenant creation, billing, invitations, membership administration UI, custom domains and organization SSO are outside this feature.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST introduce a first-class Tenant with stable id, unique slug, display name, active/disabled status, created time and updated time.
- **FR-002**: The system MUST introduce TenantMembership linking exactly one user to one tenant with tenant-local `admin`, `manager`, or `viewer` role and active/disabled status.
- **FR-003**: A user MUST have at most one membership row per tenant.
- **FR-004**: Global AccessProfile status MUST remain authoritative for whether the authenticated identity may use the application at all.
- **FR-005**: Application role/capabilities MUST be resolved from the active TenantMembership rather than a global AccessProfile role.
- **FR-006**: RequestContext MUST contain one validated Tenant context for every tenant-scoped domain request.
- **FR-007**: The API MUST fail closed when tenant context is missing, invalid, disabled, or not represented by an active membership for the authenticated user.
- **FR-008**: The client MUST NOT be able to grant itself tenant access by sending an arbitrary tenant id/slug.
- **FR-009**: Customer rows MUST have a non-null tenant owner and all customer repository list/get/create/update/delete operations MUST require tenant scope.
- **FR-010**: Opportunity rows MUST have a non-null tenant owner and all opportunity repository/read/workflow operations MUST require tenant scope.
- **FR-011**: Customer email uniqueness MUST be enforced per tenant rather than globally.
- **FR-012**: Cross-tenant resource lookup/mutation using an id from another tenant MUST behave as not-found after membership validation and MUST not mutate data.
- **FR-013**: Successful Customer and Opportunity mutations MUST derive tenant ownership exclusively from RequestContext, never request body/query ownership fields.
- **FR-014**: AuditEvent `tenantId` MUST be non-null for tenant-owned domain audit events and MUST equal the validated RequestContext tenant id.
- **FR-015**: Audit reads MUST be tenant-scoped at repository level and MUST not return another tenant's audit events.
- **FR-016**: The same authenticated user MUST be able to resolve different roles/capabilities in different active tenants.
- **FR-017**: Session discovery MUST expose the authenticated identity plus only the active tenant memberships available to that user.
- **FR-018**: Tenant-scoped Principal/authorization state MUST be server-derived from the selected tenant membership.
- **FR-019**: The web application MUST make tenant selection explicit in the URL for tenant-owned resource pages.
- **FR-020**: TanStack Router MUST own tenant navigation/path state and TanStack Query keys MUST include tenant identity for tenant-owned remote state.
- **FR-021**: All HTTP clients used for tenant-owned resources/commands MUST propagate the explicitly selected tenant context through one project-owned transport boundary.
- **FR-022**: Tenant switching MUST invalidate or naturally segregate all tenant-owned cached server state so prior-tenant data is not rendered under the new tenant context.
- **FR-023**: The shell MUST visibly identify the current tenant and provide a deterministic switcher when more than one active membership is available.
- **FR-024**: An unauthorized/disabled tenant route MUST not render protected customer, opportunity, audit, or workflow state.
- **FR-025**: Membership revocation or tenant disablement MUST take effect on the next server-authorized request without requiring a new login.
- **FR-026**: Demo mode MUST model deterministic tenant membership and isolation semantics without treating demo behavior as an HTTP/server authorization bypass.
- **FR-027**: Security events, telemetry correlation and durable audit MUST retain the existing request correlation guarantees after tenant context is introduced.
- **FR-028**: Tenant context MAY be included in operational/security telemetry only as a non-secret stable identifier; authentication/session secrets MUST remain excluded.
- **FR-029**: Existing authentication, Customer CRUD, Opportunity workflow, audit atomicity, observability, strict TypeScript, accessibility and CI guarantees MUST remain intact.

### Key Entities

- **Tenant**: Security/data-isolation boundary representing one organization/workspace.
- **TenantMembership**: User-to-tenant association carrying tenant-local role and active/disabled status.
- **Global AccessProfile**: Application-wide access switch for an authenticated identity; no longer the source of tenant-local role.
- **Tenant RequestContext**: Server-validated tenant plus tenant-local Principal used by guards, repositories, mutations and audit.
- **Tenant Session Discovery**: Authenticated identity plus selectable active memberships; not a substitute for request-time membership validation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Automated PostgreSQL isolation tests demonstrate 100% of tested Customer and Opportunity list/detail/mutation paths return or mutate only the RequestContext tenant.
- **SC-002**: Cross-tenant id tests for Customer and Opportunity read/update/delete/workflow paths produce zero cross-tenant mutations and no successful cross-tenant audit events.
- **SC-003**: Authorization-matrix tests prove one identity can be Manager in Tenant A and Viewer in Tenant B with corresponding capabilities in 100% of tested operations.
- **SC-004**: 100% of committed Customer/Opportunity audit events in reference tenant flows contain the correct non-null tenant id and tenant-scoped audit reads return no foreign rows.
- **SC-005**: Browser tests demonstrate tenant switch changes URL, visible tenant, capabilities and Customer/Opportunity data without rendering prior-tenant cached rows.
- **SC-006**: Repository architecture tests demonstrate every tenant-owned repository method requires tenant scope and no tenant-owned Prisma query intentionally omits tenant filtering.
- **SC-007**: Membership revocation/tenant-disable integration tests deny the next protected request without re-authentication.
- **SC-008**: Demo mode and HTTP mode both pass tenant-navigation journeys, while HTTP mode additionally proves server-side membership enforcement.
- **SC-009**: Existing quality, PostgreSQL, Storybook/axe, Playwright and Spec Kit gates remain green after tenancy is integrated.

## Assumptions

- Shared-table PostgreSQL with mandatory `tenant_id` is the reference storage model; schema-per-tenant/database-per-tenant are outside this feature.
- Tenant-local roles remain the existing `admin`, `manager`, `viewer` set; custom roles are a future feature.
- Better Auth remains identity/session infrastructure only and does not become the tenant authorization authority.
- No global super-admin bypass is introduced in the reference feature.
- Resource ids remain globally unique even though access is always tenant-scoped.
- Tenant selection transport and frontend routing details are technical-plan decisions so long as the URL visibly identifies tenant context and the server validates membership every request.
