# Tasks: HTTP API and PostgreSQL Persistence

**Status**: Implemented (Retrofitted)

## Web Deployment and HTTP Adapter

- [x] T001 Add Vercel SPA configuration and deployment documentation
- [x] T002 Add typed environment configuration for demo/http provider selection
- [x] T003 Implement `HttpDataProvider`
- [x] T004 Implement stable frontend API error mapping
- [x] T005 Add shared `ApiErrorEnvelope` contract
- [x] T006 Preserve demo mode as zero-config frontend fallback

## Fastify Reference API

- [x] T007 Create optional `apps/api` workspace
- [x] T008 Add `/health` and Customers CRUD routes
- [x] T009 Add Fastify request/response JSON Schemas
- [x] T010 Add stable application error envelope with request correlation
- [x] T011 Keep in-memory repository for isolated API tests
- [x] T012 Run API tests through `fastify.inject()`

## PostgreSQL Persistence

- [x] T013 Convert `CustomerRepository` to async boundary
- [x] T014 Pin Prisma 7.10.0 and configure PostgreSQL adapter
- [x] T015 Add `PrismaCustomerRepository` without leaking generated types
- [x] T016 Add PostgreSQL customer schema, status enum, indexes, and unique email
- [x] T017 Add explicit migration
- [x] T018 Separate reference seed from migration
- [x] T019 Add local `compose.yml` and database developer commands/docs
- [x] T020 Add repository integration tests against PostgreSQL 17

## Real End-to-End Gate

- [x] T021 Configure Vite preview proxy for same-origin `/api`
- [x] T022 Start Fastify and Vite preview from Playwright
- [x] T023 Assert real GET/POST/PATCH/DELETE traffic in customer journey
- [x] T024 Provision PostgreSQL 17 in CI browser and quality jobs
- [x] T025 Apply migrations and explicit seed in CI
- [x] T026 Validate React -> HTTP -> Fastify -> Prisma -> PostgreSQL in Playwright
- [x] T027 Fix Prisma generated ESM imports for production Node execution
- [x] T028 Preserve Playwright report artifact upload without weakening test gates
- [x] T029 Pass frozen install/typecheck/tests/build/Storybook/a11y/E2E CI
- [x] T030 Mark feature as historical retrofit
