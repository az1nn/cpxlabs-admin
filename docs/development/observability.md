# Observability and durable audit

## Concern boundaries

The reference API deliberately keeps four different concerns separate:

| Concern | Reference mechanism | Durability / authority |
|---|---|---|
| Operational request logs | Fastify/Pino | Operational evidence only |
| Security events | Structured Fastify/Pino events | Operational security evidence only |
| Traces and metrics | Optional OpenTelemetry + OTLP | Operational telemetry only |
| Domain audit | PostgreSQL `audit_events` | Durable application evidence |

OpenTelemetry exporters never become part of customer mutation correctness. A disabled or failed telemetry bootstrap does not disable the API or the durable audit path.

## Request correlation

Every API request receives a server-generated UUID and returns it in `x-request-id`. The same value is used in application error envelopes, security events, audit `correlationId`, and as the `cpx.request_id` span attribute when Fastify tracing is enabled.

Clients must treat request ids as opaque identifiers.

## Durable audit

Customer create/update/delete uses `CustomerMutationService`. In the Prisma reference adapter, the domain mutation and `AuditEvent` append run inside the same PostgreSQL transaction.

If audit persistence fails, the customer mutation rolls back. Forbidden, unauthenticated, validation, and not-found requests do not create successful customer audit events.

Audit snapshots are explicit allowlists. The application never persists request headers, cookies, passwords, session data, bearer tokens, provider objects, or arbitrary request bodies as audit metadata.

## Inspect audit history

Admin users have the project-owned `audit.read` capability and can query:

```text
GET /api/audit-events
```

Supported filters are `actorId`, `action`, `subjectType`, and `subjectId`, plus bounded `limit` and opaque `cursor` pagination. There are no public audit mutation endpoints.

## Enable OpenTelemetry locally

The default is disabled:

```env
OTEL_ENABLED=false
```

To send traces and metrics to an OTLP/HTTP collector:

```env
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
OTEL_SERVICE_NAME=cpxlabs-admin-api
```

`OTEL_EXPORTER_OTLP_ENDPOINT` is the collector base HTTP endpoint; the API appends `/v1/traces` and `/v1/metrics`.

Telemetry initializes before Fastify is loaded so HTTP and Fastify instrumentation can be registered correctly. Health checks opt out of Fastify spans. Fastify/Pino remains the logging implementation; OpenTelemetry Logs is not part of this reference baseline.
