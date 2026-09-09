# Research: Authentication and Authorization

## Decision 1 — Better Auth 1.7.3 as the reference authentication/session provider

**Decision**: Pin `better-auth` to `1.7.3` for the reference implementation.

**Rationale**:
- It is the current stable npm release as of 2026-09-08.
- It is framework-agnostic and has an official Fastify integration guide.
- Its official Prisma adapter documentation explicitly covers Prisma 7 + PostgreSQL.
- It provides cookie-based session management, server APIs, origin controls, and rate limiting without requiring a hosted vendor.
- It keeps identity/session mechanics in an ecosystem library rather than building password/session protocol code ourselves.

**Alternatives considered**:
- **Auth.js**: mature, but more framework-centric for the reference use case and less direct for Fastify.
- **Custom Fastify session/password stack**: rejected because it would make the starter own sensitive auth protocol concerns.
- **Hosted-only providers (Clerk/Auth0/etc.)**: useful adapters later, but unsuitable as the only reference because the starter should run locally without a required SaaS account.

**Sources**:
- https://www.npmjs.com/package/better-auth?activeTab=versions
- https://better-auth.com/docs/integrations/fastify
- https://better-auth.com/docs/adapters/prisma

## Decision 2 — Better Auth handles identity/session; project code owns authorization

**Decision**: Do not use Better Auth Admin-plugin permissions or roles as the application's authorization source of truth.

**Rationale**:
- The constitution requires stable typed capabilities and provider-replaceable auth infrastructure.
- Existing `Capability`, `Principal`, `can`, and `authorize` project abstractions already establish the intended application boundary.
- The application needs domain capabilities such as `customers.read` and `customers.delete`, not auth-vendor administrative permissions.
- Keeping roles/capabilities app-owned makes Cognito, Entra ID, Auth0, Keycloak, or another future identity provider replaceable without rewriting domain permissions.

**Alternatives considered**:
- **Better Auth Admin plugin custom roles**: technically capable, but would duplicate/couple the project's app-level capability model to the auth provider.
- **Persist every capability per user**: rejected for the first slice because the three reference roles are sufficient and a role mapping is easier to audit.

**Sources**:
- https://better-auth.com/docs/plugins/admin
- `.specify/memory/constitution.md`

## Decision 3 — Same-origin opaque cookie session

**Decision**: Keep the reference browser/API topology same-origin and use Better Auth's normal server-side session token cookie. Do not mirror the session token into browser storage.

**Rationale**:
- Same-origin avoids third-party cookie and Safari ITP problems and reduces CORS/CSRF complexity.
- Better Auth's primary session cookie is an opaque server-side session identifier.
- The repository constitution already prefers same-origin for secure cookie sessions.

**Alternatives considered**:
- **Bearer JWT in localStorage**: rejected because it unnecessarily exposes reusable auth material to JavaScript/XSS and creates a second session model.
- **Cross-origin cookie topology as default**: supported as a deployment variation later, but adds origin/cookie policy complexity without benefit to the reference topology.

**Sources**:
- https://better-auth.com/docs/concepts/cookies
- https://better-auth.com/docs/concepts/session-management

## Decision 4 — Seven-day sliding session, no application-capability cookie cache

**Decision**: Start with a 7-day session lifetime and 24-hour refresh/update window, matching Better Auth's documented baseline, while keeping application capability evaluation server-side on each protected request. Do not cache application capabilities in a client-readable or provider session-data cookie.

**Rationale**:
- It is a reasonable enterprise starter default and easy to override later.
- Role/status changes must take effect without waiting for stale authorization state in the browser.
- The identity session may be valid while the application access profile is disabled; app authorization therefore remains a separate server evaluation.

**Alternatives considered**:
- **Short 15–60 minute session**: stronger for some environments but unnecessarily disruptive for the generic starter without MFA/refresh-token UX.
- **Embed capabilities into the auth session cookie**: rejected because it introduces stale authority and provider coupling.

**Source**:
- https://better-auth.com/docs/concepts/session-management

## Decision 5 — Controlled reference-user provisioning; public sign-up disabled

**Decision**: Runtime self-registration is disabled. Local development and CI use a controlled seed path that creates the three reference identities (`admin`, `manager`, `viewer`) through a seed-only Better Auth configuration that allows sign-up while the normal runtime configuration does not.

**Rationale**:
- Enterprise admin applications commonly provision users rather than expose public registration.
- Using Better Auth's own server APIs for seed creation preserves password hashing and schema hooks rather than inserting credential records manually.
- A separate future user-management/invitation feature can add controlled provisioning without expanding this feature.

**Alternatives considered**:
- **Admin plugin just for seeding**: rejected because it introduces provider-owned role fields that could be mistaken for application authorization state.
- **Direct Prisma insertion of password/account records**: rejected because it relies on provider internals and could bypass password hashing invariants.

**Sources**:
- https://better-auth.com/docs/authentication/email-password
- https://better-auth.com/docs/concepts/api

## Decision 6 — Application access profile is checked on every protected request

**Decision**: Store `role` and `status` in an application-owned `AccessProfile`, keyed by Better Auth user ID. Resolve the profile when building the Principal/RequestContext for protected requests.

**Rationale**:
- Disabled access and role changes apply on the next server request even if the identity session remains valid.
- It preserves a clean distinction between authentication identity and authorization state.
- Capabilities can be derived from role in one audited mapping rather than duplicated in the database.

**Alternatives considered**:
- **Store role as Better Auth user additional field**: simpler physically, but couples authorization schema to the authentication provider and makes provider replacement harder.
- **Store capability arrays per user**: deferred until a real fine-grained requirement appears.

## Decision 7 — Better Auth built-in rate limiting is retained for auth endpoints

**Decision**: Keep Better Auth production rate limiting enabled and configure proxy/IP trust explicitly for deployments that sit behind a trusted reverse proxy.

**Rationale**:
- Repeated sign-in attempts need abuse protection.
- Better Auth applies a production default limiter and documents safe forwarded-IP handling.
- The starter should not invent a separate auth rate-limit subsystem in this slice.

**Alternatives considered**:
- **No rate limiting**: rejected by FR-019.
- **Redis-backed rate limiter baseline**: rejected because there is no current need to introduce Redis.

**Source**:
- https://better-auth.com/docs/concepts/rate-limit
