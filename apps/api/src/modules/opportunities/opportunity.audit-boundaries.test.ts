import { createPrincipal } from '@cpxlabs-admin/authorization'
import { describe, expect, it } from 'vitest'

import { buildApp } from '../../app.js'
import { InMemoryAuditRepository } from '../../platform/audit/audit.repository.js'
import { createAuthorizationGuards } from '../../platform/authorization/guards.js'

function authorizationFor(role: 'admin' | 'viewer') {
  const principal = createPrincipal({
    id: `${role}-audit-boundary`,
    email: `${role}-audit-boundary@example.com`,
    name: role,
    role,
  })
  return createAuthorizationGuards(async () => ({ principal }))
}

async function opportunityAuditCount(repository: InMemoryAuditRepository) {
  return (await repository.list({ subjectType: 'opportunity', limit: 100 })).data.length
}

describe('opportunity audit boundaries', () => {
  it('appends no successful audit for forbidden or validation-rejected commands', async () => {
    const viewerAudit = new InMemoryAuditRepository()
    const viewerApp = buildApp({ auditRepository: viewerAudit, authorization: authorizationFor('viewer') })
    const forbidden = await viewerApp.inject({
      method: 'POST',
      url: '/api/opportunities',
      payload: {
        name: 'Forbidden',
        accountName: 'Forbidden',
        amountMinor: 100,
        currency: 'BRL',
        expectedCloseDate: '2026-11-30',
      },
    })
    expect(forbidden.statusCode).toBe(403)
    expect(await opportunityAuditCount(viewerAudit)).toBe(0)
    await viewerApp.close()

    const adminAudit = new InMemoryAuditRepository()
    const adminApp = buildApp({ auditRepository: adminAudit, authorization: authorizationFor('admin') })
    const invalid = await adminApp.inject({
      method: 'POST',
      url: '/api/opportunities',
      payload: {
        name: '',
        accountName: '',
        amountMinor: -1,
        currency: 'brl',
        expectedCloseDate: 'invalid-date',
      },
    })
    expect(invalid.statusCode).toBe(400)
    expect(await opportunityAuditCount(adminAudit)).toBe(0)
    await adminApp.close()
  })

  it('appends no audit for invalid, stale or missing transition commands', async () => {
    const audit = new InMemoryAuditRepository()
    const app = buildApp({ auditRepository: audit, authorization: authorizationFor('admin') })
    const list = await app.inject({ method: 'GET', url: '/api/opportunities?page=1&pageSize=25' })
    const opportunity = list.json<{ data: { id: string }[] }>().data[0]!

    const invalid = await app.inject({
      method: 'POST',
      url: `/api/opportunities/${opportunity.id}/commands/transition`,
      payload: { targetStage: 'proposal', expectedVersion: 1 },
    })
    expect(invalid.statusCode).toBe(409)
    expect(await opportunityAuditCount(audit)).toBe(0)

    const valid = await app.inject({
      method: 'POST',
      url: `/api/opportunities/${opportunity.id}/commands/transition`,
      payload: { targetStage: 'discovery', expectedVersion: 1 },
    })
    expect(valid.statusCode).toBe(200)
    expect(await opportunityAuditCount(audit)).toBe(1)

    const stale = await app.inject({
      method: 'POST',
      url: `/api/opportunities/${opportunity.id}/commands/transition`,
      payload: { targetStage: 'proposal', expectedVersion: 1 },
    })
    expect(stale.statusCode).toBe(409)
    expect(await opportunityAuditCount(audit)).toBe(1)

    const missing = await app.inject({
      method: 'POST',
      url: '/api/opportunities/missing-opportunity/commands/transition',
      payload: { targetStage: 'discovery', expectedVersion: 1 },
    })
    expect(missing.statusCode).toBe(404)
    expect(await opportunityAuditCount(audit)).toBe(1)
    await app.close()
  })
})
