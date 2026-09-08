import { can as canPrincipal, type Principal } from '@cpxlabs-admin/authorization'
import type { Capability } from '@cpxlabs-admin/contracts'
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type PropsWithChildren,
  type ReactNode,
} from 'react'

type AuthorizationContextValue = {
  principal: Principal | null
  can: (capability: Capability) => boolean
}

const AuthorizationContext = createContext<AuthorizationContextValue | null>(null)

type AuthorizationProviderProps = PropsWithChildren<{
  principal: Principal | null
}>

export function AuthorizationProvider({
  principal,
  children,
}: AuthorizationProviderProps) {
  const can = useCallback(
    (capability: Capability) => canPrincipal(principal, capability),
    [principal],
  )

  const value = useMemo(() => ({ principal, can }), [principal, can])

  return (
    <AuthorizationContext.Provider value={value}>
      {children}
    </AuthorizationContext.Provider>
  )
}

export function useAuthorization(): AuthorizationContextValue {
  const value = useContext(AuthorizationContext)

  if (!value) {
    throw new Error('useAuthorization must be used inside AuthorizationProvider')
  }

  return value
}

type CanProps = PropsWithChildren<{
  capability: Capability
  fallback?: ReactNode
}>

export function Can({ capability, children, fallback = null }: CanProps) {
  const authorization = useAuthorization()

  return authorization.can(capability) ? children : fallback
}
