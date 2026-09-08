import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { createPrismaClient } from '../database/prisma.js'
import { PrismaAccessProfileRepository } from './access-profile.repository.js'

const databaseUrl = process.env.DATABASE_URL?.trim()
const describeDatabase = databaseUrl ? describe : describe.skip

describeDatabase('PrismaAccessProfileRepository', () => {
  const prisma = createPrismaClient(databaseUrl!)
  const repository = new PrismaAccessProfileRepository(prisma)
  const userId = `access-profile-${Date.now()}`
  const email = `${userId}@example.com`

  beforeAll(async () => {
    await prisma.user.create({
      data: {
        id: userId,
        name: 'Access Profile Test',
        email,
        emailVerified: true,
      },
    })
  })

  afterAll(async () => {
    await prisma.user.deleteMany({ where: { id: userId } })
    await prisma.$disconnect()
  })

  it('creates, changes role, disables and restores an access profile', async () => {
    await expect(repository.getByUserId(userId)).resolves.toBeNull()

    const created = await repository.upsert({ userId, role: 'viewer' })
    expect(created).toMatchObject({ userId, role: 'viewer', status: 'active' })

    const promoted = await repository.upsert({ userId, role: 'manager' })
    expect(promoted).toMatchObject({ userId, role: 'manager', status: 'active' })

    const disabled = await repository.setStatus(userId, 'disabled')
    expect(disabled.status).toBe('disabled')
    await expect(repository.getByUserId(userId)).resolves.toMatchObject({
      userId,
      role: 'manager',
      status: 'disabled',
    })

    const restored = await repository.setStatus(userId, 'active')
    expect(restored.status).toBe('active')
  })
})
