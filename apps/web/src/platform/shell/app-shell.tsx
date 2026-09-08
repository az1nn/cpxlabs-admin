import { useLocation, useRouter } from '@tanstack/react-router'
import type { MouseEvent, PropsWithChildren } from 'react'

import { useAuthorization } from '../authorization/authorization-provider'
import { resourceRegistry } from '../resources/resources'
import { getNavigationItems } from './navigation'

export function AppShell({ children }: PropsWithChildren) {
  const router = useRouter()
  const location = useLocation()
  const authorization = useAuthorization()
  const navigation = getNavigationItems(resourceRegistry, authorization.can)

  const navigate = (event: MouseEvent<HTMLAnchorElement>, href: string) => {
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return
    }

    event.preventDefault()
    router.history.push(href)
  }

  return (
    <div className="min-h-screen bg-background text-foreground lg:grid lg:grid-cols-[248px_minmax(0,1fr)]">
      <aside className="border-b bg-primary text-primary-foreground lg:min-h-screen lg:border-b-0 lg:border-r lg:border-white/10">
        <div className="px-4 py-5">
          <a
            className="block rounded-md px-3 py-2 text-sm font-semibold tracking-tight outline-none focus-visible:ring-2 focus-visible:ring-white/60"
            href="/"
            onClick={(event) => navigate(event, '/')}
          >
            CPXLabs Admin
          </a>
        </div>

        <nav className="px-3 pb-5" aria-label="Primary navigation">
          <p className="mb-2 px-3 text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-primary-foreground/55">
            Workspace
          </p>
          <a
            className={`mb-5 block rounded-md px-3 py-2 text-sm transition-colors ${
              location.pathname === '/'
                ? 'bg-white/12 text-white'
                : 'text-primary-foreground/75 hover:bg-white/8 hover:text-white'
            }`}
            href="/"
            aria-current={location.pathname === '/' ? 'page' : undefined}
            onClick={(event) => navigate(event, '/')}
          >
            Overview
          </a>

          {navigation.map((item) => (
            <div key={item.resource} className="mb-5">
              <p className="mb-2 px-3 text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-primary-foreground/55">
                {item.group}
              </p>
              <a
                className={`block rounded-md px-3 py-2 text-sm transition-colors ${
                  location.pathname.startsWith(item.href)
                    ? 'bg-white/12 text-white'
                    : 'text-primary-foreground/75 hover:bg-white/8 hover:text-white'
                }`}
                href={item.href}
                aria-current={location.pathname.startsWith(item.href) ? 'page' : undefined}
                onClick={(event) => navigate(event, item.href)}
              >
                {item.label}
              </a>
            </div>
          ))}
        </nav>
      </aside>

      <div className="min-w-0">
        <header className="flex h-16 items-center justify-between border-b bg-card px-5 sm:px-7">
          <div>
            <p className="m-0 text-sm font-semibold">Enterprise workspace</p>
            <p className="m-0 mt-0.5 text-xs text-muted-foreground">Reusable admin platform</p>
          </div>
          <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
            {authorization.principal?.id ?? 'Anonymous'}
          </span>
        </header>
        <main className="mx-auto w-full max-w-[1600px] p-5 sm:p-7">{children}</main>
      </div>
    </div>
  )
}
