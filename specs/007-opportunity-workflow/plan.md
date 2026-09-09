# Implementation Plan: Opportunity Workflow

**Branch**: `feat/007-opportunity-workflow`  
**Spec**: `specs/007-opportunity-workflow/spec.md`

## Summary

Add Opportunity as the repository's first explicit non-CRUD workflow reference. The implementation introduces a finite server-authoritative state machine, optimistic concurrency through `expectedVersion`, resource-specific query/command APIs, typed opportunity capabilities, PostgreSQL persistence, reusable durable audit, and later a domain-specific web workflow client/UI. The generic frontend `DataProvider` remains unchanged.

## Technical Context

- **Frontend**: React 19 + Vite 8 + TypeScript strict + TanStack Router/Query/Table + RHF/Zod + owned UI package.
- **Backend**: Fastify 5 modular monolith.
- **Persistence**: PostgreSQL 17 through Prisma 7.10.0.
- **Authentication/session**: Better Auth behind application-owned Principal/RequestContext.
- **Authorization**: project-owned typed capability policy; API authoritative.
- **Audit**: existing append-only PostgreSQL audit platform from feature 006.
- **Testing**: Vitest, Fastify inject, PostgreSQL integration, Storybook/axe, Playwright.
- **Deployment**: same-origin `/api` reference topology; no new service.

No unresolved `NEEDS CLARIFICATION` items remain.

## Constitution Check — Pre-design

### Spec before implementation
PASS. `spec.md`, quality checklist, and this plan precede production code.

### Backend-agnostic frontend
PASS. Web commands will target an application-owned Opportunity service contract. The generic DataProvider is intentionally not extended with CRM commands.

### Server-authoritative authorization
PASS. Opportunity capabilities gate every API read/create/transition operation. UI visibility does not grant authority.

### Strict TypeScript and CI
PASS. New packages/types remain inside existing strict workspaces and existing quality/browser gates are preserved.

### Simplicity over premature frameworks
PASS. A small explicit workflow module/state machine is preferred over a configurable workflow engine or command-bus framework.

## Architecture

```text
Web opportunity routes/components
        ↓
TanStack Query
        ↓
OpportunityService (domain-specific frontend boundary)
        ↓ HTTP
Fastify opportunity routes
        ↓
AuthorizationGuards
        ↓
OpportunityWorkflowService
        ├── lifecycle state machine
        ├── optimistic version check
        └── audit append
        ↓
Prisma $transaction
        ├── Opportunity
        └── AuditEvent
        ↓
PostgreSQL 17
```

Read paths use `OpportunityRepository` for bounded list/detail retrieval. Mutation paths use `OpportunityWorkflowService`; stage is never writable through a generic repository route.

## Domain Lifecycle

```text
qualification → discovery → proposal → negotiation → won
      └──────────────┴──────────┴──────────→ lost
```

Rules:

- create always begins at `qualification`, version `1`;
- only the next forward stage is allowed;
- every non-terminal stage may transition to `lost` with non-blank reason;
- `won` and `lost` are terminal;
- every successful transition increments version exactly once;
- all transition commands require `expectedVersion`;
- stale commands return stable workflow conflict;
- invalid transition returns stable workflow invalid-transition error;
- missing id remains standard not-found.

## Persistence Design

### Opportunity

Prisma model fields:

```text
id                String @id @default(cuid())
name              String
accountName       String
amountMinor       BigInt
currency          String
expectedCloseDate DateTime @db.Date
stage             OpportunityStage
version           Int @default(1)
lossReason        String?
createdAt         DateTime @default(now())
updatedAt         DateTime @updatedAt
```

Indexes:

- stage;
- expectedCloseDate;
- updatedAt;
- accountName.

No delete route is added. No public generic stage update route exists.

### Optimistic transition transaction

Within one Prisma transaction:

1. read opportunity by id;
2. return not-found if missing;
3. compare persisted `version` with `expectedVersion`;
4. validate lifecycle target/loss reason;
5. perform conditional update `where id + version` (via `updateMany`) and increment version;
6. if conditional update count is zero, return workflow conflict;
7. reload updated opportunity;
8. append `opportunities.stage.change` audit event;
9. commit both together.

This preserves at-most-one winner when concurrent commands use the same observed version.

## Audit Generalization

Feature 006 remains the audit authority. Contracts are extended, not replaced:

```text
AuditSubjectType = customer | opportunity
AuditAction += opportunities.create | opportunities.stage.change
AuditSnapshot = CustomerAuditSnapshot | OpportunityAuditSnapshot
```

`OpportunityAuditSnapshot` is an explicit allowlist:

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

No auth/session/header/raw request data is admitted.

## API Surface

```text
GET  /api/opportunities
GET  /api/opportunities/:opportunityId
POST /api/opportunities
POST /api/opportunities/:opportunityId/commands/transition
```

Intentionally absent:

```text
PATCH  /api/opportunities/:opportunityId
DELETE /api/opportunities/:opportunityId
```

Stable command-specific error codes are added to the shared error envelope:

```text
WORKFLOW_INVALID_TRANSITION
WORKFLOW_CONFLICT
```

## Frontend Boundary

007B adds:

```text
features/opportunities/
  api/opportunity-service.ts
  api/http-opportunity-service.ts
  queries/
  components/
  routes/
```

The generic `platform/data/DataProvider` is not modified with transition/advance methods.

Resource registry entry:

```text
list: /opportunities
create: /opportunities/new
show: /opportunities/:id
edit: absent
```

## Capability Policy

```text
Admin   opportunities.read/create/transition
Manager opportunities.read/create/transition
Viewer  opportunities.read
```

## Testing Strategy

### Unit

- lifecycle transition matrix;
- loss-reason semantics;
- DTO/domain mapping;
- capability matrix;
- frontend service URL/command serialization;
- valid-action derivation.

### API/Fastify

- list/detail/create authorization;
- command authorization;
- no generic PATCH/DELETE surface;
- stable invalid-transition/conflict envelopes;
- request-id propagation.

### PostgreSQL integration

- create starts qualification/version 1;
- every documented valid transition;
- invalid/skipped/terminal transitions leave state unchanged;
- two concurrent commands with same expected version yield one success/one conflict;
- create/transition audit atomicity and exactly-one semantics;
- failed/stale/invalid commands append zero audit;
- safe opportunity snapshots.

### Browser (007B)

- Viewer read-only list/detail;
- Manager/Admin create;
- valid forward transition;
- loss reason flow;
- terminal state action absence;
- stale conflict triggers authoritative refresh;
- existing Customer journeys remain green.

## Implementation Slices

### 007A — PR #12

- Spec Kit artifacts through analyze;
- opportunity contracts/capabilities;
- Prisma model/migration;
- audit generalization;
- state machine;
- repository/workflow service;
- Fastify routes;
- PostgreSQL/API/unit tests;
- backend docs/ADR;
- quality CI green.

### 007B — New MR

- frontend OpportunityService;
- routes/resource registry/UI;
- Storybook/a11y;
- Playwright role/workflow/concurrency recovery;
- task reconciliation;
- full convergence and final CI.

## Constitution Check — Post-design

PASS. The design introduces no new framework, preserves DataProvider/backend boundaries, keeps authorization server-authoritative, extends the established transactional audit platform, and has explicit CI/architecture tests. No constitution exception is required.
