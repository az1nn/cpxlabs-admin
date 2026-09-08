# Feature Specification: HTTP API and PostgreSQL Persistence

**Feature Branch**: historical retrofit

**Created**: 2026-09-08

**Status**: Implemented (Retrofitted)

**Retrofit Notice**: This specification documents behavior implemented before Spec Kit adoption.

## User Scenarios & Testing

### User Story 1 - Deploy the web application independently (Priority: P1)

As a team, I can deploy the Vite SPA to Vercel in zero-backend demo mode or point the same application at an HTTP backend through environment configuration.

**Independent Test**: Build the Vercel web project with demo provider enabled, then switch to HTTP mode without changing feature components.

### User Story 2 - Execute customer CRUD through a real HTTP contract (Priority: P1)

As an application user, customer list/create/show/edit/delete actions work through a REST API while the frontend remains coupled only to `DataProvider` and shared API contracts.

**Independent Test**: Playwright observes real GET/POST/PATCH/DELETE traffic while completing the customer CRUD journey.

### User Story 3 - Persist reference data in PostgreSQL (Priority: P1)

As a reference-backend operator, customer data persists through PostgreSQL behind a repository boundary, with migrations separated from optional development seed data.

**Independent Test**: Apply migrations to an empty PostgreSQL instance, seed explicitly, run repository integration tests, then complete browser CRUD through Fastify and Prisma.

### Edge Cases

- HTTP errors must map to a stable frontend error model rather than leaking Fastify/ORM internals.
- Seed data must never be embedded in schema migrations.
- A database implementation must not leak generated Prisma types through shared contracts.
- SPA deep links must resolve correctly on Vercel.
- ESM output from generated Prisma code must remain executable after TypeScript production compilation.

## Requirements

### Functional Requirements

- **FR-001**: `apps/web` MUST support environment-selected `demo` and `http` data providers.
- **FR-002**: The HTTP provider MUST serialize list pagination/search/filter/sort state into the REST contract.
- **FR-003**: Shared API errors MUST use a stable envelope with code/message and optional details/request ID.
- **FR-004**: The optional reference API MUST use Fastify and expose health plus Customers CRUD endpoints.
- **FR-005**: Fastify request/response schemas MUST validate and constrain transport payloads.
- **FR-006**: Persistence MUST be accessed through an async `CustomerRepository` contract.
- **FR-007**: The reference persistent adapter MUST use PostgreSQL 17 and pinned Prisma 7.10.0 behind the repository.
- **FR-008**: Database schema changes MUST be applied through explicit migrations.
- **FR-009**: Reference/demo seed data MUST be executed separately from migrations.
- **FR-010**: CI MUST validate migrations, seed, repository integration, API tests, production build, and real browser CRUD against PostgreSQL.
- **FR-011**: The Vercel SPA MUST support fallback routing for deep links while preserving `/api/*` behavior.

### Key Entities

- **ApiErrorEnvelope**: Transport-safe structured error returned by the API.
- **CustomerRepository**: Application persistence boundary independent of Prisma.
- **PrismaCustomerRepository**: Reference PostgreSQL infrastructure adapter.
- **CustomerStatus**: Database-constrained customer lifecycle enum (`lead`, `active`, `inactive`).

## Success Criteria

- **SC-001**: The same Customers UI works in demo and HTTP modes without feature-level infrastructure changes.
- **SC-002**: Playwright passes through React -> HttpDataProvider -> Fastify -> Prisma -> PostgreSQL.
- **SC-003**: Migrations can initialize a clean PostgreSQL database without inserting demo records.
- **SC-004**: Repository integration tests execute against real PostgreSQL in CI.
- **SC-005**: Production Node output starts successfully with generated Prisma ESM imports.

## Assumptions

- Same-origin browser/API topology is the preferred reference deployment model.
- Fastify and Prisma are reference implementations rather than mandatory frontend platform dependencies.
