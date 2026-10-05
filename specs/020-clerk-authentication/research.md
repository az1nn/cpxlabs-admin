# Research: Clerk Authentication Provider Migration

**Feature**: `SPEC-020-CLERK-AUTHENTICATION`

**Research date**: 2026-10-05

## Decision 1 — Use `@clerk/react` for React + Vite

**Decision**: Use Clerk's current React SDK package `@clerk/react`.

**Rationale**:

- Clerk's current React Quickstart installs `@clerk/react`.
- Clerk has deprecated the older `@clerk/clerk-react` package in favor of `@clerk/react`.
- The supported root integration is `ClerkProvider`.
- The application remains a Vite SPA; no Next.js/React Router framework SDK is needed for this repository.

**Version policy**: During implementation, resolve npm `@latest` and save the resolved version exactly. Do not copy a version from stale documentation snippets.

**Sources**:

- https://clerk.com/docs/react/getting-started/quickstart
- https://www.npmjs.com/package/@clerk/react

## Decision 2 — Use `@clerk/fastify` for the API

**Decision**: Use Clerk's official Fastify SDK rather than manual JWT verification.

**Rationale**:

- `clerkPlugin()` integrates authentication with Fastify and validates session JWTs from requests.
- `getAuth()` exposes authenticated state/user ID at the Fastify request boundary.
- `clerkClient` provides the Backend API client when provider user details are needed.
- Keeping SDK usage inside an adapter lets downstream code continue to consume project-owned identity/authorization types.

**Version policy**: Resolve npm `@latest` during implementation and save the exact resulting version.

**Sources**:

- https://clerk.com/docs/fastify/getting-started/quickstart
- https://clerk.com/docs/reference/fastify/clerk-plugin
- https://clerk.com/docs/reference/fastify/get-auth

## Decision 3 — Prefer Bearer session tokens for the web → API boundary

**Decision**: Protected application API calls explicitly attach a Clerk session token as `Authorization: Bearer <token>`.

**Rationale**:

- Clerk documents `useAuth().getToken()` as the browser mechanism for retrieving the current session token for API requests.
- The Fastify SDK accepts session JWTs from request headers.
- Requiring the Bearer header prevents the application API from silently relying on ambient cookie-only authentication and makes the identity boundary explicit.
- Tokens stay in Clerk/session memory and are fetched as needed; application code does not copy reusable tokens into localStorage/sessionStorage.

**Alternative considered**: Cookie-only same-origin API authentication. Rejected for the migrated application API because explicit Bearer transport is easier to audit, test, and isolate from CSRF-style ambient credential behavior.

**Sources**:

- https://clerk.com/docs/guides/development/making-requests
- https://clerk.com/docs/reference/react/use-auth
- https://clerk.com/docs/reference/fastify/clerk-plugin

## Decision 4 — Use Clerk's maintained `<SignIn />` component

**Decision**: Replace the app-owned password form with Clerk's prebuilt sign-in component on the existing `/sign-in` route.

**Rationale**:

- Credential protocol, verification steps, MFA additions, and provider-specific error handling belong to Clerk.
- The prebuilt component reduces custom auth UI logic and follows Clerk's supported flow.
- CPXLabs Admin retains route ownership, safe return-target behavior, surrounding layout, and application authorization.

**Alternative considered**: Rebuild Clerk's email/password custom flow with low-level hooks. Rejected because there is no product requirement requiring custom credential-flow ownership.

**Sources**:

- https://clerk.com/docs/react/components/authentication/sign-in
- https://clerk.com/docs/guides/development/custom-flows/authentication/email-password

## Decision 5 — Keep authorization and access status outside Clerk

**Decision**: Clerk proves identity only. `AccessProfile`, `ApplicationRole`, `Capability`, `Principal`, and `RequestContext` remain application-owned.

**Rationale**:

- The repository constitution requires server-authoritative typed authorization and provider replaceability.
- Existing domain behavior already consumes `Principal`/`RequestContext`.
- A provider migration should not silently migrate business permissions into vendor metadata/organization roles.
- Role/status changes must take effect from current PostgreSQL state on the next server-authoritative request.

## Decision 6 — Remove Better Auth provider tables

**Decision**: Remove Better Auth's local `User`, `Session`, `Account`, and `Verification` models from the reference Prisma schema and remove the `AccessProfile -> User` foreign key.

**Rationale**:

- Clerk becomes the provider of record for identity/session.
- Keeping provider-owned Better Auth schema after migration creates misleading dual ownership.
- Application data needs only the stable external Clerk user ID to map authorization state.

**Migration safety**:

- The schema migration is intentionally destructive for Better Auth provider data.
- It must not drop `AccessProfile`, domain data, or audit data.
- Production rollout must ensure required Clerk identities/access profiles exist before switching traffic.

## Decision 7 — Fetch display identity only inside the provider adapter

**Decision**: The Clerk adapter may use `clerkClient.users.getUser(userId)` to obtain transport-safe display identity required by the existing Principal/audit contract.

**Rationale**:

- Clerk's Fastify reference explicitly demonstrates `getAuth()` followed by `clerkClient.users.getUser()`.
- Email/name remain descriptive identity, not capability authority.
- This keeps provider-specific calls centralized and replaceable.

**Trade-off**: A Backend API lookup can add latency/rate-limit pressure. If measurement shows this is material, a later spec may introduce verified session claims or webhook-synchronized display identity. This feature does not prematurely add that complexity.

## Decision 8 — Live E2E uses Clerk-supported test tooling when credentials exist

**Decision**: Add/document a live Clerk E2E lane using Clerk's supported Playwright testing utilities, but treat external keys/account setup as a Human Async Gate.

**Rationale**:

- CI cannot manufacture a Clerk tenant/secret safely.
- Repository tests can fully validate adapter boundaries, Bearer enforcement, authorization, build, and demo/regression flows without external credentials.
- A true sign-in journey must be run against an actual Clerk development instance before production readiness is claimed.

**Sources**:

- https://clerk.com/docs/testing/playwright/overview
- https://clerk.com/docs/testing/test-emails-and-phones

## Decision 9 — Environment loading must precede Clerk Fastify imports

**Decision**: Preserve the API startup pattern that loads `.env` before dynamically importing the Clerk-specific adapter.

**Rationale**:

- Clerk's Fastify SDK documentation explicitly warns that environment variables must be loaded before importing Clerk modules because keys are read during initialization.
- The current `server.ts` dynamic-import pattern can preserve this invariant.

**Source**:

- https://clerk.com/docs/reference/fastify/clerk-plugin
