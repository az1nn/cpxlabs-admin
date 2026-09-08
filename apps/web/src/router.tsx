import {
  Outlet,
  createRootRoute,
  createRoute,
  createRouter,
  useRouter,
} from '@tanstack/react-router'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, PageHeader } from '@cpxlabs-admin/ui'

import { CustomerCreatePage } from './features/customers/customer-create-page'
import { CustomerDetailPage } from './features/customers/customer-detail-page'
import { CustomerEditPage } from './features/customers/customer-edit-page'
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

const customerCreateRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/customers/new',
  component: CustomerCreateRoute,
})

const customerDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/customers/$customerId',
  component: CustomerDetailRoute,
})

const customerEditRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/customers/$customerId/edit',
  component: CustomerEditRoute,
})

function OverviewPage() {
  return (
    <section className="grid gap-6">
      <PageHeader
        eyebrow="Platform baseline"
        title="Enterprise administration starter"
        description="Resource-driven navigation, capability-aware UI, an owned design system and server-oriented data contracts are active."
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>React + Vite</CardTitle>
            <CardDescription>SPA-first and backend-agnostic runtime.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">No framework-specific backend assumptions.</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Resource Registry</CardTitle>
            <CardDescription>Navigation and capabilities from metadata.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">CRUD metadata without domain workflow lock-in.</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Owned UI</CardTitle>
            <CardDescription>Base UI behavior + Tailwind semantic tokens.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">Application-owned components following shadcn conventions.</CardContent>
        </Card>
      </div>
    </section>
  )
}

function CustomersRoute() {
  const router = useRouter()
  const search = customersRoute.useSearch()
  const navigate = customersRoute.useNavigate()

  const updateSearch = (patch: Partial<CustomerListSearch>) => {
    void navigate({
      search: (previous) => ({ ...previous, ...patch }),
      replace: true,
    })
  }

  return (
    <CustomerListPage
      search={search}
      onSearchChange={updateSearch}
      onCreate={() => router.history.push('/customers/new')}
      onOpen={(id) => router.history.push(`/customers/${id}`)}
    />
  )
}

function CustomerCreateRoute() {
  const router = useRouter()
  return (
    <CustomerCreatePage
      onCreated={(id) => router.history.push(`/customers/${id}`)}
      onCancel={() => router.history.push('/customers')}
    />
  )
}

function CustomerDetailRoute() {
  const router = useRouter()
  const { customerId } = customerDetailRoute.useParams()
  return (
    <CustomerDetailPage
      customerId={customerId}
      onBack={() => router.history.push('/customers')}
      onEdit={() => router.history.push(`/customers/${customerId}/edit`)}
      onDeleted={() => router.history.push('/customers')}
    />
  )
}

function CustomerEditRoute() {
  const router = useRouter()
  const { customerId } = customerEditRoute.useParams()
  return (
    <CustomerEditPage
      customerId={customerId}
      onSaved={() => router.history.push(`/customers/${customerId}`)}
      onCancel={() => router.history.push(`/customers/${customerId}`)}
    />
  )
}

const routeTree = rootRoute.addChildren([
  indexRoute,
  customersRoute,
  customerCreateRoute,
  customerDetailRoute,
  customerEditRoute,
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
