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
})
