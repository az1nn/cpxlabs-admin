# cpxlabs-admin Constitution

## Core Principles

### I. Spec Before Implementation (NON-NEGOTIABLE)

Every material feature or cross-cutting change MUST begin with a Spec Kit feature specification before implementation starts. The default lifecycle is `specify -> clarify (when needed) -> plan -> tasks -> analyze (when useful) -> implement -> converge`. Material unresolved `NEEDS CLARIFICATION` items MUST be resolved before implementation. Small, isolated maintenance fixes may use a reduced workflow only when the PR clearly documents scope, diagnosis, and validation.

Historical specifications `001` through `004` are explicitly retrofitted records of work completed before Spec Kit adoption; they MUST NOT be represented as originally Spec Kit-driven.

### II. Backend-Agnostic Frontend and Explicit Boundaries

The web application MUST depend on stable contracts, providers, and explicit use cases rather than backend implementation details. `DataProvider` is limited to generic CRUD concerns; domain workflows MUST use named operations/use cases rather than hiding business behavior inside generic updates. TanStack Router owns navigation and URL state; TanStack Query owns remote/server-state caching. Duplicate client-side sources of truth are prohibited without an explicit ADR.

`apps/web` MUST NOT import Prisma, database code, or Fastify internals. Shared contracts MUST NOT expose ORM-generated or transport-internal types.

### III. Server Authority and Typed Authorization

Authorization capabilities MUST be typed and stable at application boundaries. Frontend permission checks exist for UX only; the API remains authoritative and MUST deny by default. `Principal` and `RequestContext` are the canonical request identity/context abstractions. Tenant or ownership isolation, when enabled, MUST be enforced server-side and repository-side rather than through UI filtering.

### IV. Strict Types, Tests, and CI Are Gates (NON-NEGOTIABLE)

TypeScript strictness MUST remain enabled, including `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`. A failing compiler, test, accessibility gate, or build MUST be fixed at the cause; reducing strictness or bypassing a gate to make CI green is prohibited.

Material changes MUST preserve the appropriate validation layers: unit/integration tests, production build, Storybook browser/accessibility coverage for shared UI, and Playwright coverage for critical journeys. Database-backed behavior MUST be validated against a real PostgreSQL service in CI when the persistence contract is involved.

### V. Simplicity, Ownership, and Evolvability

The starter MUST avoid becoming a bespoke framework. Prefer mature ecosystem libraries behind project-owned boundaries. New packages, services, caches, queues, state managers, or abstractions require a concrete need and a clear consumer. Cross-cutting structural decisions MUST be recorded as ADRs. Implementation details such as ORM, auth vendor, feature-flag vendor, or telemetry exporter MUST remain replaceable behind stable application contracts where practical.

## Enterprise Engineering Constraints

- The reference web runtime is React + Vite, SPA-first.
- Navigable list state such as pagination, sorting, filtering, search, tabs, and saved-view identifiers belongs in the URL when it affects shareable page state.
- Large or potentially large datasets use server-side pagination/filtering/sorting; virtualization is only a rendering optimization.
- Shared UI MUST target WCAG 2.2 AA behavior and preserve keyboard/focus semantics.
- Security decisions follow deny-by-default authorization, server-side validation, secure session handling, and current OWASP guidance.
- Logs, telemetry, and functional audit trails are distinct concerns and MUST remain separable when introduced.
- PostgreSQL is the reference relational store. Prisma is an infrastructure adapter and MUST remain behind repository boundaries; exact version pinning is preferred for the reference persistence layer.
- The reference browser/API topology SHOULD be same-origin to simplify secure cookie sessions, CSRF policy, and deployment behavior.
- `pnpm-lock.yaml` is versioned and CI installs with `--frozen-lockfile`.

## Spec and Architecture Workflow

The artifact hierarchy is:

`Constitution -> Feature Spec -> Technical Plan/Research/Contracts -> Tasks -> Implementation/Tests -> Convergence`

ADRs explain durable, cross-cutting architectural decisions and SHOULD be referenced from the relevant feature plan. Documentation under `docs/` supplements but does not replace a feature spec. Every material PR MUST identify its spec path, state the validation performed, and report unresolved convergence items if any.

For new features, the feature directory under `specs/###-slug/` is the source of truth for scope and acceptance criteria. Completed tasks MUST be checked off rather than silently deleted. When implementation diverges from a plan, update the artifacts or record the architectural change before merge.

## Governance

This constitution supersedes informal project habits where they conflict. Amendments require a PR that explains the rationale, affected workflows, and any migration required for existing specs or code. Constitution versions use semantic versioning: MAJOR for incompatible governance changes, MINOR for new principles or materially expanded rules, PATCH for clarifications that do not alter obligations.

All implementation and review work MUST verify constitution compliance. Complexity that violates a principle requires explicit justification in the feature plan's Complexity Tracking section.

**Version**: 1.0.0 | **Ratified**: 2026-09-08 | **Last Amended**: 2026-09-08
