# Implementation Plan: HTTP API and PostgreSQL Persistence

**Branch**: historical retrofit | **Date**: 2026-09-08 | **Spec**: `specs/004-http-api-persistence/spec.md`

**Status**: Implemented (Retrofitted)

## Summary

Prove the backend-agnostic frontend boundary with an HTTP `DataProvider`, add an optional Fastify reference API, and persist Customers through PostgreSQL behind an async repository contract. Keep Vercel web deployment functional in demo mode and validate the complete HTTP/database path in CI.

## Technical Context

**Language/Version**: TypeScript strict; Node.js 22 reference runtime

**Primary Dependencies**: Fastify, Prisma 7.10.0, `@prisma/adapter-pg`, PostgreSQL driver, Playwright

**Storage**: PostgreSQL 17

**Testing**: Vitest/API inject tests, repository integration tests, Storybook/axe, Playwright real HTTP E2E

**Target Platform**: Vercel for SPA web; Node/Fastify server; PostgreSQL service

**Project Type**: Full reference stack in a backend-agnostic monorepo

**Performance Goals**: Server-driven list operations; no frontend rewrite when switching providers

**Constraints**: ORM stays behind repositories; seed separated from migrations; same-origin reference topology; exact Prisma pin

**Scale/Scope**: Reference Customers CRUD end-to-end rather than generalized domain services or distributed infrastructure

## Constitution Check

- Spec-before-implementation: **Historical exception**; retrofit only.
- Backend-agnostic frontend: Pass; HTTP introduced behind existing provider contract.
- Strict types/tests/CI: Pass, including PostgreSQL integration and browser E2E.
- Simplicity: Pass; modular monolith/reference API, no Redis/queues/microservices introduced.
- Replaceable infrastructure: Pass; Fastify/Prisma remain optional reference implementations.

## Project Structure

```text
apps/web/
├── src/platform/data/http-data-provider.ts
└── vercel.json

apps/api/
├── prisma/
│   ├── migrations/
│   └── schema.prisma
└── src/
    ├── modules/customers/
    │   ├── customer.routes.ts
    │   ├── customer.repository.ts
    │   └── customer.prisma-repository.ts
    └── platform/
        ├── database/
        └── errors.ts

packages/contracts/
└── src/api-error.ts

compose.yml
```

**Structure Decision**: The API remains an optional app. Persistence details live inside `apps/api`; web and shared contracts never import generated Prisma code.

## Architecture Decisions

- Vercel deploys the Vite SPA with a deep-link rewrite and demo provider by default.
- `HttpDataProvider` is selected through environment configuration.
- Fastify is the TypeScript reference API and uses JSON Schema validation/serialization.
- `CustomerRepository` is asynchronous and injected into routes/application composition.
- PostgreSQL 17 is the reference database; Prisma 7.10.0 is pinned behind the repository adapter.
- Migrations define schema only; seed is explicit.
- Playwright runs web preview and Fastify together, proxying `/api` same-origin and using PostgreSQL in CI.

## Complexity Tracking

The repository abstraction is justified because the starter explicitly supports multiple backend/persistence implementations and already has both in-memory and PostgreSQL adapters. No unresolved constitution violations remain beyond the historical retrofit.
