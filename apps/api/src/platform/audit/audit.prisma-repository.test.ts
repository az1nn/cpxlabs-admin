import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { createPrismaClient, type AppPrismaClient } from '../database/prisma.js'
import { PrismaAuditRepository } from './audit.prisma-repository.js'

const databaseUrl = process.env.DATABASE_URL
const describeDatabase = databaseUrl ? describe : describe.skip

describeDatabase('PrismaAuditRepository', () => {
  let prisma: AppPrismaClient
  const actorId = `audit-repo-${Date.now()}`

  beforeAll(() => {
    prisma = createPrismaClient(databaseUrl!)
  })

  afterAll(async () => {
    if (!prisma) return
    await prisma.auditEvent.deleteMany({ where: { actorId } })
    await prisma.$disconnect()
  })

  it('persists append-only history and paginates with an opaque cursor', async () => {
    const repository = new PrismaAuditRepository(prisma)
    for (let index = 0; index < 3; index += 1) {
      await repository.append({
        actorId,
        actorEmail: 'audit-repo@example.com',
        actorName: 'Audit Repository',
        action: 'customers.create',
        subjectType: 'customer',
        subjectId: `deleted-subject-${index}`,
        before: null,
        after: null,
        correlationId: `correlation-${index}`,
        tenantId: null,
      })
    }

    const first = await repository.list({ actorId, limit: 2 })
    expect(first.data).toHaveLength(2)
    expect(first.nextCursor).toEqual(expect.any(String))
    expect(first.data.every((event) => event.actor.id === actorId)).toBe(true)

    const second = await repository.list({ actorId, limit: 2, cursor: first.nextCursor! })
    expect(second.data).toHaveLength(1)
    expect(second.nextCursor).toBeNull()
    expect(second.data[0]!.subject.id).toMatch(/^deleted-subject-/)
  })

  it('rejects malformed cursors through the application validation envelope boundary', async () => {
    const repository = new PrismaAuditRepository(prisma)
    await expect(repository.list({ actorId, cursor: 'not-a-valid-cursor' })).rejects.toMatchObject({
      code: 'validation',
      statusCode: 400,
    })
  })
})
