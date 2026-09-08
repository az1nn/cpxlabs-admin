# Implementation Plan: Design System and Customer CRUD

**Branch**: historical retrofit | **Date**: 2026-09-08 | **Spec**: `specs/002-design-system-crud/spec.md`

**Status**: Implemented (Retrofitted)

## Summary

Introduce a small project-owned UI package using Tailwind CSS v4 and Base UI behavior, then exercise the platform architecture with a complete Customers CRUD flow using React Hook Form, Zod, TanStack Query mutations, and typed capability-aware actions.

## Technical Context

**Language/Version**: TypeScript strict; React 19

**Primary Dependencies**: Tailwind CSS v4, Base UI, React Hook Form, Zod, TanStack Query

**Storage**: Provider-defined; no backend dependency required by the feature

**Testing**: Vitest + Testing Library

**Target Platform**: Modern browsers

**Project Type**: Enterprise web application / reusable UI package

**Performance Goals**: Lightweight shared primitives; server-oriented list behavior preserved

**Constraints**: Open-code component ownership; no feature-specific behavior in `packages/ui`; capability checks remain UX-only

**Scale/Scope**: Reference CRUD plus the minimum reusable design-system primitives needed to support it

## Constitution Check

- Spec-before-implementation: **Historical exception**; retrofit only.
- Backend-agnostic frontend: Pass.
- Server-authoritative authorization: UI uses capabilities only for adaptation; Pass.
- Strict TypeScript/tests: Pass.
- Simplicity: Pass; primitives extracted only with concrete Customers/App Shell consumers.

## Project Structure

```text
packages/ui/
├── styles.css
└── src/
    ├── button.tsx
    ├── dialog.tsx
    ├── form-field.tsx
    ├── page-header.tsx
    └── index.ts

apps/web/src/features/customers/
├── api/
├── components/
├── schemas/
└── views/
```

**Structure Decision**: Keep generic visual/behavioral primitives in `packages/ui`; keep customer schemas/forms/views inside the Customers feature.

## Architecture Decisions

- Tailwind v4 supplies styling infrastructure and semantic tokens.
- Base UI supplies headless behavior where useful, but application code consumes owned components.
- React Hook Form owns form interaction state; Zod owns form validation contracts.
- TanStack Query remains mutation/cache owner.
- Delete confirmation is a reusable Dialog concern, while delete semantics stay in the feature.

## Complexity Tracking

No unresolved constitution violations beyond the documented historical retrofit.
