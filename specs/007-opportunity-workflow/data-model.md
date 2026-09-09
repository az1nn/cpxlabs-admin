# Data Model: Opportunity Workflow

## Opportunity

Reference CRM aggregate controlled by explicit lifecycle commands.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Server-generated immutable identifier. |
| `name` | string | Required, trimmed, 1–160 chars. |
| `accountName` | string | Required, trimmed, 1–160 chars. |
| `amountMinor` | integer | Required non-negative safe integer in minor currency units. |
| `currency` | string | Required uppercase three-letter currency code. |
| `expectedCloseDate` | date | Required `YYYY-MM-DD` business calendar date. |
| `stage` | enum | `qualification`, `discovery`, `proposal`, `negotiation`, `won`, `lost`. |
| `version` | integer | Starts at 1; increments exactly once per committed stage transition. |
| `lossReason` | string/null | Required non-blank when stage is `lost`; null otherwise. |
| `createdAt` | timestamp | Server-generated immutable creation time. |
| `updatedAt` | timestamp | Server-maintained update time. |

### Creation invariants

- Client does not supply `stage`, `version`, `lossReason`, `createdAt`, or `updatedAt`.
- New rows always use `stage=qualification`, `version=1`, `lossReason=null`.
- Amount is stored as PostgreSQL `BIGINT` and mapped to a JSON safe integer.
- Expected close date uses date semantics, not timestamp/timezone semantics.

## OpportunityStage

```text
qualification
discovery
proposal
negotiation
won
lost
```

### Transition graph

```text
qualification → discovery → proposal → negotiation → won
      └──────────────┴──────────┴──────────→ lost
```

Allowed transitions:

| Current | Allowed targets |
|---|---|
| qualification | discovery, lost |
| discovery | proposal, lost |
| proposal | negotiation, lost |
| negotiation | won, lost |
| won | none |
| lost | none |

`lost` requires `lossReason`. Every other target requires `lossReason` to be absent/ignored as null in persisted state.

## OpportunityTransitionCommand

Ephemeral command contract, not a persistent entity.

| Field | Type | Rules |
|---|---|---|
| `targetStage` | OpportunityStage | Must be a valid target from current persisted stage. |
| `expectedVersion` | integer | Required positive integer observed by caller. |
| `lossReason` | string/undefined | Required only for target `lost`; trimmed and non-blank. |

### Command outcome

Successful command:

```text
current version N
      ↓ valid + compare-and-swap
new version N+1
```

Failed stale/invalid/not-found/forbidden commands leave stage/version unchanged and append no successful opportunity audit event.

## OpportunityAuditSnapshot

Allowlisted immutable snapshot embedded in generic audit evidence.

```text
id
name
accountName
amountMinor
currency
expectedCloseDate
stage
version
lossReason
updatedAt
```

No authentication credentials, provider sessions, cookies, headers, authorization tokens, request bodies, or arbitrary metadata are included.

## Audit extension

The generic `AuditEvent` storage from feature 006 is reused.

New action identifiers:

```text
opportunities.create
opportunities.stage.change
```

New subject type:

```text
opportunity
```

Create event:

```text
before = null
after  = OpportunityAuditSnapshot
```

Transition event:

```text
before = OpportunityAuditSnapshot
after  = OpportunityAuditSnapshot
```

Opportunity and AuditEvent are intentionally not linked by a database foreign key; audit evidence remains interpretable independent of future lifecycle/storage changes.

## Relationships

```text
Principal (logical)
   │ actor
   ▼
AuditEvent ── subjectId ──> Opportunity (logical)

Opportunity
   └── stage + version form workflow state
```

## Persistence indexes

Reference PostgreSQL indexes:

- Opportunity(stage)
- Opportunity(expectedCloseDate)
- Opportunity(updatedAt)
- Opportunity(accountName)

Existing audit indexes continue to serve subject/action/correlation retrieval.
