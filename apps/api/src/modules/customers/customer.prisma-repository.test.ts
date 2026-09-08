import { afterAll, describe, expect, it } from 'vitest'

import { createPrismaClient } from '../../platform/database/prisma.js'
import { PrismaCustomerRepository } from './customer.prisma-repository.js'

const databaseUrl = process.env.DATABASE_URL?.trim()
const describeDatabase = databaseUrl ? describe : describe.skip

describeDatabase('PrismaCustomerRepository', () => {
  const prisma = createPrismaClient(databaseUrl!)
  const repository = new PrismaCustomerRepository(prisma)
  const email = `repository.${Date.now()}@example.com`

  afterAll(async () => {
    await prisma.customer.deleteMany({ where: { email } })
    await prisma.$disconnect()
  })

  it('persists list, create, update, get and delete operations', async () => {
    const created = await repository.create({
      name: 'Repository Customer',
      company: 'CPXLabs',
      email,
      status: 'lead',
    })

    await expect(repository.get(created.id)).resolves.toMatchObject({
      id: created.id,
      email,
      status: 'lead',
    })

    const updated = await repository.update(created.id, {
      name: 'Repository Customer Updated',
      company: 'CPXLabs',
      email,
      status: 'active',
    })

    expect(updated.status).toBe('active')

    const listed = await repository.list({
      page: 1,
      pageSize: 25,
      search: 'Repository Customer Updated',
      status: 'active',
      sort: 'name',
      direction: 'asc',
    })

    expect(listed.total).toBeGreaterThanOrEqual(1)
    expect(listed.data.some((customer) => customer.id === created.id)).toBe(true)

    await repository.delete(created.id)

    await expect(repository.get(created.id)).rejects.toMatchObject({
      code: 'not_found',
      statusCode: 404,
    })
  })
})
