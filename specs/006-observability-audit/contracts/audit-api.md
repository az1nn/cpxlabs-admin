# Contract: Audit and Correlation API

## Common response correlation

Every API response includes:

```http
x-request-id: <opaque-server-generated-id>
```

For application errors, the existing error envelope carries the same value:

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "The requested action is not permitted",
    "requestId": "<same-value-as-x-request-id>"
  }
}
```

Clients must treat the value as opaque.

## `GET /api/audit-events`

Read-only bounded audit history. Requires `audit.read`.

### Query

```text
limit?: integer      default 50, min 1, max 100
cursor?: string      opaque continuation cursor
subjectType?: string optional exact subject type filter
subjectId?: string   optional exact subject id filter
actorId?: string     optional exact actor id filter
action?: string      optional exact action filter
```

### Success `200`

```json
{
  "data": [
    {
      "id": "audit-id",
      "actor": {
        "id": "user-id",
        "email": "admin@example.com",
        "name": "Admin User"
      },
      "action": "customers.update",
      "subject": {
        "type": "customer",
        "id": "cus_123"
      },
      "before": {
        "id": "cus_123",
        "name": "Old name",
        "email": "ops@example.com",
        "company": "Example",
        "status": "lead",
        "updatedAt": "2026-09-09T10:00:00.000Z"
      },
      "after": {
        "id": "cus_123",
        "name": "New name",
        "email": "ops@example.com",
        "company": "Example",
        "status": "active",
        "updatedAt": "2026-09-09T10:01:00.000Z"
      },
      "correlationId": "request-id",
      "tenantId": null,
      "occurredAt": "2026-09-09T10:01:00.000Z"
    }
  ],
  "nextCursor": "opaque-or-null"
}
```

### Authorization

- Admin reference role: allowed (`audit.read`)
- Manager: `403 FORBIDDEN`
- Viewer: `403 FORBIDDEN`
- no valid session: `401 AUTHENTICATION_REQUIRED`

### Pagination semantics

- newest-first by `(occurredAt DESC, id DESC)`;
- `limit` is capped at 100;
- `nextCursor` is null when no further records are available;
- cursor is opaque to clients and invalid cursor input returns the existing validation/error envelope.

## Audit action identifiers

Initial stable values:

```text
customers.create
customers.update
customers.delete
```

The action namespace intentionally matches application capability/domain naming but audit-read authorization is independent through `audit.read`.

## Mutation audit contract

There is no public `POST/PATCH/DELETE /api/audit-events` endpoint.

Customer mutations append audit internally only after authorization and validation and inside the same logical database transaction as the domain mutation.
