# Implementation Specification V1

Status: Approved baseline
Date: 2026-09-08

## 1. Goal

`cpxlabs-admin` is an enterprise React starter for CRM, ERP, backoffice, dashboards and administrative SaaS applications. It must provide conventions and reusable platform primitives without forcing every domain into CRUD.

## 2. Runtime and core stack

- React + Vite
- TypeScript in strict mode
- TanStack Router for type-safe routing and URL state
- TanStack Query for remote/server state
- TanStack Table for data-grid primitives
- React Hook Form + Zod for forms and runtime validation
- Tailwind CSS + shadcn/ui + Base UI for the design-system foundation
- pnpm workspaces + Turborepo
- Vitest + Testing Library + Playwright
- Storybook for the UI catalog
- OpenTelemetry abstraction for observability
- OpenFeature abstraction for feature flags

## 3. Architectural style

The frontend is a modular monolith organized by feature. Shared platform capabilities live outside domain features. Infrastructure implementations are hidden behind contracts/adapters.

### Rules

1. Feature-first organization is the default.
2. Cross-feature imports are forbidden unless exposed by the target feature public API.
3. `shared` may not depend on `features`.
4. `platform` may not depend on application-specific feature internals.
5. Authentication and authorization are separate concerns.
6. Client-side permission checks improve UX only; the backend remains authoritative.
7. Remote state belongs to TanStack Query, not a generic global store.
8. URL-addressable state such as pagination, filters, sorting and tabs belongs in the URL.
9. Redux/Zustand are not baseline dependencies. Add them only when a concrete global client-state problem exists.
10. Backend technology is not part of the frontend contract.

## 4. Repository layout

```text
cpxlabs-admin/
├── apps/
│   ├── web/
│   └── api/                 # optional reference backend, added later
├── packages/
│   ├── ui/
│   ├── contracts/
│   ├── authorization/
│   ├── config/
│   ├── observability/
│   └── testing/
├── docs/
│   ├── architecture/
│   └── adr/
├── package.json
├── pnpm-workspace.yaml
└── turbo.json
```

## 5. Web application boundaries

```text
apps/web/src/
├── app/                     # bootstrap/composition root
├── routes/                  # TanStack Router route definitions
├── features/                # business verticals
├── platform/                # resource registry, auth integration, navigation, flags
└── shared/                  # app-local generic utilities
```

A feature should normally expose only its public surface through `index.ts`.

```text
features/customers/
├── api/
├── components/
├── model/
├── schemas/
├── views/
└── index.ts
```

## 6. Platform contracts

### ResourceDefinition

A resource describes discoverability and common administration metadata. It does not define the domain model.

```ts
export type ResourceDefinition = {
  name: string
  label: string
  routes: {
    list?: string
    create?: string
    show?: string
    edit?: string
  }
  capabilities?: {
    list?: Capability
    show?: Capability
    create?: Capability
    edit?: Capability
    delete?: Capability
  }
  navigation?: {
    group?: string
    order?: number
    hidden?: boolean
  }
}
```

The Resource Registry may feed navigation, breadcrumbs, command palette, route metadata and permission-aware discoverability.

### Capabilities

Capabilities are typed strings using the `<resource>.<action>` convention.

Examples:

```text
customers.read
customers.create
customers.update
customers.delete
users.read
users.manage
```

The UI consumes a stable API such as `can(capability)`. Backend enforcement remains mandatory.

### DataProvider

A generic DataProvider exists only for generic resource operations and administrative CRUD acceleration.

```ts
export interface DataProvider {
  getList<T>(resource: string, params: ListParams): Promise<ListResult<T>>
  getOne<T>(resource: string, id: string): Promise<T>
  create<T>(resource: string, input: unknown): Promise<T>
  update<T>(resource: string, id: string, input: unknown): Promise<T>
  delete(resource: string, id: string): Promise<void>
}
```

Domain workflows do not get disguised as CRUD. Operations such as `closeOpportunity`, `approveInvoice` or `transferOwnership` are explicit use cases/mutations.

## 7. Routing and URL state

TanStack Router is the routing foundation. Search params are validated and typed.

For list screens, the URL is the canonical representation for shareable navigation state:

```text
/customers?page=2&pageSize=50&status=active&sort=createdAt.desc
```

The table reads route search state; query keys derive from validated route state.

## 8. Data fetching

Preferred client flow:

```text
Route/Search State
      ↓
TanStack Query
      ↓
API Client
      ↓
HTTP API
```

Query keys must be deterministic and include every parameter that changes the server result, including tenant context where applicable.

Mutations invalidate the smallest affected query scope. Optimistic updates are used only when rollback semantics are clear.

## 9. Data grid baseline

The common DataGrid must support:

- server-side pagination
- server-side sorting
- server-side filtering
- column visibility
- row selection
- bulk actions
- row actions
- empty/loading/error states
- URL synchronization

Virtualization is an optional rendering optimization and never replaces server-side pagination for large datasets.

## 10. Forms baseline

Forms use React Hook Form with Zod schemas. Client validation exists for usability; the backend validates independently.

Common form primitives must standardize:

- labels and help text
- validation messages
- disabled/read-only state
- async submission state
- field arrays
- dirty-state protection
- API error mapping

## 11. Authentication and authorization

Frontend authentication is provider-based. No feature imports a vendor SDK directly.

Authorization uses typed capabilities. Route guards and component guards may hide or disable unavailable actions, but server/API enforcement is authoritative and deny-by-default.

## 12. Design system

The starter owns its component source and design tokens. Token layers:

```text
primitive tokens → semantic tokens → component usage
```

Baseline component groups:

- primitives
- forms
- feedback
- navigation
- overlays
- data display
- data grid
- app shell

Accessibility target: WCAG 2.2 AA.

## 13. Backend boundary

The web application is backend-agnostic. A future `apps/api` may provide a Fastify + PostgreSQL reference implementation, but that backend is not required by `apps/web`.

Supported integration models include REST/OpenAPI, GraphQL or dedicated adapters for existing .NET, Python, Java and Node backends.

## 14. Testing gates

Baseline gates:

- typecheck
- lint
- unit tests
- component tests for complex shared UI
- build
- Playwright smoke tests for critical journeys

Architecture tests should be introduced to prevent forbidden dependency directions as the repository grows.

## 15. Reference features required before V1 release

### Customer

Validates ordinary enterprise CRUD:

- list/filter/sort/paginate
- create
- view
- edit
- delete

### Opportunity

Validates non-CRUD workflow:

- create
- assign
- advance stage
- close won
- close lost

### Authorization scenario

At minimum:

- Admin
- Manager
- Viewer

Server mocks/reference API must demonstrate that hiding a button is not the authorization boundary.

## 16. Definition of Done for the starter V1

V1 is ready when:

1. a new resource can be registered without editing the app shell;
2. a list page can express filters/sorting/pagination through typed URL state;
3. a feature can use generic CRUD where appropriate and explicit domain mutations where not;
4. authorization is capability-based and backend-authoritative;
5. the app can switch API implementations without rewriting feature UI;
6. the shared DataGrid and form primitives cover the reference Customer feature;
7. the Opportunity feature proves the architecture is not CRUD-bound;
8. CI enforces typecheck, lint, tests and production build.
