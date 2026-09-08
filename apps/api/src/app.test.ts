import { afterEach, describe, expect, it } from 'vitest'

import { buildApp } from './app.js'

const apps: ReturnType<typeof buildApp>[] = []

afterEach(async () => {
  await Promise.all(apps.splice(0).map((app) => app.close()))
})

function createApp() {
  const app = buildApp()
  apps.push(app)
  return app
}

describe('reference API', () => {
  it('exposes health and customer list endpoints', async () => {
    const app = createApp()

    const health = await app.inject({ method: 'GET', url: '/health' })
    expect(health.statusCode).toBe(200)
    expect(health.json()).toEqual({ status: 'ok' })

    const customers = await app.inject({
      method: 'GET',
      url: '/api/customers?page=1&pageSize=25&sort=name&direction=asc',
    })
    expect(customers.statusCode).toBe(200)
    expect(customers.json()).toMatchObject({ total: 2 })
  })

  it('implements create, read, update and delete with the shared HTTP shape', async () => {
    const app = createApp()
    const input = {
      name: 'Vercel Customer',
      email: 'vercel@example.com',
      company: 'CPX Labs',
      status: 'lead',
    }

    const created = await app.inject({ method: 'POST', url: '/api/customers', payload: input })
    expect(created.statusCode).toBe(201)
    const customer = created.json<{ id: string; name: string }>()

    const found = await app.inject({ method: 'GET', url: `/api/customers/${customer.id}` })
    expect(found.statusCode).toBe(200)
    expect(found.json()).toMatchObject({ name: 'Vercel Customer' })

    const updated = await app.inject({
      method: 'PATCH',
      url: `/api/customers/${customer.id}`,
      payload: { ...input, name: 'Updated Customer', status: 'active' },
    })
    expect(updated.statusCode).toBe(200)
    expect(updated.json()).toMatchObject({ name: 'Updated Customer', status: 'active' })

    const deleted = await app.inject({ method: 'DELETE', url: `/api/customers/${customer.id}` })
    expect(deleted.statusCode).toBe(204)

    const missing = await app.inject({ method: 'GET', url: `/api/customers/${customer.id}` })
    expect(missing.statusCode).toBe(404)
    expect(missing.json()).toMatchObject({
      error: { code: 'not_found', message: 'Customer not found' },
    })
  })

  it('maps validation failures to the stable error envelope', async () => {
    const app = createApp()
    const response = await app.inject({
      method: 'POST',
      url: '/api/customers',
      payload: { name: '', email: 'not-an-email', company: '', status: 'invalid' },
    })

    expect(response.statusCode).toBe(400)
    expect(response.json()).toMatchObject({ error: { code: 'validation' } })
  })
})
