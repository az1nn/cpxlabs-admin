# Feature Specification: Enterprise Starter Foundation

**Feature Branch**: historical retrofit

**Created**: 2026-09-08

**Status**: Implemented (Retrofitted)

**Retrofit Notice**: This specification documents behavior implemented before Spec Kit adoption. It was reconstructed from merged implementation, ADRs, tests, and review history.

## User Scenarios & Testing

### User Story 1 - Start an enterprise application from stable primitives (Priority: P1)

As an application team, I can start from a React enterprise foundation with routing, remote-data state, resource metadata, typed authorization capabilities, and a consistent application shell instead of assembling those concerns independently for each project.

**Independent Test**: Run the web application and verify resource-derived navigation and the Customers list operate through the registered provider without importing backend infrastructure.

**Acceptance Scenarios**:

1. **Given** a registered resource and sufficient capability, **When** the application renders, **Then** the resource appears in navigation and its route is reachable.
2. **Given** server/list state changes, **When** pagination/search/sort/filter state changes, **Then** navigable state is represented in the URL and remote data remains owned by TanStack Query.

### User Story 2 - Replace infrastructure behind contracts (Priority: P2)

As a product team, I can replace the source of CRUD data without rewriting resource screens because the frontend consumes a stable `DataProvider` boundary.

**Independent Test**: Supply a different provider implementation and verify the Customers resource continues to operate through the same UI/query layer.

### Edge Cases

- A resource without the required capability must not appear as an actionable navigation destination.
- Generic CRUD metadata must not be used to model domain-specific workflows.
- Router loaders must not introduce a second remote-data cache beside TanStack Query.

## Requirements

### Functional Requirements

- **FR-001**: The web application MUST use React, Vite, and strict TypeScript.
- **FR-002**: Routing and navigable URL/search state MUST be owned by TanStack Router.
- **FR-003**: Remote/server state MUST be owned by TanStack Query.
- **FR-004**: The platform MUST expose a `ResourceRegistry` for resource metadata and navigation derivation.
- **FR-005**: Generic CRUD access MUST be available through a backend-agnostic `DataProvider` contract.
- **FR-006**: Authorization MUST expose typed capabilities and keep frontend checks separate from authoritative server enforcement.
- **FR-007**: The application MUST provide an enterprise App Shell and a first reference `customers` resource.
- **FR-008**: TypeScript MUST retain `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`.

### Key Entities

- **ResourceDefinition**: Stable metadata describing a resource, routes, labels, and required capabilities.
- **Capability**: Typed permission identifier such as `customers.read`.
- **Principal**: Authenticated actor representation used by authorization boundaries.
- **DataProvider**: Generic CRUD adapter contract, intentionally not a domain workflow abstraction.

## Success Criteria

- **SC-001**: The starter builds under strict TypeScript without disabling strict compiler options.
- **SC-002**: A Customers list can be reached from registry-derived navigation and rendered through the provider boundary.
- **SC-003**: Changing URL list state does not require duplicating state into a separate global store.
- **SC-004**: No frontend source file needs ORM or Fastify implementation types.

## Assumptions

- SPA-first navigation is appropriate for the reference admin/backoffice use case.
- A reference backend may be added later without becoming mandatory to the frontend architecture.
