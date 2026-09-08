# ADR-0011 — PostgreSQL persistence behind repository boundaries

- Status: Accepted
- Date: 2026-09-08

## Context

The reference Fastify API needs a real persistence path without coupling HTTP routes, shared contracts or the React application to an ORM.

The persistence choice also needs to be conservative enough for an enterprise starter. At this decision point Prisma 8 is the current major, Prisma 7 remains officially supported, and Drizzle 1.0 is still pre-stable. The starter values a stable migration path and replaceable infrastructure over adopting the newest ORM major immediately.

## Decision

Use PostgreSQL as the default reference database and Prisma ORM `7.10.0` as the pinned reference adapter.

The following rules are architectural constraints:

1. `CustomerRepository` is the application persistence boundary.
2. `InMemoryCustomerRepository` remains the zero-infrastructure implementation for demos and tests.
3. `PrismaCustomerRepository` is an infrastructure adapter and is selected only when `DATABASE_URL` is configured.
4. Fastify routes receive repositories through dependency injection and do not import Prisma.
5. Prisma-generated models and error types do not escape the API infrastructure boundary.
6. Shared frontend/API contracts remain independent from the ORM.
7. PostgreSQL constraints and indexes enforce persistent invariants in addition to HTTP and TypeScript validation.
8. Schema migrations contain schema changes only. Reference/demo data is populated through an explicit idempotent seed command.
9. CI runs PostgreSQL 17, applies committed migrations, seeds reference data, executes repository integration tests and runs the browser CRUD journey through the persistent API.
10. Prisma, `@prisma/client` and the PostgreSQL driver adapter are pinned exactly for the reference persistence implementation.

## Rationale

PostgreSQL provides the relational capabilities expected from CRM, ERP and backoffice workloads while remaining portable across managed cloud providers.

Prisma 7 is deliberately one major behind the newest Prisma line. This is a stability choice, not a permanent restriction. Prisma 8 can be evaluated later without changing route contracts, shared DTOs or frontend data access because the ORM is isolated behind repositories.

Drizzle remains a valid future adapter candidate. No application-layer API depends on Prisma-specific behavior.

## Consequences

### Positive

- The frontend remains backend-agnostic.
- HTTP routes remain persistence-agnostic.
- ORM replacement is localized to infrastructure adapters.
- Tests can choose fast in-memory execution or real PostgreSQL integration.
- Database migrations are deterministic and production-safe.
- Persistent constraints such as customer status and unique email are enforced by PostgreSQL.

### Trade-offs

- The repository layer introduces explicit mapping code between Prisma and domain DTOs.
- CI now provisions PostgreSQL and therefore has a higher execution cost.
- Prisma client generation becomes part of API typecheck, test and build workflows.
- The reference implementation intentionally does not use the newest Prisma major.

## Validation gate

This decision is considered operationally validated only while the following journey remains green:

```text
React / TanStack Query
        ↓
HttpDataProvider
        ↓
Fastify routes
        ↓
CustomerRepository
        ↓
PrismaCustomerRepository
        ↓
PostgreSQL
```

The Playwright customer CRUD test must exercise this path in CI rather than silently falling back to the in-memory provider.
