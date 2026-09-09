import { createPrincipal } from '@cpxlabs-admin/authorization'
import { afterEach, describe, expect, it } from 'vitest'

import { buildApp } from '../../app.js'
import { InMemoryAuditRepository } from '../../platform/audit/audit.repository.js'
import { createAuthorizationGuards } from '../../platform/authorization/guards.js'

const apps: ReturnType<typeof buildApp>[] = []

function authorizationFor(role: 'admin' | 'manager' | 'viewer') {
  const principal = createPrincipal({
    id: `${role}-audit-policy`,
    email: `${role}-audit-policy@example.com`,
    name: `${role} audit policy`,
    role,
  })
  return createAuthorizationGuards(async () => ({ principal }))
}

const validInput = {
  name: 'Audit Policy Customer',
  email: 'audit-policy@example.com',
  company: 'CPX Labs',
  status: 'lead' as const,
}

afterEach(async () => {
  await Promise.all(apps.splice(0).map((app) => app.close()))
})

function track(app: ReturnType<typeof buildApp>) {
  apps.push(app)
  return app
}

async function expectNoAudit(repository: InMemoryAuditRepository) {
  const events = await repository.list({ limit: 100 })
  expect(events.data).toHaveLength(0)
}

describe('customer audit policy', () => {
  it('does not append domain audit for read-only requests', async () => {
    const audit = new InMemoryAuditRepository()
    const app = track(buildApp({ auditRepository: audit, authorization: authorizationFor('admin') }))

    const response = await app.inject({
      method: 'GET',
      url: '/api/customers?page=1&pageSize=25',
    })

    expect(response.statusCode).toBe(200)
    await expectNoAudit(audit)
  })

  it('does not append domain audit for unauthenticated or forbidden mutations', async () => {
    const unauthenticatedAudit = new InMemoryAuditRepository()
    const unauthenticatedApp = track(buildApp({ auditRepository: unauthenticatedAudit }))
    const unauthenticated = await unauthenticatedApp.inject({
      method: 'POST',
      url: '/api/customers',
      payload: validInput,
    })
    expect(unauthenticated.statusCode).toBe(401)
    await expectNoAudit(unauthenticatedAudit)

    const forbiddenAudit = new InMemoryAuditRepository()
    const forbiddenApp = track(
      buildApp({ auditRepository: forbiddenAudit, authorization: authorizationFor('viewer') }),
    )
    const forbidden = await forbiddenApp.inject({
      method: 'POST',
      url: '/api/customers',
      payload: validInput,
    })
    expect(forbidden.statusCode).toBe(403)
    await expectNoAudit(forbiddenAudit)
  })

  it('does not append domain audit for validation or not-found failures', async () => {
    const audit = new InMemoryAuditRepository()
    const app = track(buildApp({ auditRepository: audit, authorization: authorizationFor('admin') }))

    const validation = await app.inject({
      method: 'POST',
      url: '/api/customers',
      payload: { name: '', email: 'invalid', company: '', status: 'invalid' },
    })
    expect(validation.statusCode).toBe(400)
    await expectNoAudit(audit)

    const missing = await app.inject({
      method: 'PATCH',
      url: '/api/customers/customer-does-not-exist',
      payload: validInput,
    })
    expect(missing.statusCode).toBe(404)
    await expectNoAudit(audit)
  })

  it('stores the same request correlation id for a committed mutation', async () => {
    const audit = new InMemoryAuditRepository()
    const app = track(buildApp({ auditRepository: audit, authorization: authorizationFor('admin') }))
    const response = await app.inject({
      method: 'POST',
      url: '/api/customers',
      payload: { ...validInput, email: 'audit-correlation@example.com' },
    })

    expect(response.statusCode).toBe(201)
    const requestId = response.headers['x-request-id']
    const events = await audit.list({ limit: 100 })
    expect(events.data).toHaveLength(1)
    expect(events.data[0]!.correlationId).toBe(requestId)
  })
})
