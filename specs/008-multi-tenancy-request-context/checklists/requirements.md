# Specification Quality Checklist: Multi-Tenancy and Request Isolation

**Feature**: `008-multi-tenancy-request-context`  
**Reviewed**: 2026-09-10  
**Result**: 16/16 PASS

- [x] User stories describe tenant isolation, tenant-local authorization, switching, audit ownership, and demo/reference behavior independently.
- [x] Every P1 story has an independently executable acceptance path.
- [x] Tenant identity is treated as a selector that requires server-side membership validation, never as authorization proof.
- [x] Missing, invalid, disabled, and unauthorized tenant contexts are explicitly fail-closed.
- [x] Cross-tenant resource probing has a defined non-disclosing not-found behavior after tenant membership validation.
- [x] Global application access and tenant-local authorization have distinct authorities.
- [x] The same identity having different roles in different tenants is explicitly required and testable.
- [x] Customer and Opportunity ownership is mandatory and repository-level isolation is required for every read/write path.
- [x] Customer email uniqueness semantics are explicitly changed from global to tenant-local.
- [x] Durable audit tenant ownership and tenant-scoped audit reads are explicit requirements.
- [x] Browser tenant selection is visible in the URL and cache-key isolation is explicitly required.
- [x] Membership revocation and tenant disablement are required to take effect on the next authorized request.
- [x] Demo mode is preserved without weakening HTTP/server authorization requirements.
- [x] Global super-admin, tenant administration, billing, invitations, SSO, and custom domains are clearly outside scope.
- [x] Success criteria are measurable through PostgreSQL, authorization-matrix, architecture, browser, and CI gates.
- [x] No unresolved `NEEDS CLARIFICATION` marker remains; the technical plan may choose transport details without changing feature intent.
