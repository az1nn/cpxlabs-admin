import { afterAll, describe, expect, it } from 'vitest'

import { createPrismaClient } from '../database/prisma.js'
import { PrismaAccessProfileRepository } from './access-profile.repository.js'

const databaseUrl = process.env.DATABASE_URL?.trim()
const describeDatabase = databaseUrl ? describe : describe.skip

describeDatabase('PrismaAccessProfileRepository', () => {
  const prisma = createPrismaClient(databaseUrl!)
  const repository = new PrismaAccessProfileRepository(prisma)
  const userId = `user_clerk_access_profile_${Date.now()}`

  afterAll(async () => {
    await prisma.accessProfile.deleteMany({ where: { userId } })
    await prisma.$disconnect()
  })

  it('stores an external identity id without requiring a local provider user row', async () => {
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
