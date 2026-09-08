# ADR-008 — Testing pyramid and browser quality gates

- Status: Accepted
- Date: 2026-09-08

## Context

The starter must support enterprise teams without turning every change into an expensive end-to-end suite. Unit tests alone are insufficient for accessibility, focus behavior, browser APIs and complete user journeys.

## Decision

Use three complementary layers:

1. **Vitest unit/integration tests** for pure logic, registries, providers and feature behavior that does not require a real browser.
2. **Storybook + Vitest Browser Mode + axe** for owned UI components. Stories are executable component specifications and accessibility violations fail CI by default.
3. **Playwright E2E** only for critical user journeys that cross routing, forms, queries, mutations and dialogs.

Chromium is the initial CI browser. Additional engines are introduced only when product requirements justify the runtime cost.

## Rules

- Tests assert user-visible behavior, not implementation details.
- Accessibility failures are errors, not warnings, for production components.
- E2E workers are limited to one in CI for deterministic execution.
- Playwright traces are retained on retry/failure.
- Storybook and E2E browser suites run separately from the fast unit-test gate.
- No snapshot-heavy testing strategy.

## Reference journey

The customer resource must prove list/search URL state plus create, show, edit and delete in one browser journey.

## Consequences

### Positive

- Fast feedback for most code changes.
- Real-browser coverage for component behavior and accessibility.
- A small number of high-value E2E tests protect platform integration seams.

### Negative

- CI needs a Chromium installation.
- Storybook becomes a maintained application in the workspace.
- Browser tests are slower than unit tests and should remain intentionally scoped.
