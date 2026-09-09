import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildApp } from '../../app.js'
import { PrismaCustomerRepository } from '../../modules/customers/customer.prisma-repository.js'
import { PrismaAccessProfileRepository } from '../authorization/access-profile.repository.js'
import { createAuthorizationGuards } from '../authorization/guards.js'
import { createPrismaClient } from '../database/prisma.js'
import { createAuth } from './auth.js'
import { createRequestContextResolver } from './session.js'

const databaseUrl = process.env.DATABASE_URL?.trim()
const describeDatabase = databaseUrl ? describe : describe.skip
const testSecret = 'cpxlabs-auth-integration-secret-0123456789abcdef'
const origin = 'http://127.0.0.1:4173'
const password = 'TestAuthPass123!'

describeDatabase('authentication and authorization integration', () => {
  const prisma = createPrismaClient(databaseUrl!)
  const accessProfiles = new PrismaAccessProfileRepository(prisma)
  const auth = createAuth({
    prisma,
    baseURL: 'http://127.0.0.1:3001',
    secret: testSecret,
    trustedOrigins: [origin],
    allowSignUp: true,
  })
  const resolveRequestContext = createRequestContextResolver({ auth, accessProfiles })
  const authorization = createAuthorizationGuards(resolveRequestContext)
  const app = buildApp({
    customerRepository: new PrismaCustomerRepository(prisma),
    authorization,
    authentication: { auth, resolveRequestContext },
  })
  const emails = {
    admin: `auth.admin.${Date.now()}@example.com`,
    manager: `auth.manager.${Date.now()}@example.com`,
    viewer: `auth.viewer.${Date.now()}@example.com`,
  } as const

  async function provision(role: keyof typeof emails) {
    const result = await auth.api.signUpEmail({
      body: {
        name: `Auth ${role}`,
        email: emails[role],
        password,
      },
    })
    await accessProfiles.upsert({
      userId: result.user.id,
      role,
      status: 'active',
    })
  }

  async function signIn(role: keyof typeof emails) {
    const response = await app.inject({
      method: 'POST',
      url: '/api/auth/sign-in/email',
      headers: { origin },
      payload: { email: emails[role], password },
    })
    expect(response.statusCode).toBe(200)

    const setCookie = response.headers['set-cookie']
    const cookies = Array.isArray(setCookie) ? setCookie : setCookie ? [setCookie] : []
    expect(cookies.length).toBeGreaterThan(0)

    return cookies.map((cookie) => cookie.split(';', 1)[0]).join('; ')
  }

  beforeAll(async () => {
    await app.ready()
    await provision('admin')
    await provision('manager')
    await provision('viewer')
  })

  afterAll(async () => {
    await app.close()
    await prisma.user.deleteMany({
      where: { email: { in: Object.values(emails) } },
    })
    await prisma.$disconnect()
  })

  it('rejects protected requests without a session and resolves the canonical session after sign-in', async () => {
    const anonymous = await app.inject({
      method: 'GET',
      url: '/api/customers?page=1&pageSize=25',
    })
    expect(anonymous.statusCode).toBe(401)
    expect(anonymous.json()).toMatchObject({
      error: { code: 'AUTHENTICATION_REQUIRED' },
    })

    const cookie = await signIn('admin')
    const session = await app.inject({
      method: 'GET',
      url: '/api/session',
      headers: { cookie },
    })

    expect(session.statusCode).toBe(200)
    expect(session.json()).toMatchObject({
      principal: {
        email: emails.admin,
        role: 'admin',
        capabilities: [
          'customers.read',
          'customers.create',
          'customers.update',
          'customers.delete',
        ],
      },
    })
  })

  it('enforces viewer and manager capabilities on direct API requests', async () => {
    const viewerCookie = await signIn('viewer')
    const viewerRead = await app.inject({
      method: 'GET',
      url: '/api/customers?page=1&pageSize=25',
      headers: { cookie: viewerCookie },
    })
    expect(viewerRead.statusCode).toBe(200)

    const viewerCreate = await app.inject({
      method: 'POST',
      url: '/api/customers',
      headers: { cookie: viewerCookie },
      payload: {
        name: 'Forbidden Customer',
        email: `forbidden.${Date.now()}@example.com`,
        company: 'CPXLabs',
        status: 'lead',
      },
    })
    expect(viewerCreate.statusCode).toBe(403)
    expect(viewerCreate.json()).toMatchObject({ error: { code: 'FORBIDDEN' } })

    const managerCookie = await signIn('manager')
    const managerCreate = await app.inject({
      method: 'POST',
      url: '/api/customers',
      headers: { cookie: managerCookie },
      payload: {
        name: 'Manager Customer',
        email: `manager.customer.${Date.now()}@example.com`,
        company: 'CPXLabs',
        status: 'lead',
      },
    })
    expect(managerCreate.statusCode).toBe(201)
    const created = managerCreate.json<{ id: string }>()

    const managerDelete = await app.inject({
      method: 'DELETE',
      url: `/api/customers/${created.id}`,
      headers: { cookie: managerCookie },
    })
    expect(managerDelete.statusCode).toBe(403)

    await prisma.customer.deleteMany({ where: { id: created.id } })
  })

  it('denies a previously authenticated user immediately after the access profile is disabled', async () => {
    const cookie = await signIn('viewer')
    const user = await prisma.user.findUniqueOrThrow({ where: { email: emails.viewer } })
    await accessProfiles.setStatus(user.id, 'disabled')

    const response = await app.inject({
      method: 'GET',
      url: '/api/customers?page=1&pageSize=25',
      headers: { cookie },
    })

    expect(response.statusCode).toBe(403)
    expect(response.json()).toMatchObject({ error: { code: 'ACCESS_DISABLED' } })

    await accessProfiles.setStatus(user.id, 'active')
  })
})
