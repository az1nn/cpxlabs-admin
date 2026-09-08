# Implementation Plan: Testing and Accessibility Platform

**Branch**: historical retrofit | **Date**: 2026-09-08 | **Spec**: `specs/003-testing-accessibility/spec.md`

**Status**: Implemented (Retrofitted)

## Summary

Add browser-level component, accessibility, and end-to-end gates without duplicating unit-test responsibility. Storybook validates reusable UI in Chromium with axe; Playwright protects critical user journeys against a production Vite preview.

## Technical Context

**Language/Version**: TypeScript strict

**Primary Dependencies**: Storybook, Vitest Browser Mode, Playwright, axe accessibility addon

**Storage**: N/A for initial browser-test layer

**Testing**: Vitest unit/component, Storybook browser/a11y, Playwright E2E

**Target Platform**: Chromium on CI, modern browser runtime

**Project Type**: Testing/quality infrastructure for monorepo web application

**Performance Goals**: Keep fast unit gates separate from higher-cost browser gates

**Constraints**: E2E tests must exercise user-visible behavior and semantic locators; browser testing must not replace unit/integration coverage

**Scale/Scope**: Shared primitives plus the critical Customers journey

## Constitution Check

- Spec-before-implementation: **Historical exception**; retrofit only.
- Strict tests/CI gates: Pass and strengthened.
- Accessibility requirement: Pass through Storybook + axe.
- Simplicity: Pass; one browser engine initially, no redundant browser matrix without need.

## Project Structure

```text
apps/storybook/
├── .storybook/
└── src/*.stories.tsx

apps/web/
├── e2e/
│   └── customer-crud.spec.ts
├── playwright.config.ts
└── vitest.config.ts

.github/workflows/ci.yml
```

**Structure Decision**: Storybook is a workspace application consuming shared UI; Playwright belongs to the web app and is explicitly excluded from its unit Vitest discovery.

## Architecture Decisions

- Unit/integration tests remain the fast feedback layer.
- Storybook validates reusable UI behavior and accessibility in a real browser.
- Playwright covers only high-value user journeys.
- Browser gates run separately in CI to isolate cost and diagnosis.

## Complexity Tracking

No unresolved constitution violations beyond the historical retrofit.
