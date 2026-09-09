import { createPrincipal } from '@cpxlabs-admin/authorization'
import { describe, expect, it } from 'vitest'

import { buildApp } from '../../app.js'
import { createAuthorizationGuards } from '../authorization/guards.js'
import { InMemoryAuditRepository } from './audit.repository.js'

function authorizationFor(role: 'admin' | 'manager' | 'viewer') {
  const principal = createPrincipal({
    id: `${role}-audit-user`,
    email: `${role}@example.com`,
    name: role,
    role,
  })
  return createAuthorizationGuards(async () => ({ principal }))
}

async function repositoryWithEvent() {
  const repository = new InMemoryAuditRepository()
  await repository.append({
    actorId: 'admin-audit-user',
    actorEmail: 'admin@example.com',
    actorName: 'Admin',
    action: 'customers.update',
    subjectType: 'customer',
    subjectId: 'cus_audit',
    before: null,
    after: null,
    correlationId: 'request-audit',
    tenantId: null,
  })
  return repository
}

describe('GET /api/audit-events', () => {
  it('allows Admin and returns the documented nested actor/subject contract', async () => {
    const repository = await repositoryWithEvent()
    const app = buildApp({ auditRepository: repository, authorization: authorizationFor('admin') })
    const response = await app.inject({ method: 'GET', url: '/api/audit-events?limit=10' })

    expect(response.statusCode).toBe(200)
    expect(response.json()).toMatchObject({
      data: [
        {
          actor: { id: 'admin-audit-user', email: 'admin@example.com', name: 'Admin' },
          action: 'customers.update',
          subject: { type: 'customer', id: 'cus_audit' },
          correlationId: 'request-audit',
        },
      ],
      nextCursor: null,
    })
    await app.close()
  })

  for (const role of ['manager', 'viewer'] as const) {
    it(`denies ${role} with 403`, async () => {
      const app = buildApp({
        auditRepository: await repositoryWithEvent(),
        authorization: authorizationFor(role),
      })
      const response = await app.inject({ method: 'GET', url: '/api/audit-events' })
      expect(response.statusCode).toBe(403)
      expect(response.json().error.code).toBe('FORBIDDEN')
      await app.close()
    })
  }

  it('denies requests without an authenticated principal with 401', async () => {
    const app = buildApp({ auditRepository: await repositoryWithEvent() })
    const response = await app.inject({ method: 'GET', url: '/api/audit-events' })
    expect(response.statusCode).toBe(401)
    expect(response.json().error.code).toBe('AUTHENTICATION_REQUIRED')
    await app.close()
  })
})
