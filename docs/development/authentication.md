# Authentication and authorization development

Feature `005-authentication-authorization` uses Better Auth for identity and secure cookie sessions while CPXLabs Admin owns application authorization.

## Local reference users

Reference identities are created only by the explicit database seed. Configure the API environment first:

```bash
cp apps/api/.env.example apps/api/.env
```

Set a development-only value for `SEED_AUTH_PASSWORD`, then run:

```bash
docker compose up -d postgres
pnpm --filter @cpxlabs-admin/api db:migrate
pnpm --filter @cpxlabs-admin/api db:seed
```

The seed provisions:

- `admin@cpxlabs.local` → Admin
- `manager@cpxlabs.local` → Manager
- `viewer@cpxlabs.local` → Viewer

The repository intentionally does not contain a reusable password. Do not run the reference auth seed in production.

## Runtime topology

The preferred development and production topology is same-origin from the browser:

```text
Browser
  ├── /            → Vite/Vercel SPA
  └── /api/*       → Fastify reference API
                        └── Better Auth + PostgreSQL
```

The browser stores no bearer token or reusable session secret in `localStorage` or `sessionStorage`. Better Auth session cookies are transported with `credentials: include` and remain provider infrastructure.

## Application authorization

Better Auth answers identity/session questions only. The application resolves the authenticated user to an `AccessProfile` on the server and constructs the canonical `Principal`.

Current reference matrix:

| Role | Read | Create | Update | Delete |
| --- | --- | --- | --- | --- |
| Admin | yes | yes | yes | yes |
| Manager | yes | yes | yes | no |
| Viewer | yes | no | no | no |

Capability keys remain the stable application contract:

- `customers.read`
- `customers.create`
- `customers.update`
- `customers.delete`

The client uses these capabilities only to adapt UX. Every protected API operation re-resolves current server access state and enforces the capability again.

## Failure semantics

- missing/expired/revoked provider session → `401 AUTHENTICATION_REQUIRED`
- authenticated identity with missing/disabled access profile → `403 ACCESS_DISABLED`
- authenticated principal lacking a required capability → `403 FORBIDDEN`

A role or access-status change therefore takes effect on the next authoritative request rather than waiting for a client token to expire.

## Security events

Authentication/authorization failures emit structured warning events with request id, method and route. Security-event metadata drops secret-like keys such as passwords, tokens, cookies, authorization headers and secrets.
