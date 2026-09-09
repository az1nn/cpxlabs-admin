import { createPrincipal } from '@cpxlabs-admin/authorization'
import { describe, expect, it } from 'vitest'

import { buildApp } from '../../app.js'
import { createAuthorizationGuards } from '../../platform/authorization/guards.js'

function authorizationFor(role: 'admin' | 'manager' | 'viewer') {
  const principal = createPrincipal({
    id: `${role}-opportunity-user`,
    email: `${role}@example.com`,
    name: role,
    role,
  })
  return createAuthorizationGuards(async () => ({ principal }))
}

const input = {
  name: 'Route Opportunity',
  accountName: 'Route Account',
  amountMinor: 250000,
  currency: 'BRL',
  expectedCloseDate: '2026-11-30',
}

describe('opportunity API', () => {
  for (const role of ['admin', 'manager', 'viewer'] as const) {
    it(`allows ${role} to list and read`, async () => {
      const app = buildApp({ authorization: authorizationFor(role) })
      const list = await app.inject({ method: 'GET', url: '/api/opportunities?page=1&pageSize=25' })
      expect(list.statusCode).toBe(200)
      const opportunity = list.json<{ data: { id: string }[] }>().data[0]!
      const detail = await app.inject({ method: 'GET', url: `/api/opportunities/${opportunity.id}` })
      expect(detail.statusCode).toBe(200)
      await app.close()
    })
  }

  for (const role of ['admin', 'manager'] as const) {
    it(`allows ${role} to create and transition via explicit command`, async () => {
      const app = buildApp({ authorization: authorizationFor(role) })
      const created = await app.inject({ method: 'POST', url: '/api/opportunities', payload: input })
      expect(created.statusCode).toBe(201)
      const opportunity = created.json<{ id: string; version: number; stage: string }>()
      expect(opportunity).toMatchObject({ version: 1, stage: 'qualification' })

      const transitioned = await app.inject({
        method: 'POST',
        url: `/api/opportunities/${opportunity.id}/commands/transition`,
        payload: { targetStage: 'discovery', expectedVersion: 1 },
      })
      expect(transitioned.statusCode).toBe(200)
      expect(transitioned.json()).toMatchObject({ stage: 'discovery', version: 2 })
      await app.close()
    })
  }

  it('denies Viewer mutations while preserving read access', async () => {
    const app = buildApp({ authorization: authorizationFor('viewer') })
    const created = await app.inject({ method: 'POST', url: '/api/opportunities', payload: input })
    expect(created.statusCode).toBe(403)
    expect(created.json().error.code).toBe('FORBIDDEN')

    const list = await app.inject({ method: 'GET', url: '/api/opportunities?page=1&pageSize=25' })
    const opportunity = list.json<{ data: { id: string }[] }>().data[0]!
    const transitioned = await app.inject({
      method: 'POST',
      url: `/api/opportunities/${opportunity.id}/commands/transition`,
      payload: { targetStage: 'discovery', expectedVersion: 1 },
    })
    expect(transitioned.statusCode).toBe(403)
    expect(transitioned.json().error.code).toBe('FORBIDDEN')
    await app.close()
  })

  it('returns stable workflow errors with matching request correlation', async () => {
    const app = buildApp({ authorization: authorizationFor('admin') })
    const created = await app.inject({ method: 'POST', url: '/api/opportunities', payload: input })
    const opportunity = created.json<{ id: string }>()

    const invalid = await app.inject({
      method: 'POST',
      url: `/api/opportunities/${opportunity.id}/commands/transition`,
      payload: { targetStage: 'proposal', expectedVersion: 1 },
    })
    expect(invalid.statusCode).toBe(409)
    expect(invalid.json().error.code).toBe('WORKFLOW_INVALID_TRANSITION')
    expect(invalid.json().error.requestId).toBe(invalid.headers['x-request-id'])

    const valid = await app.inject({
      method: 'POST',
      url: `/api/opportunities/${opportunity.id}/commands/transition`,
      payload: { targetStage: 'discovery', expectedVersion: 1 },
    })
    expect(valid.statusCode).toBe(200)

    const stale = await app.inject({
      method: 'POST',
      url: `/api/opportunities/${opportunity.id}/commands/transition`,
      payload: { targetStage: 'proposal', expectedVersion: 1 },
    })
    expect(stale.statusCode).toBe(409)
    expect(stale.json().error).toMatchObject({
      code: 'WORKFLOW_CONFLICT',
      details: { expectedVersion: 1, currentVersion: 2 },
    })
    expect(stale.json().error.requestId).toBe(stale.headers['x-request-id'])
    await app.close()
  })

  it('does not expose generic update or delete endpoints', async () => {
    const app = buildApp({ authorization: authorizationFor('admin') })
    const created = await app.inject({ method: 'POST', url: '/api/opportunities', payload: input })
    const opportunity = created.json<{ id: string }>()
    expect((await app.inject({ method: 'PATCH', url: `/api/opportunities/${opportunity.id}`, payload: input })).statusCode).toBe(404)
    expect((await app.inject({ method: 'PUT', url: `/api/opportunities/${opportunity.id}`, payload: input })).statusCode).toBe(404)
    expect((await app.inject({ method: 'DELETE', url: `/api/opportunities/${opportunity.id}` })).statusCode).toBe(404)
    await app.close()
  })
})
