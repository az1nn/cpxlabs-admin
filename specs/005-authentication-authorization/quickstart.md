# Quickstart: Validate Authentication and Authorization

## Prerequisites

- Node.js version accepted by the repository engines field
- pnpm from the root `packageManager` declaration
- Docker/Compose or another PostgreSQL 17 instance
- environment values for the API database and authentication secret/base URL

## Environment

Start from the API example environment and provide values equivalent to:

```text
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cpxlabs_admin
BETTER_AUTH_SECRET=<long-random-secret>
BETTER_AUTH_URL=http://localhost:3001
APP_ORIGIN=http://localhost:4173
```

Reference seed users use controlled development/test credentials supplied by seed or CI environment rather than production defaults.

## Install and Prepare Database

```bash
pnpm install --frozen-lockfile
docker compose up -d postgres
pnpm --filter @cpxlabs-admin/api db:migrate
pnpm --filter @cpxlabs-admin/api db:seed
```

Expected outcome:

- Better Auth identity/session schema exists.
- Application access-profile schema exists.
- Admin, Manager, and Viewer reference identities/access profiles exist in local/CI data.
- Existing customer seed data remains available.

## Run API and Web

```bash
pnpm --filter @cpxlabs-admin/api dev
pnpm --filter @cpxlabs-admin/web dev
```

Use the web origin configured for the environment. The reference topology should route browser `/api` traffic to the API same-origin in preview/E2E scenarios.

## Validate User Story 1 — Session

1. Open a protected route without a session.
2. Confirm navigation goes to `/sign-in`.
3. Sign in with an active reference user.
4. Confirm the protected route becomes available.
5. Reload the page and confirm the session is restored.
6. Sign out from the shell.
7. Confirm protected navigation/API access requires sign-in again.

Expected API checks:

```text
GET /api/session without session -> 401 AUTHENTICATION_REQUIRED
GET /api/session with active session/profile -> 200 principal DTO
```

## Validate User Story 2 — Role Matrix

Use the same customer operations for each reference role.

### Admin

Expected: list/show/create/edit/delete all succeed.

### Manager

Expected: list/show/create/edit succeed; delete is unavailable in UI and direct DELETE returns `403 FORBIDDEN`.

### Viewer

Expected: list/show succeed; create/edit/delete are unavailable in UI and direct mutation requests return `403 FORBIDDEN`.

## Validate User Story 3 — Disabled Access

1. Establish an identity session for a reference user.
2. Change that user's application access profile status to disabled using a test fixture/repository helper.
3. Request `/api/session` or a protected domain endpoint again.
4. Confirm access fails closed even though the provider identity session was previously valid.

Expected: `403 ACCESS_DISABLED` for the application session endpoint and no domain mutation.

## Automated Validation

```bash
pnpm typecheck
pnpm test
pnpm build
pnpm test:storybook
pnpm e2e
```

CI must run the persistence/auth integration against a real PostgreSQL service. The Playwright journey must use the real Fastify API rather than the demo provider.

## Security Validation

During the browser test:

- confirm no password is retained after form submission;
- confirm no provider session token is written to localStorage/sessionStorage;
- confirm direct unauthorized API calls are rejected server-side;
- confirm sign-in errors do not disclose account existence;
- confirm repeated auth calls are handled by configured abuse protection.

## Success Signal

The feature is ready to converge when all specification success criteria pass and the role matrix behaves identically through UI intent and direct API enforcement.
