import { Card, CardContent, CardDescription, CardHeader, CardTitle, PageHeader } from '@cpxlabs-admin/ui'
import {
  Outlet,
  createRootRoute,
  createRoute,
  createRouter,
  useRouter,
} from '@tanstack/react-router'
import { useEffect } from 'react'
import { z } from 'zod'

import { SignInPage } from './features/auth/sign-in-page'
import { CustomerCreatePage } from './features/customers/customer-create-page'
import { CustomerDetailPage } from './features/customers/customer-detail-page'
import { CustomerEditPage } from './features/customers/customer-edit-page'
import { CustomerListPage } from './features/customers/customer-list-page'
import { customerListSearchSchema } from './features/customers/customer-list-search'
import type { CustomerListSearch } from './features/customers/customer-list-search'
import { OpportunityCreatePage } from './features/opportunities/opportunity-create-page'
import { OpportunityDetailPage } from './features/opportunities/opportunity-detail-page'
import { OpportunityListPage } from './features/opportunities/opportunity-list-page'
import { opportunityListSearchSchema } from './features/opportunities/opportunity-list-search'
import type { OpportunityListSearch } from './features/opportunities/opportunity-list-search'
import { useAppSession } from './platform/authentication/session-provider'
import { AppShell } from './platform/shell/app-shell'

const rootRoute = createRootRoute({ component: Outlet })

const signInSearchSchema = z.object({ redirect: z.string().optional() })

const signInRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/sign-in',
  validateSearch: signInSearchSchema,
  component: SignInRoute,
})

const authenticatedRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: '_authenticated',
  component: AuthenticatedLayout,
})

const indexRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/',
  component: OverviewPage,
})

const customersRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/customers',
  validateSearch: customerListSearchSchema,
  component: CustomersRoute,
})

const customerCreateRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/customers/new',
  component: CustomerCreateRoute,
})

const customerDetailRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/customers/$customerId',
  component: CustomerDetailRoute,
})

const customerEditRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/customers/$customerId/edit',
  component: CustomerEditRoute,
})

const opportunitiesRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/opportunities',
  validateSearch: opportunityListSearchSchema,
  component: OpportunitiesRoute,
})

const opportunityCreateRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/opportunities/new',
  component: OpportunityCreateRoute,
})

const opportunityDetailRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/opportunities/$opportunityId',
  component: OpportunityDetailRoute,
})

function safeRedirect(redirect: string | undefined) {
  return redirect && redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '/'
}

function SessionLoading() {
  return (
    <main className="grid min-h-screen place-items-center bg-background p-5 text-sm text-muted-foreground">
      Checking session…
    </main>
  )
}

function AuthenticatedLayout() {
  const session = useAppSession()
  const router = useRouter()

  useEffect(() => {
    if (session.status !== 'unauthenticated') return
    const destination = `${window.location.pathname}${window.location.search}${window.location.hash}`
    router.history.replace(`/sign-in?redirect=${encodeURIComponent(destination)}`)
  }, [router, session.status])

  if (session.status === 'loading') return <SessionLoading />
  if (session.status !== 'authenticated') return null

  return <AppShell><Outlet /></AppShell>
}

function SignInRoute() {
  const session = useAppSession()
  const router = useRouter()
  const search = signInRoute.useSearch()
  const destination = safeRedirect(search.redirect)

  useEffect(() => {
    if (session.status === 'authenticated') router.history.replace(destination)
  }, [destination, router, session.status])

  if (session.status === 'loading') return <SessionLoading />
  if (session.status === 'authenticated') return null
  return <SignInPage onAuthenticated={() => router.history.replace(destination)} />
}

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
          <CardHeader><CardTitle>React + Vite</CardTitle><CardDescription>SPA-first and backend-agnostic runtime.</CardDescription></CardHeader>
          <CardContent className="text-sm text-muted-foreground">No framework-specific backend assumptions.</CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Resource Registry</CardTitle><CardDescription>Navigation and capabilities from metadata.</CardDescription></CardHeader>
          <CardContent className="text-sm text-muted-foreground">CRUD metadata without domain workflow lock-in.</CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Owned UI</CardTitle><CardDescription>Base UI behavior + Tailwind semantic tokens.</CardDescription></CardHeader>
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
    void navigate({ search: (previous) => ({ ...previous, ...patch }), replace: true })
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
  return <CustomerCreatePage onCreated={(id) => router.history.push(`/customers/${id}`)} onCancel={() => router.history.push('/customers')} />
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

function OpportunitiesRoute() {
  const router = useRouter()
  const search = opportunitiesRoute.useSearch()
  const navigate = opportunitiesRoute.useNavigate()
  const updateSearch = (patch: Partial<OpportunityListSearch>) => {
    void navigate({ search: (previous) => ({ ...previous, ...patch }), replace: true })
  }

  return (
    <OpportunityListPage
      search={search}
      onSearchChange={updateSearch}
      onCreate={() => router.history.push('/opportunities/new')}
      onOpen={(id) => router.history.push(`/opportunities/${id}`)}
    />
  )
}

function OpportunityCreateRoute() {
  const router = useRouter()
  return (
    <OpportunityCreatePage
      onCreated={(id) => router.history.push(`/opportunities/${id}`)}
      onCancel={() => router.history.push('/opportunities')}
    />
  )
}

function OpportunityDetailRoute() {
  const router = useRouter()
  const { opportunityId } = opportunityDetailRoute.useParams()
  return <OpportunityDetailPage opportunityId={opportunityId} onBack={() => router.history.push('/opportunities')} />
}

const routeTree = rootRoute.addChildren([
  signInRoute,
  authenticatedRoute.addChildren([
    indexRoute,
    customersRoute,
    customerCreateRoute,
    customerDetailRoute,
    customerEditRoute,
    opportunitiesRoute,
    opportunityCreateRoute,
    opportunityDetailRoute,
  ]),
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register { router: typeof router }
}
