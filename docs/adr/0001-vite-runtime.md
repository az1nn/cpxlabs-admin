# ADR-001: Vite as Web Application Runtime

- Status: Accepted
- Date: 2026-09-08

## Context

The project is intended to be a reusable enterprise starter for CRM, ERP, dashboards and backoffice applications. The majority of these applications are authenticated, highly interactive and API-driven, with no structural requirement for SSR.

## Decision

Use Vite as the default web runtime/build foundation for `apps/web`.

The starter will not depend on Next.js-specific primitives such as Server Components, Server Actions or App Router.

## Consequences

### Positive

- framework-neutral React architecture;
- simpler SPA mental model;
- easier integration with existing backends;
- no coupling between frontend architecture and backend deployment model;
- direct control over routing, caching and API integration.

### Negative

- SSR/SSG is not a baseline capability;
- backend/BFF concerns require a separate service when needed;
- some capabilities provided by fullstack meta-frameworks must be composed explicitly.

## Guardrail

If a future product requires SSR as a core business requirement, it should evaluate a dedicated runtime rather than introducing hidden SSR assumptions into this starter.
