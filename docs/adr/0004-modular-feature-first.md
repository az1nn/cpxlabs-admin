# ADR-004: Modular Monolith with Feature-First Boundaries

- Status: Accepted
- Date: 2026-09-08

## Context

Enterprise frontends often degrade into global `components`, `hooks`, `services` and `utils` directories where domain boundaries disappear. The starter must scale across many features and multiple contributors without prematurely creating separately versioned packages for every domain.

## Decision

Use a modular monolith organized vertically by feature inside `apps/web`.

Shared packages are reserved for genuinely reusable platform concerns. Feature internals are private by default and cross-feature access occurs through explicit public exports.

## Dependency rules

```text
app/routes → features → platform/shared packages
                   ↘ contracts

shared/platform ✕ feature internals
feature A      ✕ feature B internals
```

A feature may depend on another feature only through an intentional public contract when the relationship is unavoidable.

## Consequences

- domain ownership remains visible in the file system;
- features can evolve independently inside one deployable application;
- fewer premature packages and versioning problems;
- architecture linting can later enforce dependency directions;
- extraction to packages/services remains possible when justified by real boundaries.
