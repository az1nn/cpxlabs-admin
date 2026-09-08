import {
  Outlet,
  createRootRoute,
  createRoute,
  createRouter,
} from '@tanstack/react-router'

import { CustomerListPage } from './features/customers/customer-list-page'
import { customerListSearchSchema } from './features/customers/customer-list-search'
import type { CustomerListSearch } from './features/customers/customer-list-search'
import { AppShell } from './platform/shell/app-shell'

const rootRoute = createRootRoute({
  component: () => (
    <AppShell>
      <Outlet />
    </AppShell>
  ),
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: OverviewPage,
})

const customersRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/customers',
  validateSearch: customerListSearchSchema,
  component: CustomersRoute,
})

function OverviewPage() {
  return (
    <section className="page-stack">
      <div>
        <p className="eyebrow">Platform baseline</p>
        <h1>Enterprise administration starter</h1>
        <p className="page-description">
          Resource-driven navigation, capability-aware UI and server-oriented data
          contracts are active.
        </p>
      </div>

      <div className="overview-grid">
        <article className="surface-card">
          <span className="metric-label">Runtime</span>
          <strong>React + Vite</strong>
          <p>SPA-first and backend-agnostic.</p>
        </article>
        <article className="surface-card">
          <span className="metric-label">Navigation</span>
          <strong>Resource Registry</strong>
          <p>Generated from metadata and capabilities.</p>
        </article>
        <article className="surface-card">
          <span className="metric-label">List state</span>
          <strong>URL controlled</strong>
          <p>Pagination, filtering and sorting remain shareable.</p>
        </article>
      </div>
    </section>
  )
}

function CustomersRoute() {
  const search = customersRoute.useSearch()
  const navigate = customersRoute.useNavigate()

  const updateSearch = (patch: Partial<CustomerListSearch>) => {
    void navigate({
      search: (previous) => ({ ...previous, ...patch }),
      replace: true,
    })
  }

  return <CustomerListPage search={search} onSearchChange={updateSearch} />
}

const routeTree = rootRoute.addChildren([indexRoute, customersRoute])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
