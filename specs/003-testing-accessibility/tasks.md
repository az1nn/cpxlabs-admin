# Tasks: Testing and Accessibility Platform

**Status**: Implemented (Retrofitted)

## Storybook and Accessibility

- [x] T001 Add `apps/storybook` workspace
- [x] T002 Configure Storybook with React/Vite
- [x] T003 Add browser-based story testing
- [x] T004 Add axe accessibility addon and fail on violations
- [x] T005 Add stories for Button, FormField, Dialog, and PageHeader

## End-to-End Testing

- [x] T006 Add Playwright to `apps/web`
- [x] T007 Configure Chromium-only initial browser target
- [x] T008 Run E2E against Vite production preview
- [x] T009 Implement customer list/search/create/show/edit/delete journey
- [x] T010 Use semantic/user-visible locators and assertions
- [x] T011 Configure retries/traces/report output for diagnostics

## Test Boundaries and CI

- [x] T012 Exclude `e2e/**` from unit Vitest discovery
- [x] T013 Add separate `browser-tests` CI job
- [x] T014 Preserve fast frozen-install/typecheck/unit/build quality job
- [x] T015 Validate Storybook/a11y and Playwright gates in CI
- [x] T016 Mark feature as historical retrofit
