# Opportunity workflow extension guide

The reference Opportunity feature is an architecture gate for domain workflows that must not be reduced to generic CRUD.

## Boundary

The generic `DataProvider` remains limited to list/get/create/update/delete resource persistence. Opportunity stage changes are business commands and therefore use the domain-specific `OpportunityService.transition()` method and the server command endpoint:

```text
POST /api/opportunities/:opportunityId/commands/transition
```

Do not add `transition`, `executeCommand`, `advanceStage`, or Opportunity-specific methods to `DataProvider`.

## State ownership

- TanStack Router owns list pagination, search, filtering and sorting in the URL.
- TanStack Query owns remote Opportunity list/detail cache.
- React Hook Form + Zod own create-form state and client-side input feedback.
- PostgreSQL/Fastify own authoritative Opportunity stage and version.
- Frontend workflow actions are suggestions derived from the current DTO; they are not authorization or lifecycle enforcement.

## Extending the lifecycle

When adding a stage or transition:

1. Update the shared `OpportunityStage` contract.
2. Update the backend transition matrix first.
3. Add/adjust PostgreSQL constraints or migration when persistence shape changes.
4. Update backend lifecycle, concurrency and atomic-audit tests.
5. Update frontend `suggestedOpportunityTargets()` only after the backend rule exists.
6. Add browser coverage for the new transition and terminal semantics.

Never implement a frontend-only transition. The API must reject invalid, skipped, backward and terminal transitions independently of UI visibility.

## Optimistic concurrency

Every transition command sends the currently loaded `expectedVersion`. The backend performs compare-and-swap against `id + version` and increments the version exactly once on success.

A `WORKFLOW_CONFLICT` means the local DTO is stale. The web application must:

1. not automatically retry the command;
2. refetch authoritative detail state;
3. invalidate affected Opportunity lists;
4. tell the operator the record changed;
5. require a fresh user decision before another command.

## Money boundary

`Opportunity.amountMinor` is always an integer count of currency minor units. Do not persist floating-point major amounts and do not assume all currencies use two decimal places.

The web form keeps the operator input as a decimal string until submit. `majorAmountToMinorUnits()` resolves the selected currency's fraction digits and performs the major-to-minor conversion with `BigInt`, then verifies the result fits the shared safe-integer transport range before producing the API `number`.

Examples:

```text
BRL 125000.50 -> 12500050  (2 fraction digits)
JPY 1250      -> 1250      (0 fraction digits)
KWD 1.234     -> 1234      (3 fraction digits)
```

List/detail display uses the same currency fraction scale. If a future product requires a canonical currency catalogue, exchange rates, arbitrary precision beyond JavaScript safe integers, or locale-aware free-form parsing, start that as a separate money/domain specification rather than widening the Opportunity form ad hoc.

## Audit

Opportunity create and transition audit rows are committed in the same database transaction as the domain mutation. Do not move required durable audit to an asynchronous UI call, event handler, best-effort logger or post-commit callback.

New audit snapshots must remain resource-specific and allowlisted. Do not serialize arbitrary request bodies, authentication data or infrastructure objects into audit JSON.

## Authorization

Reference capabilities are:

```text
opportunities.read
opportunities.create
opportunities.transition
```

Admin and Manager can create/transition; Viewer is read-only. UI capability checks improve UX only. Fastify guards remain authoritative for every request.

## Resource Registry

Opportunity deliberately registers only:

```text
list   /opportunities
show   /opportunities/:id
create /opportunities/new
```

There is no generic edit/delete route. If future requirements introduce editable non-workflow Opportunity fields, prefer a narrowly scoped domain command or explicitly document why a generic edit surface is safe before adding one.

## Required regression gates

A workflow change is incomplete until the following remain green:

- strict TypeScript;
- unit/domain transition tests;
- PostgreSQL repository/workflow tests;
- optimistic concurrency test;
- atomic audit rollback test;
- authorization matrix;
- currency-aware minor-unit conversion tests;
- DataProvider CRUD-only architecture assertion;
- Storybook + axe states for the workflow panel;
- Playwright read-only, successful transition, terminal and stale-version recovery journeys.
