import { createPrincipal } from '@cpxlabs-admin/authorization'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { PrismaAuditRepository } from '../../platform/audit/audit.prisma-repository.js'
import { createPrismaClient, type AppPrismaClient } from '../../platform/database/prisma.js'
import { PrismaCustomerMutationService } from './customer.mutation-service.js'

const databaseUrl = process.env.DATABASE_URL
const describeDatabase = databaseUrl ? describe : describe.skip

describeDatabase('PrismaCustomerMutationService', () => {
  let prisma: AppPrismaClient
  const createdIds: string[] = []
  const principal = createPrincipal({
    id: 'audit-test-admin',
    email: 'audit-admin@example.com',
    name: 'Audit Admin',
    role: 'admin',
  })

  beforeAll(() => {
    prisma = createPrismaClient(databaseUrl!)
  })

  afterAll(async () => {
    if (!prisma) return
    if (createdIds.length > 0) {
      await prisma.auditEvent.deleteMany({ where: { subjectId: { in: createdIds } } })
      await prisma.customer.deleteMany({ where: { id: { in: createdIds } } })
    }
    await prisma.customer.deleteMany({ where: { email: { contains: 'audit-rollback-' } } })
    await prisma.$disconnect()
  })

  it('writes exactly one safe durable audit event for create, update and delete', async () => {
    const audit = new PrismaAuditRepository(prisma)
    const service = new PrismaCustomerMutationService(prisma)
    const email = `audit-${Date.now()}@example.com`
    const context = { principal, requestId: crypto.randomUUID() }

    const created = await service.create(
      { name: 'Audit Customer', email, company: 'Audit Co', status: 'lead' },
      context,
    )
    createdIds.push(created.id)
    await service.update(
      created.id,
      { name: 'Audit Customer Updated', email, company: 'Audit Co', status: 'active' },
      { principal, requestId: crypto.randomUUID() },
    )
    await service.delete(created.id, { principal, requestId: crypto.randomUUID() })

    const events = await audit.list({ subjectType: 'customer', subjectId: created.id, limit: 10 })
    expect(events.data).toHaveLength(3)
    expect(events.data.map((event) => event.action).sort()).toEqual([
      'customers.create',
      'customers.delete',
      'customers.update',
    ])
    expect(events.data.every((event) => event.actor.id === principal.id)).toBe(true)
    expect(events.data.every((event) => event.subject.id === created.id)).toBe(true)
    expect(events.data.some((event) => event.action === 'customers.delete' && event.after === null)).toBe(true)
    expect(await prisma.customer.findUnique({ where: { id: created.id } })).toBeNull()
  })

  it('rolls back the customer mutation when audit persistence fails', async () => {
    const email = `audit-rollback-${Date.now()}@example.com`
    const service = new PrismaCustomerMutationService(prisma, async () => {
      throw new Error('simulated audit failure')
    })

    await expect(
      service.create(
        { name: 'Rollback Customer', email, company: 'Rollback Co', status: 'lead' },
        { principal, requestId: crypto.randomUUID() },
      ),
    ).rejects.toMatchObject({ code: 'infrastructure', statusCode: 500 })

    expect(await prisma.customer.findUnique({ where: { email } })).toBeNull()
  })
})
