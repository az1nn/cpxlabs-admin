# Contract: Opportunity Workflow API

All endpoints use the existing cookie-session authentication, application-owned Principal/capability authorization, stable error envelope, and `x-request-id` response correlation.

## Opportunity DTO

```json
{
  "id": "opp_123",
  "name": "Enterprise Renewal",
  "accountName": "Acme Brasil",
  "amountMinor": 12500000,
  "currency": "BRL",
  "expectedCloseDate": "2026-11-30",
  "stage": "proposal",
  "version": 3,
  "lossReason": null,
  "createdAt": "2026-09-09T15:00:00.000Z",
  "updatedAt": "2026-09-09T15:10:00.000Z"
}
```

## `GET /api/opportunities`

Requires `opportunities.read`.

### Query

```text
page: integer       default 1, min 1
pageSize: integer   default 25, min 1, max 100
search?: string
sort?: name | accountName | amountMinor | expectedCloseDate | stage | updatedAt
direction?: asc | desc
filter.stage?: qualification | discovery | proposal | negotiation | won | lost
```

### Success `200`

```json
{
  "data": ["<Opportunity DTO>"],
  "total": 42
}
```

## `GET /api/opportunities/:opportunityId`

Requires `opportunities.read`.

### Success `200`

Returns one Opportunity DTO.

### Missing

`404 not_found` using the existing error envelope.

## `POST /api/opportunities`

Requires `opportunities.create`.

### Request

```json
{
  "name": "Enterprise Renewal",
  "accountName": "Acme Brasil",
  "amountMinor": 12500000,
  "currency": "BRL",
  "expectedCloseDate": "2026-11-30"
}
```

The request has no `stage`, `version`, or `lossReason` field.

### Success `201`

Returns Opportunity DTO with:

```text
stage=qualification
version=1
lossReason=null
```

A successful create appends one durable `opportunities.create` audit event inside the same transaction.

## `POST /api/opportunities/:opportunityId/commands/transition`

Requires `opportunities.transition`.

### Request — forward/won transition

```json
{
  "targetStage": "discovery",
  "expectedVersion": 1
}
```

### Request — lost transition

```json
{
  "targetStage": "lost",
  "expectedVersion": 2,
  "lossReason": "Customer selected incumbent renewal"
}
```

### Success `200`

Returns the updated Opportunity DTO. `version` is exactly `expectedVersion + 1`.

A successful transition appends one durable `opportunities.stage.change` audit event in the same transaction.

### Invalid lifecycle transition

`409`:

```json
{
  "error": {
    "code": "WORKFLOW_INVALID_TRANSITION",
    "message": "The requested opportunity transition is not allowed",
    "requestId": "<same as x-request-id>"
  }
}
```

Examples:

- qualification → proposal;
- discovery → qualification;
- won → any target;
- lost → any target;
- target lost without non-blank loss reason.

### Stale optimistic version

`409`:

```json
{
  "error": {
    "code": "WORKFLOW_CONFLICT",
    "message": "The opportunity changed since it was loaded",
    "details": {
      "expectedVersion": 2,
      "currentVersion": 3
    },
    "requestId": "<same as x-request-id>"
  }
}
```

The caller should refresh authoritative opportunity state before presenting/retrying a new command.

### Missing opportunity

`404 not_found`.

## Intentionally absent generic mutation endpoints

The feature does **not** define:

```text
PATCH  /api/opportunities/:opportunityId
PUT    /api/opportunities/:opportunityId
DELETE /api/opportunities/:opportunityId
```

There is no transport path for directly assigning stage/version/lossReason as generic editable fields.

## Authorization matrix

| Operation | Admin | Manager | Viewer |
|---|---:|---:|---:|
| List/detail | allow | allow | allow |
| Create | allow | allow | deny |
| Transition command | allow | allow | deny |

The API enforces this matrix independently of frontend visibility.

## Audit extension

New durable audit namespaces:

```text
action: opportunities.create
subject.type: opportunity

action: opportunities.stage.change
subject.type: opportunity
```

Opportunity snapshots use the allowlist in `data-model.md` and reuse the existing correlation/actor envelope.
