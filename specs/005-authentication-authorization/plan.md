# Implementation Plan: Authentication and Authorization

**Branch**: `feat/005-authentication-authorization` | **Date**: 2026-09-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-authentication-authorization/spec.md`

## Summary

Introduce a reference enterprise authentication boundary with Better Auth-backed identity/session handling, an application-owned access profile and role-to-capability mapping, canonical Principal/RequestContext resolution, protected Fastify routes, and a Vite sign-in/session experience. Better Auth remains an infrastructure/provider detail; application authorization stays typed, deny-by-default, and server-authoritative.

## Technical Context

**Language/Version**: TypeScript 7.x, Node.js >=22.12, React 19

**Primary Dependencies**: Better Auth 1.7.3, Fastify 5.12.1, Prisma 7.10.0, PostgreSQL 17, React + Vite, TanStack Router, TanStack Query, React Hook Form + Zod

**Storage**: PostgreSQL for Better Auth identity/session records, application access profiles, and existing domain data

**Testing**: Vitest unit/API/integration tests, PostgreSQL-backed repository/auth integration tests, Storybook/axe for sign-in/shared UI where applicable, Playwright for Admin/Manager/Viewer journeys

**Target Platform**: Same-origin browser SPA + Node.js Fastify API; Vercel-compatible web deployment and independently deployable reference API

**Project Type**: pnpm/Turborepo web application monorepo

**Performance Goals**: Session/principal resolution should not materially dominate normal CRUD request latency; avoid duplicate identity/session calls per protected request; browser session bootstrap should provide usable authenticated state within standard interactive web expectations

**Constraints**: Secure cookie sessions; no reusable auth secret in browser-accessible storage; server-authoritative authorization; public self-registration disabled; Better Auth and Prisma must remain infrastructure details; existing strict TypeScript and CI gates cannot be weakened

**Scale/Scope**: Reference Admin/Manager/Viewer authorization across the current customer resource; architecture must remain suitable for future resources, external IdPs, tenants, and MFA without requiring frontend domain rewrites

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|---|---|---|
| Spec Before Implementation | PASS | `spec.md` and requirements checklist exist before code changes. |
| Backend-Agnostic Frontend | PASS | Web consumes app-owned session/auth service contracts; Better Auth integration is isolated in platform adapters. |
| Server Authority / Typed Authorization | PASS | Principal/RequestContext and capability enforcement are resolved by API; UI checks remain UX-only. |
| Strict Types / Tests / CI | PASS | Plan includes unit, API, PostgreSQL integration, browser and E2E coverage; no compiler relaxation. |
| Simplicity / Replaceability | PASS | One mature auth library is used for identity/session mechanics; app authorization is not coupled to provider roles. |
| Same-Origin Session Topology | PASS | `/api/auth/*`, `/api/session`, and domain APIs remain same-origin in the reference topology. |

No constitution violations require Complexity Tracking.

## Architecture Decisions

1. **Authentication provider**: Better Auth `1.7.3`, exact pin, is the reference identity/session adapter.
2. **Authorization ownership**: application roles and capabilities remain in project-owned contracts and access-profile data; Better Auth authorization/admin roles are not the source of truth.
3. **Session transport**: opaque server-validated cookie session; session credentials are not copied into localStorage/sessionStorage.
4. **Principal bootstrap**: app-owned `GET /api/session` resolves Better Auth identity + current application access profile and returns a transport-safe principal DTO.
5. **Server context**: protected Fastify routes resolve `RequestContext` and deny unauthenticated/unauthorized access before domain behavior.
6. **Role mapping**: `admin`, `manager`, `viewer` map to typed capabilities in project-owned code; capabilities are derived, not persisted individually.
7. **Disabled access**: access-profile status is checked server-side on principal resolution. Existing identity sessions cannot bypass a disabled application profile.
8. **Self-registration**: disabled in normal runtime. Reference users are provisioned only by controlled development/test seed setup; user-management UI is out of scope.
9. **Session caching**: provider-side session cookie caching is not enabled in the first slice; application capabilities are always derived from current server-side access state.
10. **Authentication UX**: app-owned `AuthService`/session query boundary isolates provider calls from feature and shell code.

## Project Structure

### Documentation (this feature)

```text
specs/005-authentication-authorization/
├── spec.md
├── checklists/
│   └── requirements.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── session-api.md
└── tasks.md
```

### Source Code

```text
packages/contracts/src/
├── resource.ts
└── session.ts                       # transport-safe session/principal contracts

packages/authorization/src/
└── index.ts                         # Principal, RequestContext, role/capability policy

apps/api/
├── prisma/schema.prisma             # Better Auth models + AccessProfile
├── prisma/migrations/
└── src/
    ├── platform/
    │   ├── authentication/
    │   │   ├── auth.ts              # Better Auth configuration/factory
    │   │   ├── fastify-auth.ts      # /api/auth/* bridge
    │   │   └── session.ts           # identity -> Principal/RequestContext
    │   ├── authorization/
    │   │   └── guards.ts            # requirePrincipal/requireCapability
    │   └── database/
    │       └── seed.ts
    └── modules/customers/
        └── customer.routes.ts       # capability-enforced resource routes

apps/web/src/
├── features/authentication/
│   ├── api/auth-service.ts
│   ├── components/sign-in-form.tsx
│   └── views/sign-in-page.tsx
├── platform/authentication/
│   ├── auth-provider.tsx
│   └── session.ts
├── platform/authorization/
│   └── authorization-provider.tsx
└── router.tsx                       # public sign-in + protected route guard
```

**Structure Decision**: Authentication mechanics live in `platform` boundaries, the user-facing sign-in slice lives in `features/authentication`, and resource modules only see RequestContext/capability guards. No new shared auth package is introduced because there is not yet a second runtime consumer requiring one.

## Phase 0: Research

Research resolves:

- Better Auth current stable release and Fastify integration pattern
- Prisma 7 adapter compatibility
- cookie/session lifecycle and CSRF/origin posture
- rate-limit defaults and trusted proxy considerations
- controlled provisioning with self-registration disabled
- boundary between identity provider data and application authorization data

Output: [research.md](./research.md)

## Phase 1: Design & Contracts

- Define Better Auth identity/session tables and `AccessProfile` application data.
- Define app-owned transport contract for `GET /api/session` and 401/403 semantics.
- Define role-to-capability policy and canonical Principal/RequestContext.
- Define end-to-end validation guide including Admin/Manager/Viewer.
- Re-check constitution after design.

Outputs: [data-model.md](./data-model.md), [contracts/session-api.md](./contracts/session-api.md), [quickstart.md](./quickstart.md)

## Post-Design Constitution Re-check

| Principle | Status | Design Result |
|---|---|---|
| Provider replaceability | PASS | Better Auth appears only behind API/web authentication adapters; app session contract is provider-neutral. |
| ORM isolation | PASS | Better Auth/Prisma schema is API infrastructure; no generated type crosses contracts. |
| Authorization authority | PASS | Capabilities are mapped in project code and checked on server for every protected operation. |
| Avoid stale authority | PASS | Access profile is resolved on server; provider session cookie cache is not used to carry application capabilities. |
| Testing | PASS | Plan requires real PostgreSQL and real HTTP/browser role matrix. |

## Complexity Tracking

No constitution violations or additional architectural exceptions are required.
