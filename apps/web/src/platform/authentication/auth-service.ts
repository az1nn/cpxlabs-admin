import type { SessionResponse } from '@cpxlabs-admin/contracts'

import { env } from '../../config/env'
import { demoPrincipal } from '../authorization/demo-principal'
import { authClient } from './auth-client'

export type SignInCredentials = {
  email: string
  password: string
}

export class AuthenticationError extends Error {
  constructor(message = 'Invalid email or password') {
    super(message)
    this.name = 'AuthenticationError'
  }
}

export class AccessUnavailableError extends Error {
  constructor(message = 'Application access is not available') {
    super(message)
    this.name = 'AccessUnavailableError'
  }
}

export type AuthService = {
  getSession(): Promise<SessionResponse | null>
  signIn(credentials: SignInCredentials): Promise<void>
  signOut(): Promise<void>
}

type AuthClientPort = {
  signInEmail(credentials: SignInCredentials): Promise<{ error?: unknown }>
  signOut(): Promise<{ error?: unknown }>
}

export function createServerAuthService(options: {
  fetcher?: typeof fetch
  client: AuthClientPort
}): AuthService {
  const fetcher = options.fetcher ?? fetch

  return {
    async getSession() {
      const response = await fetcher('/api/session', {
        method: 'GET',
        credentials: 'include',
        cache: 'no-store',
        headers: { accept: 'application/json' },
      })

      if (response.status === 401) {
        return null
      }

      if (response.status === 403) {
        throw new AccessUnavailableError()
      }

      if (!response.ok) {
        throw new Error(`Session request failed with status ${response.status}`)
      }

      return response.json() as Promise<SessionResponse>
    },

    async signIn(credentials) {
      const result = await options.client.signInEmail(credentials)
      if (result.error) {
        throw new AuthenticationError()
      }
    },

    async signOut() {
      const result = await options.client.signOut()
      if (result.error) {
        throw new Error('Unable to sign out')
      }
    },
  }
}

const serverAuthService = createServerAuthService({
  client: {
    signInEmail: (credentials) => authClient.signIn.email(credentials),
    signOut: () => authClient.signOut(),
  },
})

const demoAuthService: AuthService = {
  async getSession() {
    return {
      principal: {
        id: demoPrincipal.id,
        email: demoPrincipal.email,
        name: demoPrincipal.name,
        role: demoPrincipal.role,
        capabilities: [...demoPrincipal.capabilities],
      },
    }
  },
  async signIn() {},
  async signOut() {},
}

export const appAuthService =
  env.VITE_AUTH_MODE === 'demo' ? demoAuthService : serverAuthService
