# Implementation Plan: Observability and Audit

**Branch**: `feat/006-observability-audit` | **Date**: 2026-09-09 | **Spec**: [spec.md](./spec.md)

## Summary

Add server-generated request correlation, optional OpenTelemetry tracing/metrics, and a durable append-only audit platform. Customer create/update/delete become the reference audited mutations and execute with their audit append inside one PostgreSQL transaction. Fastify routes depend on application abstractions; Prisma and telemetry exporters remain infrastructure details.

## Technical Context

**Language/Version**: TypeScript 7.x, Node.js >=22.12, React 19

**Primary Dependencies**: Fastify 5.x, Prisma 7.10.0, PostgreSQL 17, Better Auth 1.7.3, `@fastify/otel` 0.21.0, OpenTelemetry Node/HTTP/OTLP packages pinned to the selected 0.222.0 generation

**Storage**: Existing PostgreSQL database plus append-only `AuditEvent` records

**Testing**: Vitest unit/API/PostgreSQL integration tests; existing Storybook/axe and Playwright gates must remain green

**Target Platform**: Node.js Fastify reference API behind same-origin browser edge; telemetry exporter optional

**Project Type**: pnpm/Turborepo monorepo

**Performance Goals**: Correlation must add negligible overhead; audit adds one transactional insert per audited mutation; audit list is indexed and bounded; tracing can be disabled with no domain semantic change

**Constraints**: Audit and mutation are atomic; audit API read-only; server authority preserved; no secret-bearing raw payloads in snapshots; no ORM/OTel vendor types outside infrastructure boundaries; strict TypeScript and CI remain unchanged

**Scale/Scope**: Customer mutations prove the reusable pattern; audit history is append-heavy and cursor-paginated; UI viewer, retention, SIEM export and multi-tenancy are deferred

## Constitution Check

| Principle | Status | Evidence |
|---|---|---|
| Spec Before Implementation | PASS | `006` spec/checklist precede production code. |
| Backend-Agnostic Frontend | PASS | Feature is API/platform-focused; existing web contracts remain unchanged except correlation headers already transport-safe. |
| Server Authority | PASS | Audit actor derives from server Principal; audit-read is server-enforced. |
| Strict Types / Tests / CI | PASS | PostgreSQL atomicity, authz matrix, error correlation and browser regressions are explicit gates. |
| Simplicity / Replaceability | PASS | Mature Fastify OTel instrumentation; one generic audit envelope; no new service/process. |
| Monolith First | PASS | Audit remains inside the reference API/PostgreSQL transaction boundary. |

No constitution violations require Complexity Tracking.

## Architecture Decisions

1. Fastify generates a UUID request id and exposes `x-request-id` on every response.
2. Error envelopes continue using their existing `requestId` field, populated from the same Fastify request id.
3. Security events keep Fastify/Pino and inherit the request id; they are not durable audit.
4. OpenTelemetry instrumentation is server-only and optional; domain routes do not import OTel APIs.
5. `@fastify/otel` is the Fastify instrumentation path; generic/deprecated Fastify instrumentation is not introduced.
6. `AuditEvent` is generic and append-only; customer snapshots are explicit allowlists.
7. `audit.read` is added to typed capabilities and granted only to Admin in the reference policy.
8. Customer reads remain on `CustomerRepository`; mutations move behind `CustomerMutationService` so the PostgreSQL implementation can atomically mutate + audit.
9. `PrismaCustomerMutationService` executes inside `prisma.$transaction`; a failed audit insert rejects/rolls back the domain mutation.
10. Audit pagination uses an opaque cursor encoding `(occurredAt,id)` and newest-first order.
11. Audit retention/export/UI are intentionally deferred.

## Project Structure

```text
apps/api/src/
├── platform/
│   ├── observability/
│   │   ├── correlation.ts
│   │   └── telemetry.ts
│   └── audit/
│       ├── audit.types.ts
│       ├── audit.repository.ts
│       ├── audit.prisma-repository.ts
│       └── audit.routes.ts
├── modules/customers/
│   ├── customer.audit.ts
│   ├── customer.mutation-service.ts
│   ├── customer.prisma-mutation-service.ts
│   └── customer.routes.ts
└── server.ts

apps/api/prisma/
├── schema.prisma
└── migrations/<timestamp>_observability_audit/

packages/contracts/src/
└── audit.ts

packages/authorization/src/
└── index.ts
```

## Phase 0: Research

Completed in [research.md](./research.md): concern separation, Fastify/OpenTelemetry integration, request-id policy, atomic audit transaction, snapshot policy, cursor pagination, and dependency pinning.

## Phase 1: Design & Contracts

- Define `AuditEvent` persistence/entity semantics and immutable lifecycle.
- Define customer audit snapshot allowlist.
- Define `GET /api/audit-events` cursor contract.
- Define request correlation response/error behavior.
- Define atomic mutation service boundary and PostgreSQL transaction expectations.
- Define validation guide for success/rollback/forbidden/read authorization.

Outputs: [data-model.md](./data-model.md), [contracts/audit-api.md](./contracts/audit-api.md), [quickstart.md](./quickstart.md)

## Post-Design Constitution Re-check

| Principle | Status | Result |
|---|---|---|
| ORM isolation | PASS | Prisma transaction code stays inside API infrastructure implementation. |
| Provider isolation | PASS | OTel exporter/instrumentation stays in observability bootstrap. |
| Server authority | PASS | Actor and audit-read capability resolve from server Principal. |
| Audit correctness | PASS | Atomic transaction is a mandatory design invariant, not best-effort logging. |
| Testing | PASS | Failure injection and no-audit-on-denial scenarios are explicit. |

## Complexity Tracking

The new `CustomerMutationService` is justified because atomic audit requires an application transaction boundary that the existing CRUD repository cannot express safely. No additional package or microservice is introduced.
