# Feature Specification: Clerk Authentication Provider Migration

**Feature ID**: `SPEC-020-CLERK-AUTHENTICATION`

**Feature Branch**: `feat/020-clerk-authentication`

**Created**: 2026-10-05

**Status**: In Progress

**Input**: User description: "Criar uma spec completa no padrão GitHub Spec Kit e implementar o login com Clerk e autenticação, buscando na documentação a versão mais recente e os padrões de biblioteca recomendados antes de implementar."

## Objective

Replace Better Auth as the reference identity/session provider with Clerk while preserving the application's existing provider-neutral authorization boundary.

Clerk owns sign-in, session issuance, token refresh/revocation, and hosted identity. CPXLabs Admin continues to own `ApplicationRole`, `Capability`, `Principal`, `RequestContext`, `AccessProfile`, and all domain authorization decisions.

The migration must use Clerk's current framework SDKs for this stack, resolve package versions from the current npm `latest` dist-tag at implementation time, pin the resulting exact versions, and keep Clerk-specific types out of domain and shared contract packages.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sign In with Clerk and Restore a Session (Priority: P1)

As a provisioned CPXLabs Admin user, I can authenticate through Clerk, return to the originally requested protected route, reload the application, and remain authenticated while my Clerk session is valid.

**Why this priority**: Authentication is the entry boundary for every protected workflow. The provider migration is not viable unless the primary sign-in/session journey works first.

**Independent Test**: Start without a Clerk session, navigate to a protected route, complete Clerk sign-in, verify the intended destination loads, reload, and verify the application Principal is restored through `GET /api/session`.

**Acceptance Scenarios**:

1. **Given** an unauthenticated browser, **When** a protected route is opened, **Then** the application redirects to `/sign-in` with a safe return target.
2. **Given** a provisioned Clerk user, **When** Clerk sign-in succeeds, **Then** the browser returns to the safe requested destination and the application session becomes authenticated.
3. **Given** a valid Clerk session, **When** the page reloads, **Then** Clerk restores the identity session and CPXLabs Admin restores the current application Principal without another credential prompt.
4. **Given** an already authenticated user, **When** `/sign-in` is opened, **Then** the application redirects to the protected default/return destination.

---

### User Story 2 - Authenticate API Requests without Delegating Authorization (Priority: P1)

As an authenticated user, my browser sends a current Clerk session token to the Fastify API while the API independently resolves the current application access profile and enforces typed capabilities.

**Why this priority**: A visual Clerk login is insufficient. Protected domain APIs must validate identity server-side and preserve deny-by-default application authorization.

**Independent Test**: Call `GET /api/session` and representative protected endpoints with no token, malformed/expired token, valid Clerk identity with no access profile, disabled profile, and active Admin/Manager/Viewer profiles; verify 401/403/200 outcomes and role matrix.

**Acceptance Scenarios**:

1. **Given** no Bearer session token, **When** a protected API is requested, **Then** the API returns `401 AUTHENTICATION_REQUIRED`.
2. **Given** an invalid or expired Clerk session token, **When** a protected API is requested, **Then** the API returns `401 AUTHENTICATION_REQUIRED` without protected data.
3. **Given** a valid Clerk user ID with no active `AccessProfile`, **When** protected behavior is requested, **Then** the API returns `403 ACCESS_DISABLED`.
4. **Given** an active application access profile, **When** protected behavior is requested, **Then** the current role-to-capability policy is applied exactly as before the provider migration.
5. **Given** a valid Clerk identity, **When** the API constructs `RequestContext`, **Then** downstream modules receive project-owned `Principal` data and do not depend on Clerk SDK types.

---

### User Story 3 - Sign Out, Revoke, and Fail Closed (Priority: P2)

As an operator, I can rely on sign-out, token expiry/revocation, and access-profile disablement to stop protected access on the next authoritative request.

**Why this priority**: Revocation and application disablement are core enterprise security controls.

**Independent Test**: Authenticate, sign out or disable the application's access profile, then attempt `/api/session` and a protected mutation and verify stale browser authority is cleared and the server rejects the request.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** the user signs out through Clerk, **Then** cached application Principal/query state is cleared and protected navigation requires authentication.
2. **Given** a Clerk session that becomes invalid, **When** the next protected request occurs, **Then** the API rejects it and the web application transitions out of authenticated application state.
3. **Given** a still-valid Clerk identity whose `AccessProfile` is disabled, **When** the next protected request occurs, **Then** the API returns `403 ACCESS_DISABLED`.
4. **Given** an application role change, **When** the next protected request occurs, **Then** capabilities are recomputed from the current application-owned access profile.

---

### User Story 4 - Remove Better Auth Runtime Ownership Cleanly (Priority: P2)

As a maintainer, I can reason about one identity/session provider without dead Better Auth runtime, schema, secrets, routes, or browser clients remaining in production paths.

**Why this priority**: Running two providers accidentally creates duplicate sources of truth and increases security/maintenance risk.

**Independent Test**: Inspect dependencies, runtime imports, Prisma schema, migrations, environment examples, startup, and authentication tests; verify Better Auth is absent from current runtime ownership and Clerk is isolated behind authentication adapters.

**Acceptance Scenarios**:

1. **Given** the migrated codebase, **When** production dependencies/imports are inspected, **Then** Better Auth and its Prisma adapter are not used by active runtime code.
2. **Given** the migrated database schema, **When** Prisma is generated/migrated, **Then** provider-owned Better Auth identity/session/account/verification tables are no longer required by application data.
3. **Given** an `AccessProfile`, **When** it is stored, **Then** its `userId` is an external Clerk user identifier without a foreign key to a local provider-owned user table.
4. **Given** Clerk is replaced in the future, **When** domain/resource modules are inspected, **Then** their authorization contracts remain `Principal`/`RequestContext`/capabilities rather than Clerk types.

### Edge Cases

- Clerk is temporarily unavailable while an already loaded page attempts to refresh a token.
- The publishable key is missing in server auth mode.
- The API secret key is missing or malformed at startup.
- A token is valid but has no `userId`.
- A Clerk user was deleted while an application `AccessProfile` remains.
- A Clerk user has no primary email or has an incomplete display name.
- The browser holds more than one tab and sign-out occurs in another tab.
- A return URL attempts an absolute, protocol-relative, or external redirect.
- A bearer token expires between render and a protected mutation.
- An active Clerk identity maps to a disabled application profile.
- A role changes while the Clerk session remains valid.
- Clerk development and production instances use different user IDs.
- Demo mode is selected and must not require Clerk keys or make Clerk network calls.
- Health/public endpoints remain reachable without authentication.
- A request contains only a Clerk cookie but no Authorization Bearer header; protected API authority must not silently fall back to cookie-only authentication.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** The web application MUST use Clerk as the reference identity/session provider in server auth mode.
- **FR-002** The implementation MUST use the current Clerk React SDK package recommended for React/Vite, `@clerk/react`; deprecated `@clerk/clerk-react` MUST NOT be introduced.
- **FR-003** The Fastify API MUST use Clerk's Fastify SDK rather than a hand-rolled JWT implementation.
- **FR-004** Clerk dependency versions MUST be resolved from npm's current `latest` dist-tag during implementation and the resolved versions MUST be pinned exactly in package manifests/lockfile.
- **FR-005** The web runtime MUST initialize Clerk through `ClerkProvider` only when server authentication mode is active.
- **FR-006** The public `/sign-in` route MUST render Clerk's maintained sign-in experience rather than owning password protocol fields in application code.
- **FR-007** Safe return-target handling MUST reject external/protocol-relative redirects.
- **FR-008** Protected web-to-API requests MUST send a current Clerk session token in the `Authorization: Bearer <token>` header.
- **FR-009** The shared HTTP transport MUST obtain tokens through Clerk's session API and MUST NOT persist reusable Clerk tokens in localStorage or sessionStorage.
- **FR-010** Protected API routes MUST require an Authorization Bearer session token and MUST NOT treat a cookie-only request as sufficient application API authentication.
- **FR-011** Fastify MUST validate Clerk session tokens server-side before protected application behavior executes.
- **FR-012** The authentication adapter MUST expose provider-neutral authenticated identity data to the application boundary.
- **FR-013** Clerk SDK types MUST NOT cross into `packages/contracts`, `packages/authorization`, resource modules, repositories, or domain workflow services.
- **FR-014** `ApplicationRole`, `Capability`, `Principal`, `RequestContext`, and capability mappings MUST remain project-owned.
- **FR-015** The API MUST resolve the current `AccessProfile` for the authenticated Clerk user on each authoritative request.
- **FR-016** Missing or disabled application access MUST fail closed with `403 ACCESS_DISABLED`.
- **FR-017** Missing, invalid, expired, or revoked identity MUST return `401 AUTHENTICATION_REQUIRED`.
- **FR-018** Capability denial for an authenticated active Principal MUST continue to return `403 FORBIDDEN`.
- **FR-019** `GET /api/session` MUST remain the application-owned browser bootstrap contract and return only the transport-safe Principal DTO.
- **FR-020** Sign-out MUST use Clerk's sign-out API and clear application/query authority state.
- **FR-021** The migration MUST remove active Better Auth browser/client/server route ownership and production dependencies.
- **FR-022** Better Auth provider tables MUST be removed from the reference Prisma schema by an explicit reviewed migration; `AccessProfile` MUST remain application-owned.
- **FR-023** `AccessProfile.userId` MUST store the external Clerk user ID without a local identity-table foreign key.
- **FR-024** Reference-user provisioning MUST be explicit and MUST NOT re-enable public self-registration in application code.
- **FR-025** Demo mode MUST remain available without Clerk keys and MUST not weaken server mode.
- **FR-026** Authentication/security failures MUST remain observable without logging bearer tokens, Clerk secret keys, passwords, or reusable credentials.
- **FR-027** Existing Admin/Manager/Viewer authorization behavior and customer/opportunity/audit protection MUST remain unchanged.
- **FR-028** Tests MUST cover provider-neutral request-context resolution, Bearer enforcement, 401/403 semantics, role capability enforcement, sign-out/session clearing, and environment fail-fast behavior.
- **FR-029** A live Clerk integration/E2E path MUST be documented and automated with Clerk-supported testing utilities when credentials are available; absence of external Clerk credentials MUST be reported as a Human Async Gate rather than hidden.
- **FR-030** Production configuration MUST document the Clerk Dashboard requirement to disable or otherwise restrict public sign-up for the reference enterprise deployment.

### Key Entities

- **Clerk Identity**: Hosted identity identified by Clerk's stable user ID. Credential/session mechanics are provider-owned.
- **Clerk Session Token**: Short-lived signed session token obtained by the browser and presented to the API as a Bearer token. It is identity evidence, not application authorization.
- **Application Access Profile**: Application-owned record keyed by Clerk user ID containing role and active/disabled status.
- **Principal**: Canonical application identity produced after valid Clerk authentication plus current application access evaluation.
- **RequestContext**: Per-request server context containing the canonical Principal and future contextual fields.
- **Application Role / Capability**: Stable project-owned authorization vocabulary independent of Clerk.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** 100% of protected API tests without a valid Bearer session token return `401` and no protected data/mutation.
- **SC-002** 100% of tested valid Clerk identities with missing/disabled access profiles return `403 ACCESS_DISABLED`.
- **SC-003** 100% of Admin/Manager/Viewer authorization matrix tests retain the pre-migration expected results.
- **SC-004** No active production source file imports `better-auth` or `@better-auth/prisma-adapter` after convergence.
- **SC-005** No Better Auth provider model is required by the converged Prisma schema.
- **SC-006** No reusable Clerk session token is intentionally persisted in browser localStorage/sessionStorage by application code.
- **SC-007** Static TypeScript, unit/integration tests, production build, Storybook/accessibility coverage, and non-live browser regression gates pass on the same final HEAD.
- **SC-008** When valid Clerk development credentials are available, the live critical journey sign-in → protected route → reload → authorized API → sign-out passes end-to-end.
- **SC-009** Clerk-specific imports are limited to the web authentication/platform boundary and API authentication adapter/startup boundary.
- **SC-010** The exact resolved `@clerk/react` and `@clerk/fastify` versions are recorded and frozen in `pnpm-lock.yaml`.

## Human Async Gate

**Gate ID**: `CLERK-LIVE-INTEGRATION`

**Owner**: operator

**Required for production readiness**: YES

**Can be self-passed by agent**: NO

The operator must supply/configure a Clerk development/production instance (publishable key + secret key), confirm enterprise sign-up policy in the Clerk Dashboard, and provide/provision at least one Clerk identity mapped to an application `AccessProfile`. Automated repository work may prepare and validate all code without these secrets, but must not claim live Clerk E2E or production readiness until the gate is explicitly satisfied.

## Assumptions

- Clerk is the requested new reference identity/session provider.
- The application continues to own roles/capabilities rather than adopting Clerk Organizations/roles in this feature.
- Social login, MFA policy design, passkeys, SAML/OIDC enterprise SSO, SCIM, Clerk Organizations, invitations, and user-management UI are outside this feature.
- Same-origin web/API deployment remains the reference topology, but API authentication is explicit Bearer-token based.
- Display identity may be fetched from Clerk at the authentication adapter boundary; it is not an authorization source of truth.
- Demo mode remains useful for local product/UI work without an external auth service.
