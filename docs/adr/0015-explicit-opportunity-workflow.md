# ADR-0015: Explicit Opportunity Workflow Commands

**Status:** Accepted  
**Date:** 2026-09-09

## Context

The starter needs to prove it supports domain workflows that cannot be reduced to generic CRUD without leaking business rules into a DataProvider or allowing clients to assign lifecycle state directly.

## Decision

Opportunity lifecycle changes use explicit application commands. The API exposes read/create endpoints plus `POST /api/opportunities/:id/commands/transition`; it intentionally exposes no generic Opportunity PATCH/PUT/DELETE route.

The reference lifecycle is an explicit state machine: `qualification → discovery → proposal → negotiation → won`, with `lost` reachable from any non-terminal stage. `won` and `lost` are terminal.

Every transition command carries `expectedVersion`. PostgreSQL commits transitions using compare-and-swap semantics on `(id, version)` and increments version exactly once. A stale command returns `WORKFLOW_CONFLICT` and appends no successful audit event.

Opportunity creation and successful transitions append durable audit evidence in the same PostgreSQL transaction as the domain change. Audit snapshots remain resource-specific allowlists.

The generic DataProvider remains CRUD-only and is not extended with `advanceStage`, `transitionOpportunity`, or similar domain commands. The web uses a dedicated OpportunityService.

## Consequences

- Business lifecycle rules stay server-authoritative and directly testable.
- Optimistic concurrency prevents silent lost updates without pessimistic locks.
- Workflow code is intentionally explicit rather than a generic configurable engine.
- Additional resources may use their own domain services/commands without changing DataProvider contracts.
- Frontend controls are UX only; Fastify re-checks capabilities and transition validity.
