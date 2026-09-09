import type { SessionResponse } from '@cpxlabs-admin/contracts'

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

export const appAuthService: AuthService = {
  async getSession() {
    const response = await fetch('/api/session', {
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
    const result = await authClient.signIn.email({
      email: credentials.email,
      password: credentials.password,
    })

    if (result.error) {
      throw new AuthenticationError()
    }
  },

  async signOut() {
    const result = await authClient.signOut()
    if (result.error) {
      throw new Error('Unable to sign out')
    }
  },
}
