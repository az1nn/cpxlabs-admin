import { describe, expect, it } from 'vitest'

import { buildApp } from '../../app.js'

describe('request correlation', () => {
  it('exposes a UUID request id on successful responses', async () => {
    const app = buildApp()
    const response = await app.inject({ method: 'GET', url: '/health' })
    expect(response.statusCode).toBe(200)
    expect(response.headers['x-request-id']).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
    )
    await app.close()
  })

  it('uses the same request id in error headers and the application error envelope', async () => {
    const app = buildApp()
    const response = await app.inject({
      method: 'GET',
      url: '/api/customers?page=1&pageSize=20',
    })
    expect(response.statusCode).toBe(401)
    expect(response.json().error.requestId).toBe(response.headers['x-request-id'])
    await app.close()
  })
})
