import { createPrincipal } from '@cpxlabs-admin/authorization'
import { afterEach, describe, expect, it } from 'vitest'

import { buildApp } from '../../app.js'
import type { AuthorizationGuards } from '../authorization/guards.js'

const apps: ReturnType<typeof buildApp>[] = []
const adminContext = {
  principal: createPrincipal({
    id: 'correlation-admin',
    email: 'correlation-admin@example.com',
    name: 'Correlation Admin',
    role: 'admin',
  }),
}
const allowAllAuthorization: AuthorizationGuards = {
  async requirePrincipal() {
    return adminContext
  },
  async requireCapability() {
    return adminContext
  },
}

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

afterEach(async () => {
  await Promise.all(apps.splice(0).map((app) => app.close()))
})

function createApp() {
  const app = buildApp({ authorization: allowAllAuthorization })
  apps.push(app)
  return app
}

describe('request correlation', () => {
  it('returns a server-generated UUID request id on successful responses', async () => {
    const response = await createApp().inject({ method: 'GET', url: '/health' })

    expect(response.statusCode).toBe(200)
    expect(response.headers['x-request-id']).toMatch(uuidPattern)
  })

  it('uses the same request id in the response header and application error envelope', async () => {
    const response = await createApp().inject({
      method: 'POST',
      url: '/api/customers',
      payload: { name: '', email: 'invalid', company: '', status: 'invalid' },
    })

    expect(response.statusCode).toBe(400)
    const requestId = response.headers['x-request-id']
    expect(requestId).toMatch(uuidPattern)
    expect(response.json().error.requestId).toBe(requestId)
  })
})
