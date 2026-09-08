import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from '@tanstack/react-router'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { AuthorizationProvider } from './platform/authorization/authorization-provider'
import { demoPrincipal } from './platform/authorization/demo-principal'
import { DataProviderProvider } from './platform/data/data-provider-context'
import { demoDataProvider } from './platform/data/demo-data-provider'
import { router } from './router'
import './styles.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
})

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Root element not found')
}

createRoot(rootElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <DataProviderProvider provider={demoDataProvider}>
        <AuthorizationProvider principal={demoPrincipal}>
          <RouterProvider router={router} />
        </AuthorizationProvider>
      </DataProviderProvider>
    </QueryClientProvider>
  </StrictMode>,
)
