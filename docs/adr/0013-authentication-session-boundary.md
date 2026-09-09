# ADR-0013: Authentication Session Boundary

- **Status:** Accepted
- **Date:** 2026-09-08
- **Spec:** `specs/005-authentication-authorization/`

## Context

The starter already has typed application capabilities and an authorization provider, but identity is represented by a demo Principal and the Fastify reference API does not authenticate requests. The new reference authentication layer must provide secure enterprise sessions without turning a specific auth vendor into the application's authorization model.

The repository constitution requires server-authoritative authorization, a backend-agnostic frontend, replaceable infrastructure details, same-origin secure-session handling, and no unnecessary bespoke framework code.

## Decision

Use Better Auth `1.7.3`, pinned exactly, as the **reference identity and session adapter** for the Fastify/PostgreSQL stack.

- Better Auth owns credential verification, password hashing, identity accounts, sessions, session cookies, trusted-origin checks, and authentication rate limiting.
- PostgreSQL persists Better Auth core identity/session records through the Prisma adapter.
- Application authorization remains project-owned. `ApplicationRole`, `Capability`, `Principal`, `RequestContext`, and role-to-capability mapping are not delegated to Better Auth plugins.
- Application authorization state is stored in an `AccessProfile` keyed by the identity user's stable ID.
- The browser consumes an application-owned `/api/session` DTO and `AuthService` boundary. Feature code does not depend on Better Auth client types.
- Protected Fastify routes resolve a current RequestContext and enforce capabilities on the server before executing domain behavior.
- The reference topology uses same-origin secure cookie sessions. Reusable session credentials are not copied to localStorage/sessionStorage.
- Public email/password sign-up is disabled in normal runtime. Controlled development/CI provisioning is separate from the production sign-up surface.

## Consequences

### Positive

- Sensitive authentication protocol behavior is delegated to a maintained library rather than custom code.
- Authorization remains stable if the identity provider later changes to Cognito, Entra ID, Auth0, Keycloak, or another adapter.
- Role/status changes can take effect on the next protected request even when an identity session remains valid.
- The web application keeps a provider-neutral session contract.

### Trade-offs

- Better Auth schema changes require deliberate dependency upgrades and database migrations.
- The API must combine identity-session state with application access state before constructing a Principal.
- Cross-origin deployments require additional cookie/origin/CORS policy beyond the same-origin reference configuration.

## Alternatives Considered

### Better Auth Admin plugin as the permission source of truth

Rejected because provider-owned roles/permissions would duplicate the existing application capability model and make identity-provider replacement materially harder.

### Custom Fastify password/session implementation

Rejected because the starter should not own password hashing, credential protocol, session rotation, and abuse-protection machinery where a mature ecosystem library exists.

### Hosted-only authentication provider

Rejected as the sole reference because the open starter must remain runnable locally without a required SaaS account. Hosted providers remain valid future adapters.

## Validation

Feature 005 requires PostgreSQL-backed API integration tests plus browser E2E coverage for sign-in, session restore, sign-out, Admin/Manager/Viewer capability enforcement, and disabled/revoked access.
