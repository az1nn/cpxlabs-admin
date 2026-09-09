import { describe, expect, it, vi } from 'vitest'

import {
  AccessUnavailableError,
  AuthenticationError,
  createServerAuthService,
} from './auth-service'

const sessionBody = {
  principal: {
    id: 'usr_1',
    email: 'admin@example.com',
    name: 'Admin',
    role: 'admin' as const,
    capabilities: [
      'customers.read',
      'customers.create',
      'customers.update',
      'customers.delete',
    ],
  },
}

function createClient(options: { signInError?: boolean; signOutError?: boolean } = {}) {
  return {
    signInEmail: vi.fn(async () => ({ error: options.signInError ? {} : undefined })),
    signOut: vi.fn(async () => ({ error: options.signOutError ? {} : undefined })),
  }
}

describe('server AuthService', () => {
  it('loads the application-owned session DTO with credentialed no-store fetch', async () => {
    const fetcher = vi.fn(async () => Response.json(sessionBody))
    const service = createServerAuthService({ fetcher, client: createClient() })

    await expect(service.getSession()).resolves.toEqual(sessionBody)
    expect(fetcher).toHaveBeenCalledWith('/api/session', {
      method: 'GET',
      credentials: 'include',
      cache: 'no-store',
      headers: { accept: 'application/json' },
    })
  })

  it('maps missing and disabled application sessions distinctly', async () => {
    const anonymous = createServerAuthService({
      fetcher: vi.fn(async () => new Response(null, { status: 401 })),
      client: createClient(),
    })
    await expect(anonymous.getSession()).resolves.toBeNull()

    const disabled = createServerAuthService({
      fetcher: vi.fn(async () => new Response(null, { status: 403 })),
      client: createClient(),
    })
    await expect(disabled.getSession()).rejects.toBeInstanceOf(AccessUnavailableError)
  })

  it('does not expose provider credential errors to the UI', async () => {
    const service = createServerAuthService({
      fetcher: vi.fn(),
      client: createClient({ signInError: true }),
    })

    await expect(
      service.signIn({ email: 'unknown@example.com', password: 'wrong' }),
    ).rejects.toEqual(new AuthenticationError())
  })

  it('surfaces failed sign-out without retaining provider details', async () => {
    const service = createServerAuthService({
      fetcher: vi.fn(),
      client: createClient({ signOutError: true }),
    })

    await expect(service.signOut()).rejects.toThrow('Unable to sign out')
  })
})
