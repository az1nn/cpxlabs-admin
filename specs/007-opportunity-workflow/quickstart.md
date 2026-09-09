# Quickstart Validation: Opportunity Workflow

## Prerequisites

```bash
pnpm install --frozen-lockfile
docker compose up -d postgres
cp apps/api/.env.example apps/api/.env
pnpm --filter @cpxlabs-admin/api db:migrate
pnpm --filter @cpxlabs-admin/api db:seed
```

Use the reference Admin/Manager/Viewer users provisioned by the explicit development seed. Do not use seed credentials as a production provisioning mechanism.

## 1. Validate lifecycle unit tests

```bash
pnpm --filter @cpxlabs-admin/api test
```

Expected:

- qualification → discovery accepted;
- discovery → proposal accepted;
- proposal → negotiation accepted;
- negotiation → won accepted;
- every non-terminal → lost accepted only with reason;
- skipped/backward/terminal transitions rejected.

## 2. Validate PostgreSQL workflow and concurrency

With `DATABASE_URL` configured:

```bash
pnpm --filter @cpxlabs-admin/api test
```

Expected integration evidence:

- create persists qualification/version 1;
- transition increments version once;
- two concurrent commands with the same expected version produce one committed transition and one workflow conflict;
- invalid/stale/not-found commands do not append successful opportunity audit events;
- committed create/transition and opportunity audit append atomically;
- safe opportunity snapshots contain only the documented allowlist.

## 3. Start reference API and web

```bash
pnpm --filter @cpxlabs-admin/api dev
pnpm --filter @cpxlabs-admin/web dev
```

Reference topology:

```text
web /api → Fastify → Opportunity workflow service → Prisma → PostgreSQL
                                      └─────────────→ durable AuditEvent
```

## 4. API workflow validation

Authenticate as Manager/Admin, then create:

```text
POST /api/opportunities
```

Verify returned state:

```text
stage = qualification
version = 1
```

Then execute:

```text
POST /api/opportunities/:id/commands/transition
{ targetStage: discovery, expectedVersion: 1 }
```

Expected:

```text
stage = discovery
version = 2
```

Retry a command with `expectedVersion: 1` and verify `WORKFLOW_CONFLICT` with no additional audit mutation.

Attempt qualification → proposal and verify `WORKFLOW_INVALID_TRANSITION`.

Verify no `PATCH /api/opportunities/:id` or opportunity DELETE route exists.

## 5. Role matrix

- Admin: list/detail/create/transition succeeds.
- Manager: list/detail/create/transition succeeds.
- Viewer: list/detail succeeds; direct create/transition API requests return `403 FORBIDDEN`.

## 6. Audit validation

As Admin:

```text
GET /api/audit-events?subjectType=opportunity&subjectId=<id>
```

Verify exactly one event per committed create/transition with request correlation and safe snapshots. Failed commands must not add successful opportunity audit events.

## 7. Frontend architecture gate (007B)

Verify the web uses a dedicated Opportunity service/client for transition commands and that the shared generic DataProvider has no `transition`, `advanceStage`, or Opportunity-specific method.

Browser acceptance must cover:

- Viewer read-only experience;
- Manager/Admin create;
- valid transition actions derived from current stage;
- loss reason requirement;
- terminal opportunity has no transition actions;
- stale conflict refreshes authoritative state;
- existing Customer E2E remains green.

## 8. Full repository gates

```bash
pnpm typecheck
pnpm test
pnpm build
pnpm test:storybook
pnpm e2e
```

All existing gates must remain green.
