import type { Principal } from '@cpxlabs-admin/authorization'
import type { SessionPrincipalDto } from '@cpxlabs-admin/contracts'
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react'

import {
  AccessUnavailableError,
  AuthenticationError,
  appAuthService,
  type AuthService,
  type SignInCredentials,
} from './auth-service'

export type SessionStatus = 'loading' | 'authenticated' | 'unauthenticated'

type SessionContextValue = {
  status: SessionStatus
  principal: Principal | null
  error: string | null
  refresh(): Promise<Principal | null>
  signIn(credentials: SignInCredentials): Promise<void>
  signOut(): Promise<void>
}

const SessionContext = createContext<SessionContextValue | null>(null)

function toPrincipal(dto: SessionPrincipalDto): Principal {
  return {
    id: dto.id,
    email: dto.email,
    name: dto.name,
    role: dto.role,
    capabilities: new Set(dto.capabilities),
  }
}

type SessionProviderProps = PropsWithChildren<{
  service?: AuthService
  onSessionCleared?: () => void
}>

export function SessionProvider({
  service = appAuthService,
  onSessionCleared,
  children,
}: SessionProviderProps) {
  const [status, setStatus] = useState<SessionStatus>('loading')
  const [principal, setPrincipal] = useState<Principal | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setError(null)

    try {
      const session = await service.getSession()
      if (!session) {
        setPrincipal(null)
        setStatus('unauthenticated')
        return null
      }

      const nextPrincipal = toPrincipal(session.principal)
      setPrincipal(nextPrincipal)
      setStatus('authenticated')
      return nextPrincipal
    } catch (caught) {
      setPrincipal(null)
      setStatus('unauthenticated')
      setError(
        caught instanceof AccessUnavailableError
          ? caught.message
          : 'Unable to restore the current session',
      )
      throw caught
    }
  }, [service])

  useEffect(() => {
    void refresh().catch(() => undefined)
  }, [refresh])

  const signIn = useCallback(
    async (credentials: SignInCredentials) => {
      setError(null)
      await service.signIn(credentials)
      const nextPrincipal = await refresh()
      if (!nextPrincipal) {
        throw new AuthenticationError('Unable to establish an application session')
      }
    },
    [refresh, service],
  )

  const signOut = useCallback(async () => {
    try {
      await service.signOut()
    } finally {
      setPrincipal(null)
      setStatus('unauthenticated')
      setError(null)
      onSessionCleared?.()
    }
  }, [onSessionCleared, service])

  const value = useMemo(
    () => ({ status, principal, error, refresh, signIn, signOut }),
    [status, principal, error, refresh, signIn, signOut],
  )

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useAppSession(): SessionContextValue {
  const value = useContext(SessionContext)
  if (!value) {
    throw new Error('useAppSession must be used inside SessionProvider')
  }
  return value
}
