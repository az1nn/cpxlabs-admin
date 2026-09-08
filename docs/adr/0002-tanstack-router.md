# ADR-002: TanStack Router as Routing Foundation

- Status: Accepted
- Date: 2026-09-08

## Context

Enterprise list screens depend heavily on typed path parameters, search parameters, loaders, navigation state and bookmarkable filters.

## Decision

Use TanStack Router as the routing foundation for `apps/web`.

Search params are treated as validated application state for navigation concerns such as pagination, sorting, filters, selected tabs and search.

## Consequences

- route/search state becomes type-safe;
- list URLs are shareable and reproducible;
- TanStack Query keys can derive directly from validated route state;
- routing is not implemented with ad-hoc `useState` strings;
- route files remain composition boundaries rather than locations for domain logic.
