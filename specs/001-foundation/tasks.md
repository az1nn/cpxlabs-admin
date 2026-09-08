# Tasks: Enterprise Starter Foundation

**Status**: Implemented (Retrofitted)

These tasks summarize completed implementation work and were reconstructed during Spec Kit adoption.

## Workspace Foundation

- [x] T001 Initialize pnpm workspace and Turborepo
- [x] T002 Create `apps/web` with React, Vite, and strict TypeScript
- [x] T003 Preserve `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`
- [x] T004 Add deterministic CI install/typecheck/test/build gates

## Platform Contracts

- [x] T005 Create `packages/contracts`
- [x] T006 Define `ResourceDefinition`
- [x] T007 Define backend-agnostic `DataProvider`
- [x] T008 Create typed `Capability` and `Principal` authorization primitives
- [x] T009 Implement `ResourceRegistry` and resource-derived navigation

## Web Platform

- [x] T010 Install/configure TanStack Router
- [x] T011 Install/configure TanStack Query as the remote cache owner
- [x] T012 Implement enterprise App Shell
- [x] T013 Implement reference `customers` resource
- [x] T014 Keep list/search/sort/page state URL-driven
- [x] T015 Add tests for registry, navigation, authorization/provider boundaries

## Validation

- [x] T016 Pass TypeScript strict gate
- [x] T017 Pass unit tests
- [x] T018 Pass production build
- [x] T019 Record foundational architectural decisions as ADRs

## Retrofit Closure

- [x] T020 Mark this feature as historical retrofit rather than native Spec Kit history
