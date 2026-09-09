# Research: Observability and Audit

## Decision 1 — Keep logs, telemetry, security events, and audit separate

**Decision**: Preserve Fastify/Pino structured logs and the existing security-event abstraction; add OpenTelemetry for server traces/metrics; persist business audit records independently in PostgreSQL.

**Rationale**: These data products have different reliability, retention, privacy, and query semantics. Durable business evidence must not depend on log shipping or a telemetry collector.

**Alternatives considered**:

- Treat structured logs as audit: rejected because log delivery/retention is not a transactional business guarantee.
- Adopt OpenTelemetry Logs immediately: rejected because OpenTelemetry JavaScript traces and metrics are stable while Logs remains in Development status.

## Decision 2 — Use the Fastify-maintained OpenTelemetry instrumentation

**Decision**: Use `@fastify/otel` 0.21.0 with the OpenTelemetry Node SDK 0.222.0 generation and HTTP instrumentation rather than deprecated Fastify instrumentation from the generic contrib package.

**Rationale**: `@fastify/otel` is maintained with Fastify and instruments Fastify request handlers/hooks. OpenTelemetry HTTP instrumentation supplies upstream/downstream HTTP propagation. Server instrumentation is opt-in through environment configuration; browser instrumentation is out of scope because OpenTelemetry JavaScript browser instrumentation remains experimental.

**Alternatives considered**:

- `@opentelemetry/instrumentation-fastify`: rejected in favor of the Fastify-maintained package.
- Custom tracing wrappers around every route: rejected because it pollutes domain routes and duplicates mature instrumentation.
- Browser tracing in this feature: deferred because browser instrumentation is experimental and not required for the server-side baseline.

## Decision 3 — Server-generated UUID request correlation

**Decision**: Generate an opaque UUID request identifier at the Fastify boundary, return it as `x-request-id`, and use the same identifier in error envelopes, security events, audit events, and structured request context.

**Rationale**: Process-local sequential IDs are not globally useful. Treating an arbitrary client-supplied request ID as authoritative risks collisions and log-context injection. Distributed trace propagation remains the OpenTelemetry concern; the application request ID remains a simple stable support identifier.

**Alternatives considered**:

- Reuse client `x-request-id` as authoritative: rejected for the baseline.
- Use trace ID as the only correlation identifier: rejected because audit/error contracts should not depend on tracing being enabled.

## Decision 4 — Atomic audit belongs in the mutation transaction

**Decision**: Introduce a customer mutation application service. The PostgreSQL implementation performs customer mutation and audit append inside one Prisma transaction. Routes depend on the service abstraction and never on Prisma.

**Rationale**: Writing audit after a repository mutation can create committed domain state without audit if the second write fails. A transaction is required to satisfy the feature's reliability guarantee.

**Alternatives considered**:

- Best-effort `repository.update(); audit.append()`: rejected because it permits audit gaps.
- Database trigger: rejected for the starter baseline because actor/capability/request context is application-owned and trigger logic would obscure the explicit application contract.
- Outbox/eventual audit: rejected for the current synchronous guarantee; a future event-driven architecture could add an outbox for external forwarding while retaining the local durable audit event.

## Decision 5 — Generic audit event, domain-specific snapshots

**Decision**: Persist a generic immutable `AuditEvent` envelope (`actor`, `action`, `subject`, `before`, `after`, correlation, time) while each audited domain provides its own allowlisted snapshot mapper.

**Rationale**: The envelope is reusable, but safe state selection is domain-specific. Storing raw request bodies or arbitrary objects would eventually leak secrets or unstable fields.

**Alternatives considered**:

- Serialize whole request body: rejected for privacy and coupling.
- Domain-specific audit tables for every resource: rejected as unnecessary duplication for the starter.

## Decision 6 — Cursor-based, read-only audit API

**Decision**: Add an Admin-only bounded `GET /api/audit-events` endpoint with an opaque cursor and newest-first ordering. No audit create/update/delete HTTP surface is exposed.

**Rationale**: An audit trail must be inspectable and pagination must remain stable while new events are appended. Offset pagination can shift under concurrent writes.

**Alternatives considered**:

- Offset/page-number audit pagination: rejected because append-heavy history can move between pages.
- Audit UI in this feature: deferred; API contract is enough to prove the reusable platform capability.

## Decision 7 — Pin fast-moving observability dependencies

**Decision**: Pin the initial observability stack exactly: `@fastify/otel` 0.21.0 and the selected OpenTelemetry experimental-package generation at 0.222.0 where applicable.

**Rationale**: OpenTelemetry Node SDK/instrumentation packages are explicitly labeled experimental/active development even though trace/metric APIs are stable. Exact pins prevent silent changes in instrumentation behavior.

**Alternatives considered**:

- Semver ranges for the observability SDK: rejected for the initial baseline.
- No instrumentation dependency: rejected because the feature requires a concrete trace-capable reference implementation.
