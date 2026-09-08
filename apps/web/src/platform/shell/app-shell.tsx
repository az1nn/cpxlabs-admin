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
    <div className="app-shell">
      <aside className="app-sidebar">
        <a className="brand" href="/" onClick={(event) => navigate(event, '/')}>
          CPXLabs Admin
        </a>

        <nav aria-label="Primary navigation">
          <span className="nav-section-label">Workspace</span>
          <div className="nav-list">
            <a
              className="nav-link"
              href="/"
              aria-current={location.pathname === '/' ? 'page' : undefined}
              onClick={(event) => navigate(event, '/')}
            >
              Overview
            </a>
          </div>

          {navigation.map((item) => (
            <div key={item.resource}>
              <span className="nav-section-label">{item.group}</span>
              <div className="nav-list">
                <a
                  className="nav-link"
                  href={item.href}
                  aria-current={
                    location.pathname.startsWith(item.href) ? 'page' : undefined
                  }
                  onClick={(event) => navigate(event, item.href)}
                >
                  {item.label}
                </a>
              </div>
            </div>
          ))}
        </nav>
      </aside>

      <div className="app-main">
        <header className="app-topbar">
          <strong>Enterprise workspace</strong>
          <span>{authorization.principal?.id ?? 'Anonymous'}</span>
        </header>
        <main className="app-content">{children}</main>
      </div>
    </div>
  )
}
