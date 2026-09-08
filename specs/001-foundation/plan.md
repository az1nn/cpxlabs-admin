# Implementation Plan: Enterprise Starter Foundation

**Branch**: historical retrofit | **Date**: 2026-09-08 | **Spec**: `specs/001-foundation/spec.md`

**Status**: Implemented (Retrofitted)

## Summary

Establish a light pnpm/Turborepo workspace with a Vite React web application and stable platform contracts for resources, data access, and authorization. Keep infrastructure replaceable and avoid creating an internal framework.

## Technical Context

**Language/Version**: TypeScript strict; React 19

**Primary Dependencies**: Vite, TanStack Router, TanStack Query, TanStack Table

**Storage**: None required for the foundation; provider is abstracted

**Testing**: Vitest + Testing Library

**Target Platform**: Modern evergreen browsers

**Project Type**: Monorepo web application / reusable enterprise starter

**Performance Goals**: Route-level scalability, server-oriented list patterns, no duplicate remote cache

**Constraints**: SPA-first; backend-agnostic; strict TypeScript; generic CRUD must not swallow domain workflows

**Scale/Scope**: Foundation intended to remain structurally viable across many enterprise features/resources

## Constitution Check

Retrospective check against constitution v1.0.0:

- Spec-before-implementation: **Historical exception**; this artifact is explicitly retrofitted.
- Backend-agnostic frontend: Pass.
- Typed authorization boundary: Pass.
- Strict TypeScript/CI: Pass.
- Simplicity/evolvability: Pass; no mandatory backend, global state manager, Redis, or microservices introduced.

## Project Structure

```text
apps/
└── web/
    └── src/
        ├── app/
        ├── features/
        ├── platform/
        └── shared/

packages/
├── contracts/
├── authorization/
├── config/
└── testing/

docs/
├── architecture/
└── adr/
```

**Structure Decision**: Use feature-first organization in `apps/web` and extract only contracts/capabilities/config/testing concerns with immediate reuse value.

## Architecture Decisions

- Vite is the web runtime.
- TanStack Router owns routes and URL state.
- TanStack Query owns remote cache.
- `ResourceRegistry` powers metadata/navigation discovery.
- `DataProvider` is deliberately constrained to generic CRUD.
- Typed capabilities are the stable authorization API; backend remains authoritative when present.

## Complexity Tracking

No unresolved constitution violations beyond the explicitly documented historical retrofit.
