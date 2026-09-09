# Research: Opportunity Workflow

## Decision 1 — Explicit command API, not generic CRUD mutation

**Decision**: Opportunity reads use resource-specific query endpoints, creation uses a dedicated create operation, and stage movement uses `POST /api/opportunities/:opportunityId/commands/transition`. The generic `DataProvider` receives no workflow methods and there is no generic opportunity PATCH/DELETE route in this feature.

**Rationale**: Stage changes carry lifecycle invariants, concurrency semantics, terminal-state rules, and audit obligations. Modeling them as field updates would leak domain behavior into generic CRUD infrastructure and violate the architecture gate established by ADR-006/data-provider boundaries.

**Alternatives considered**:
- Generic `PATCH /opportunities/:id` with a `stage` field: rejected because it makes workflow invariants look like ordinary persistence updates.
- Add `advanceStage()` to `DataProvider`: rejected because the provider would become CRM/domain-specific.
- Generic command bus/framework: rejected as unnecessary internal framework surface for one reference workflow.

## Decision 2 — Fixed reference state machine

**Decision**: Use the reference graph:

```text
qualification → discovery → proposal → negotiation → won
      └──────────────┴──────────┴──────────→ lost
```

`lost` is reachable from every non-terminal stage with a required reason. `won` and `lost` are terminal. Backward/reopen transitions are outside the feature.

**Rationale**: A small explicit graph is understandable, testable, and strong enough to prove non-CRUD behavior without prematurely building a configurable workflow engine.

**Alternatives considered**:
- Configurable stage graph in database: rejected as premature framework/configuration complexity.
- Backward transitions: deferred because they introduce additional business semantics and audit interpretation.

## Decision 3 — Optimistic concurrency with version compare-and-swap

**Decision**: Persist integer `version`, require `expectedVersion` on every transition command, and commit transitions through a conditional update that includes the observed version. A zero-row conditional update is mapped to a stable workflow conflict after distinguishing missing rows.

**Rationale**: It prevents stale operators from overwriting newer workflow decisions without holding long-lived locks. It is deterministic under concurrent commands and easy for the web client to recover from by refreshing authoritative state.

**Alternatives considered**:
- Last-write-wins: rejected as unsafe for enterprise workflows.
- Pessimistic row locks exposed through application sessions: rejected as unnecessary complexity and poor fit for HTTP interaction.
- ETag-only contract: viable future transport representation, but explicit expectedVersion is simpler for the first reference domain command.

## Decision 4 — PostgreSQL/Prisma transaction remains the reference persistence adapter

**Decision**: Add an `Opportunity` Prisma model and implement create/transition + durable audit inside one Prisma transaction. Read queries remain behind an Opportunity repository interface.

**Rationale**: The repository already uses PostgreSQL 17 and Prisma 7.10.0 with transaction-backed customer audit. Reusing that persistence boundary proves the architecture rather than introducing another storage stack.

## Decision 5 — Safe integer transport for monetary minor units

**Decision**: The public contract uses `amountMinor: number` constrained to non-negative safe integers. PostgreSQL stores the value as `BIGINT`; the Prisma adapter maps between `bigint` and transport-safe numbers and rejects values outside JavaScript safe-integer range.

**Rationale**: Integer minor units avoid floating-point currency errors while preserving ergonomic JSON. `BIGINT` avoids the low ceiling of a 32-bit database integer.

**Alternatives considered**:
- Decimal string transport: accurate but adds parsing complexity not needed for the architecture gate.
- Floating-point amount: rejected for monetary correctness.

## Decision 6 — Calendar date for expected close date

**Decision**: Persist expected close date using PostgreSQL date semantics and expose `YYYY-MM-DD` in the transport contract.

**Rationale**: Expected close is a business calendar date, not an instant/timezone event.

## Decision 7 — Extend audit as a second resource, not a new history subsystem

**Decision**: Generalize the current audit DTO snapshot union and subject/action namespaces to include opportunities. Opportunity create and committed stage transitions append to the existing `audit_events` table using an explicit Opportunity snapshot mapper.

**Rationale**: Feature 006 intentionally created a reusable durable audit platform. Reusing it for a second resource proves that boundary while keeping resource-specific snapshot allowlists.

**Alternatives considered**:
- New `opportunity_history` table: rejected because it duplicates actor/correlation/audit infrastructure.
- Raw JSON request logging: rejected because it violates the safe allowlist and separation guarantees.

## Decision 8 — Typed capability matrix

**Decision**:

```text
Admin   → opportunities.read, opportunities.create, opportunities.transition
Manager → opportunities.read, opportunities.create, opportunities.transition
Viewer  → opportunities.read
```

The API remains authoritative. UI action visibility is only a UX affordance.

## Decision 9 — Frontend domain service boundary

**Decision**: Add an application-owned `OpportunityService`/HTTP implementation under the opportunity feature/platform boundary for list/detail/create/transition. TanStack Query owns remote state and invalidation. The existing generic `DataProvider` stays unchanged.

**Rationale**: This is the frontend half of the non-CRUD architecture gate: domain commands remain explicit and typed without creating an internal framework.

## Decision 10 — Two implementation slices

**Decision**:
- **007A / PR #12**: backend model, workflow state machine, capabilities, audit generalization, API, PostgreSQL integration/concurrency tests.
- **007B / new PR**: web resource/query/command UI, Storybook/accessibility, Playwright role/workflow journeys, Spec Kit convergence.

**Rationale**: Keeps review surfaces bounded while preserving one Spec Kit feature and honors the project rule that every stage gets a new MR rather than reusing an existing MR for later work.
