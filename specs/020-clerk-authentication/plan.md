# Implementation Plan: Clerk Authentication Provider Migration

**Branch**: `feat/020-clerk-authentication` | **Date**: 2026-10-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/020-clerk-authentication/spec.md`

## Summary

Migrate the reference identity/session layer from Better Auth to Clerk using the current React and Fastify SDKs, explicit Bearer session tokens for browser-to-API requests, and a provider-neutral identity adapter. Preserve the existing application-owned access profile, Principal/RequestContext contract, typed capability matrix, and server-authoritative authorization.

## Technical Context

**Language/Version**: TypeScript 7.x, Node.js >=22.12, React 19

**Primary Dependencies**: `@clerk/react` current npm latest (exact pin resolved during implementation), `@clerk/fastify` current npm latest (exact pin resolved during implementation), Fastify 5.12.x, Prisma 7.10.x, PostgreSQL 17, TanStack Router/Query

**Storage**: PostgreSQL for domain/application authorization data only; Clerk hosts identity/session data

**Testing**: Vitest unit/integration, PostgreSQL-backed authorization tests, Storybook/axe regression, Playwright product regression, Clerk-supported live Playwright lane when external credentials are available

**Target Platform**: Vite SPA + Node.js Fastify API; same-origin reference deployment with explicit Bearer API auth

**Project Type**: pnpm/Turborepo web application monorepo

**Performance Goals**: One identity validation + one current access-profile read per protected request; provider user lookup centralized and measurable; no duplicate token/session bootstrap calls from each feature

**Constraints**: No token persistence in browser storage; deny-by-default server authorization; demo mode must not require Clerk; no Clerk types beyond auth adapter boundaries; exact dependency lockfile; no Better Auth runtime after convergence

**Scale/Scope**: Existing customer/opportunity/audit protected surfaces and Admin/Manager/Viewer roles; no organization/SSO/user-admin expansion

## Constitution Check

| Principle | Status | Evidence |
|---|---|---|
| Spec Before Implementation | PASS | Full Spec Kit artifacts are authored on Feature 020 before runtime/package changes. |
| Backend-Agnostic Frontend | PASS | Domain/features consume application session/transport boundaries; Clerk hooks are isolated to auth/bootstrap transport. |
| Server Authority / Typed Authorization | PASS | AccessProfile + Principal/RequestContext + capability guards stay authoritative on Fastify. |
| Strict Types / Tests / CI | PASS | Typecheck, unit/integration, build, browser/a11y, PostgreSQL and live-Clerk gate are explicitly planned. |
| Simplicity / Replaceability | PASS | Official Clerk SDKs are used behind project-owned adapters; no custom JWT cryptography. |
| Engineering Graph Canonicality | PASS | Git Spec Kit artifacts remain canonical; graph remains derived. |
| Same-Origin Security | PASS | Deployment remains same-origin while protected API calls require explicit Bearer session tokens. |

No constitution exception is required.

## Architecture

```text
Browser
  |
  | ClerkProvider + <SignIn />
  | useAuth().getToken()
  v
Authenticated fetch  ---------------------------+
  | Authorization: Bearer <session JWT>         |
  v                                             |
Fastify + @clerk/fastify                        |
  | validate session -> Clerk userId            |
  | optional Clerk Backend User lookup          |
  v                                             |
Provider-neutral AuthenticatedIdentity          |
  + PostgreSQL AccessProfile -------------------+
  |
  v
Principal / RequestContext
  |
  +-> typed capability guards
  |
  +-> Customer / Opportunity / Audit modules
```

### Authority boundary

- Clerk: identity, credential flows, session issuance/refresh/revocation.
- CPXLabs Admin: access activation, role, capabilities, Principal, RequestContext, domain authorization.
- Browser: UX only; never authoritative for capability decisions.

## Design Decisions

1. **React integration**: `ClerkProvider` + maintained `SignIn` UI.
2. **API integration**: `@clerk/fastify` `clerkPlugin` + `getAuth` inside a provider adapter.
3. **API transport**: Bearer session token required for protected application API requests.
4. **Application session contract**: keep `GET /api/session` and existing transport DTO stable.
5. **Auth adapter**: introduce project-owned `IdentityProvider` / `AuthenticatedIdentity` shape consumed by RequestContext resolution.
6. **Authorization**: preserve current AccessProfile repository and capability policy.
7. **Data migration**: drop Better Auth provider tables; AccessProfile keeps external user ID and loses local User FK.
8. **Demo mode**: unchanged provider-neutral demo Principal; Clerk initialized only in server mode.
9. **Provisioning**: explicit Clerk users + access profiles; no public application sign-up.
10. **Testing**: fake identity adapter for deterministic API tests; live Clerk E2E is a separately visible external gate.

## Project Structure

### Documentation

```text
specs/020-clerk-authentication/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── session-api.md
├── tasks.md
├── analysis.md
├── convergence.md
└── checklists/
    └── requirements.md

docs/adr/0028-clerk-authentication-provider-boundary.md
```

### Primary source changes

```text
apps/api/
├── package.json
├── .env.example
├── prisma/
│   ├── schema.prisma
│   └── migrations/<timestamp>_clerk_identity_migration/migration.sql
└── src/
    ├── app.ts
    ├── server.ts
    └── platform/authentication/
        ├── identity-provider.ts
        ├── clerk-identity-provider.ts
        ├── session.ts
        └── *.test.ts

apps/web/
├── package.json
├── .env.example
└── src/
    ├── main.tsx
    ├── router.tsx
    ├── config/env.ts
    ├── features/auth/sign-in-page.tsx
    └── platform/authentication/
        ├── clerk-auth-provider.tsx
        ├── authenticated-fetch.ts
        └── session-provider.tsx
```

Existing HTTP adapters are updated to consume authenticated fetch rather than obtaining provider details themselves.

## Phase 0 — Dependency and documentation verification

1. Verify current official Clerk React/Fastify guidance.
2. Resolve `@clerk/react@latest` and `@clerk/fastify@latest` from npm in the implementation branch.
3. Save exact versions and regenerate `pnpm-lock.yaml`.
4. Record the exact resolved versions in convergence evidence.

## Phase 1 — Provider-neutral server boundary

1. Define `AuthenticatedIdentity` and `IdentityProvider`.
2. Refactor RequestContext resolver to depend on the interface.
3. Implement Clerk Fastify adapter using `getAuth` and `clerkClient`.
4. Require Bearer header for protected API identity resolution.
5. Preserve 401/403/capability behavior.

## Phase 2 — Persistence migration

1. Remove Better Auth provider models from Prisma.
2. Remove AccessProfile FK to local User.
3. Add reviewed migration that drops only provider tables/FK.
4. Update reference provisioning/seed behavior for external Clerk IDs.

## Phase 3 — Web Clerk session/login

1. Add conditional `ClerkProvider` in server auth mode.
2. Replace custom credential form with Clerk `SignIn`.
3. Add token-aware authenticated fetch boundary using `getToken()`.
4. Feed the token-aware fetcher into application HTTP adapters.
5. Keep `GET /api/session` as the Principal bootstrap.
6. Use Clerk sign-out and clear application query/principal state.

## Phase 4 — Tests, CI, and migration cleanup

1. Replace Better Auth integration tests with fake-provider + Clerk adapter tests.
2. Verify Bearer-only behavior.
3. Preserve full role matrix.
4. Keep default CI deterministic without external SaaS secrets.
5. Add/document live Clerk Playwright lane requiring external credentials.
6. Remove Better Auth env/dependencies/imports/docs.

## Phase 5 — Convergence

1. Run Spec Kit/Engineering Graph checks.
2. Run Product CI gates on the same candidate HEAD.
3. Record Human Async Gate `CLERK-LIVE-INTEGRATION`.
4. Do not claim production readiness while that gate is pending.

## Engineering Graph References

**Constrained by ADRs**: ADR-0013 (superseded for identity provider by ADR-0028; app-owned authorization remains), ADR-0028

**Depends on Specs/Tasks**: `SPEC-005-AUTHENTICATION-AUTHORIZATION` as the existing contract being migrated; no unfinished task dependency

**Primary implementation paths**: `apps/api/src/platform/authentication/`, `apps/web/src/platform/authentication/`, `apps/api/prisma/`, `apps/web/src/main.tsx`, `apps/web/src/router.tsx`

**Primary validation paths**: API auth/authorization tests, web auth tests, Playwright auth journey, root CI workflows

## Complexity Tracking

No constitution violations.
