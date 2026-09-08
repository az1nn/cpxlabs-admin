# Feature Specification: Design System and Customer CRUD

**Feature Branch**: historical retrofit

**Created**: 2026-09-08

**Status**: Implemented (Retrofitted)

**Retrofit Notice**: This specification documents behavior implemented before Spec Kit adoption.

## User Scenarios & Testing

### User Story 1 - Build enterprise screens from owned UI primitives (Priority: P1)

As a product team, I can build consistent enterprise screens from project-owned components and semantic tokens while relying on accessible headless behavior underneath.

**Independent Test**: Render the customer pages and shared primitives and verify consistent styling, focus behavior, validation states, and responsive layout.

### User Story 2 - Complete customer CRUD without leaking infrastructure (Priority: P1)

As an authorized user, I can list, create, inspect, edit, and delete customers through the same resource/provider boundaries established by the foundation.

**Independent Test**: Complete the CRUD journey while changing provider implementation without rewriting the feature views.

### User Story 3 - Adapt actions to capabilities (Priority: P2)

As a user, I see only create/edit/delete actions allowed by my capabilities while server authority remains outside the UI abstraction.

### Edge Cases

- Validation errors must be shown next to the relevant field.
- Delete requires explicit confirmation.
- Empty/loading/error/not-found states must be represented deliberately.
- UI capability checks must not be treated as security enforcement.

## Requirements

### Functional Requirements

- **FR-001**: The workspace MUST expose project-owned UI primitives from `packages/ui`.
- **FR-002**: The design system MUST use semantic tokens and support enterprise density without coupling features to raw primitive behavior.
- **FR-003**: Base UI/headless behavior MAY be used behind owned components.
- **FR-004**: Customers MUST support list/create/show/edit/delete flows.
- **FR-005**: Forms MUST use React Hook Form and Zod validation.
- **FR-006**: Mutations MUST update/invalidate TanStack Query state correctly.
- **FR-007**: Destructive deletion MUST require a confirmation dialog.
- **FR-008**: Resource actions MUST adapt to typed capabilities.
- **FR-009**: Generic CRUD behavior MUST remain behind `DataProvider` rather than becoming coupled to a specific backend.

### Key Entities

- **Customer**: Reference enterprise resource with name, email, company, status, and update metadata.
- **UI Primitive**: Project-owned component exposing stable styling/accessibility semantics.
- **Customer Form Schema**: Validation contract for create/edit user input.

## Success Criteria

- **SC-001**: A user can complete customer create/show/edit/delete from the browser UI.
- **SC-002**: The CRUD implementation passes strict TypeScript and unit/build gates.
- **SC-003**: Shared primitives are reusable outside the Customers feature without feature-specific dependencies.
- **SC-004**: No customer view imports backend persistence types.

## Assumptions

- The first design-system scope is intentionally small and expands only with concrete consumers.
- CRUD is a reference productivity path, not a universal business-domain abstraction.
