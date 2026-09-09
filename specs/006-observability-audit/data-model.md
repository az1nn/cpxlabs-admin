# Data Model: Observability and Audit

## AuditEvent

Durable immutable evidence for one committed auditable domain mutation.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Server/database generated immutable identifier. |
| `actorId` | string | Required authenticated Principal id. |
| `actorEmail` | string | Required stable human-readable actor identity at event time. |
| `actorName` | string | Required display name at event time. |
| `action` | string | Stable application action, initially `customers.create`, `customers.update`, `customers.delete`. |
| `subjectType` | string | Stable domain type, initially `customer`. |
| `subjectId` | string | Required domain identifier; remains useful after deletion. |
| `before` | JSON/null | Allowlisted safe pre-mutation snapshot when applicable. |
| `after` | JSON/null | Allowlisted safe post-mutation snapshot when applicable. |
| `correlationId` | string | Request correlation identifier that caused the mutation. |
| `tenantId` | string/null | Reserved future context; null in current non-tenant baseline. |
| `occurredAt` | timestamp | Immutable database/application occurrence time. |

### Invariants

- Application code exposes append and read operations only; no update/delete operation.
- `before`/`after` are domain allowlists, never raw request/session objects.
- Create: `before=null`, `after!=null`.
- Update: `before!=null`, `after!=null`.
- Delete: `before!=null`, `after=null`.
- Customer mutation and event append share the same database transaction.
- Failed/rolled-back/forbidden mutation has no successful customer audit event.

## CustomerAuditSnapshot

Allowlisted customer state persisted inside an AuditEvent.

```text
id
name
email
company
status
updatedAt
```

No request headers, credentials, session/provider data, arbitrary request metadata, or unrelated payload fields are included.

## CorrelationContext

Ephemeral per-request context rather than a database entity.

```text
requestId: UUID-like opaque string
```

The same value is exposed as the response `x-request-id`, used by the error envelope, and attached to logs/security/audit context. Trace identity is related operational context but does not replace the application request id.

## AuditCursor

Opaque transport cursor representing the last visible audit position.

Conceptual components:

```text
occurredAt
id
```

Clients treat the cursor as opaque. The server validates/decodes it and retrieves records older than that stable `(occurredAt,id)` position in newest-first order.

## Relationships

```text
Principal (logical)
   │ actorId
   ▼
AuditEvent ── subjectId ──> Customer (logical/current row may be absent)
```

No database foreign key from audit event to customer is required because customer deletion must not remove or invalidate historical audit evidence. Actor identity is snapshotted by stable id/email/name so audit history does not require mutable identity rows to remain queryable forever.
