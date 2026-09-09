# Quickstart: Validate Observability and Audit

## Prerequisites

- Node.js and pnpm versions required by the repository
- PostgreSQL 17 reference database
- Feature branch dependencies installed
- Reference authentication seed configured

## Setup

```bash
docker compose up -d postgres
cp apps/api/.env.example apps/api/.env
pnpm install --frozen-lockfile
pnpm --filter @cpxlabs-admin/api db:migrate
pnpm --filter @cpxlabs-admin/api db:seed
```

Start the reference API/web using the normal development workflow.

## Scenario A — Correlation

1. Sign in as the reference Admin.
2. Request a valid customer endpoint and inspect `x-request-id`.
3. Trigger a known application error.
4. Verify the error envelope `requestId` equals the response `x-request-id`.
5. Verify security/structured log context for the request uses the same identifier.

Expected: every response has one non-empty correlation id and errors expose the same value.

## Scenario B — Successful atomic audit

1. Create a customer as Admin.
2. Update the customer.
3. Delete the customer.
4. Query `GET /api/audit-events?subjectId=<id>` as Admin.

Expected:

- exactly three matching events;
- action sequence identifies create/update/delete;
- update carries safe before/after state;
- delete remains inspectable after the customer row no longer exists;
- each event has actor and correlation id.

## Scenario C — Authorization

1. Query audit history as Admin: expect success.
2. Query as Manager: expect `403 FORBIDDEN`.
3. Query as Viewer: expect `403 FORBIDDEN`.
4. Query without a session: expect `401 AUTHENTICATION_REQUIRED`.

## Scenario D — Audit rollback

Run the PostgreSQL integration test that injects an audit persistence failure during a customer mutation.

Expected: the request fails and a subsequent customer read proves the domain mutation did not commit.

## Scenario E — No false domain audit

Exercise forbidden and invalid customer mutations.

Expected: no successful customer mutation audit event is appended for the rejected operation, while security/operational evidence can still be emitted.

## Scenario F — Telemetry optionality

Run the test suite with telemetry disabled, then enable the reference telemetry bootstrap against a test/collector endpoint.

Expected: customer and audit behavior is unchanged. Trace exporting is operationally optional and does not become a correctness dependency.

## Full gate

```bash
pnpm typecheck
pnpm test
pnpm build
pnpm test:storybook
pnpm e2e
```

All existing authentication, authorization, accessibility and browser gates must remain green.
