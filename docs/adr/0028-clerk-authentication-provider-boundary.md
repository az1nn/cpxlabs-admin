# ADR-0028: Clerk Authentication Provider Boundary

- **Status:** Accepted
- **Date:** 2026-10-05
- **Spec:** `specs/020-clerk-authentication/`
- **Supersedes:** ADR-0013 only for the identity/session provider choice; ADR-0013's application-owned authorization boundary remains in force.

## Context

CPXLabs Admin already has a stable application authorization model: `AccessProfile`, typed `ApplicationRole`/`Capability`, canonical `Principal`/`RequestContext`, deny-by-default Fastify guards, and an app-owned `GET /api/session` contract.

Feature 005 selected Better Auth for local identity/session mechanics. The current product direction requires Clerk login/authentication instead. The migration must not turn a vendor switch into a rewrite of domain authorization or leave two active identity/session providers.

## Decision

Use Clerk as the reference identity/session provider.

- Use `@clerk/react` for the Vite/React browser integration.
- Use `@clerk/fastify` for Fastify session-token validation and provider user lookup.
- Resolve both from npm's current `latest` dist-tag during Feature 020 implementation and pin the resolved versions exactly.
- Use Clerk's maintained `<SignIn />` component for credential flow.
- Browser-to-API protected requests send a current Clerk session JWT explicitly as an Authorization Bearer token.
- Fastify rejects protected requests that do not provide the Bearer token even if ambient cookies exist.
- Clerk-specific SDK objects are normalized inside an authentication adapter.
- PostgreSQL `AccessProfile`, application roles/capabilities, Principal/RequestContext and server capability guards remain authoritative for application authorization.
- Remove Better Auth runtime dependencies/routes/client and provider-owned identity/session tables.
- `AccessProfile.userId` becomes a unique external Clerk user ID with no local provider-user foreign key.
- Demo mode remains provider-neutral and does not require Clerk.

## Consequences

### Positive

- Clerk owns credential/session protocol and maintained authentication UI.
- Application authorization remains stable and testable across provider changes.
- The API boundary is explicit through Bearer tokens rather than ambient cookie authority.
- Better Auth provider schema/runtime is removed, eliminating dual identity ownership.
- Domain modules continue to depend on project contracts rather than vendor SDKs.

### Trade-offs

- Local/server auth mode now depends on an external Clerk development instance for a true sign-in flow.
- Clerk Backend API user lookup can add latency and rate-limit pressure; this must be measured before adding claims/webhook caching.
- Existing Better Auth identities/sessions do not migrate automatically to Clerk IDs; production cutover requires explicit user provisioning/mapping.
- Live auth E2E requires protected Clerk test credentials, so it remains an explicit external gate.

## Rejected alternatives

### Keep Better Auth and add Clerk only in the frontend

Rejected because two independent session/identity authorities create ambiguity and do not implement a real provider migration.

### Put roles/capabilities in Clerk metadata/Organizations

Rejected for this feature because it couples domain authorization to the identity vendor and conflicts with the existing stable authorization boundary.

### Hand-roll Clerk JWT verification

Rejected because the official Fastify SDK exists and should own protocol-level validation.

### Cookie-only API auth

Rejected for the protected application API. Explicit Bearer tokens produce a clearer web/API trust boundary and avoid ambient-cookie authority.

## Validation

Feature 020 requires:

- exact pinned Clerk dependency resolution;
- strict TypeScript;
- provider-neutral API tests;
- Bearer-only enforcement tests;
- PostgreSQL access-profile tests;
- production build;
- browser/a11y regressions;
- live Clerk sign-in E2E when external credentials are available;
- Spec Kit and Engineering Graph gates;
- explicit Human Async Gate status for live Clerk integration.
