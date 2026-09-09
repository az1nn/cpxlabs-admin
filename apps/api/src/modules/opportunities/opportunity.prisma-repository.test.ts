import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { createPrismaClient, type AppPrismaClient } from '../../platform/database/prisma.js'
import { PrismaOpportunityRepository } from './opportunity.prisma-repository.js'

const databaseUrl = process.env.DATABASE_URL
const describeDatabase = databaseUrl ? describe : describe.skip

describeDatabase('PrismaOpportunityRepository', () => {
  let prisma: AppPrismaClient
  const ids: string[] = []

  beforeAll(async () => {
    prisma = createPrismaClient(databaseUrl!)
    for (const [name, accountName, stage, amountMinor, expectedCloseDate] of [
      ['Alpha Renewal', 'Acme Brasil', 'qualification', 100_00n, '2026-10-01'],
      ['Beta Expansion', 'Beta Retail', 'proposal', 250_00n, '2026-11-15'],
      ['Gamma Upsell', 'Acme Brasil', 'negotiation', 500_00n, '2026-12-20'],
    ] as const) {
      const row = await prisma.opportunity.create({
        data: {
          name,
          accountName,
          stage,
          amountMinor,
          currency: 'BRL',
          expectedCloseDate: new Date(`${expectedCloseDate}T00:00:00.000Z`),
        },
      })
      ids.push(row.id)
    }
  })

  afterAll(async () => {
    if (!prisma) return
    await prisma.opportunity.deleteMany({ where: { id: { in: ids } } })
    await prisma.$disconnect()
  })

  it('lists with search, stage filter and stable transport mapping', async () => {
    const repository = new PrismaOpportunityRepository(prisma)
    const result = await repository.list({
      page: 1,
      pageSize: 10,
      search: 'Acme',
      stage: 'negotiation',
      sort: 'amountMinor',
      direction: 'desc',
    })

    expect(result.total).toBe(1)
    expect(result.data[0]).toMatchObject({
      name: 'Gamma Upsell',
      accountName: 'Acme Brasil',
      amountMinor: 500_00,
      expectedCloseDate: '2026-12-20',
      stage: 'negotiation',
      version: 1,
    })
  })

  it('returns detail and maps missing rows to not_found', async () => {
    const repository = new PrismaOpportunityRepository(prisma)
    const found = await repository.get(ids[0]!)
    expect(found.id).toBe(ids[0])
    await expect(repository.get('missing-opportunity')).rejects.toMatchObject({
      code: 'not_found',
      statusCode: 404,
    })
  })
})
