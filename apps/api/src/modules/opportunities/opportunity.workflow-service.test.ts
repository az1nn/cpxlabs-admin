import { createPrincipal } from '@cpxlabs-admin/authorization'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { PrismaAuditRepository } from '../../platform/audit/audit.prisma-repository.js'
import { createPrismaClient, type AppPrismaClient } from '../../platform/database/prisma.js'
import { PrismaOpportunityWorkflowService } from './opportunity.workflow-service.js'

const databaseUrl = process.env.DATABASE_URL
const describeDatabase = databaseUrl ? describe : describe.skip

describeDatabase('PrismaOpportunityWorkflowService', () => {
  let prisma: AppPrismaClient
  const ids: string[] = []
  const principal = createPrincipal({
    id: 'opportunity-workflow-admin',
    email: 'opportunity-admin@example.com',
    name: 'Opportunity Admin',
    role: 'admin',
  })

  beforeAll(() => {
    prisma = createPrismaClient(databaseUrl!)
  })

  afterAll(async () => {
    if (!prisma) return
    if (ids.length > 0) {
      await prisma.auditEvent.deleteMany({ where: { subjectType: 'opportunity', subjectId: { in: ids } } })
      await prisma.opportunity.deleteMany({ where: { id: { in: ids } } })
    }
    await prisma.opportunity.deleteMany({ where: { name: { startsWith: 'Rollback Opportunity' } } })
    await prisma.$disconnect()
  })

  it('creates qualification/version 1 and audits exactly once', async () => {
    const service = new PrismaOpportunityWorkflowService(prisma)
    const audit = new PrismaAuditRepository(prisma)
    const requestId = crypto.randomUUID()
    const created = await service.create(
      {
        name: 'Workflow Opportunity',
        accountName: 'Acme Brasil',
        amountMinor: 12500000,
        currency: 'BRL',
        expectedCloseDate: '2026-11-30',
      },
      { principal, requestId },
    )
    ids.push(created.id)

    expect(created).toMatchObject({ stage: 'qualification', version: 1, lossReason: null })
    const events = await audit.list({ subjectType: 'opportunity', subjectId: created.id, limit: 10 })
    expect(events.data).toHaveLength(1)
    expect(events.data[0]).toMatchObject({
      action: 'opportunities.create',
      correlationId: requestId,
      subject: { type: 'opportunity', id: created.id },
    })
    expect(events.data[0]!.before).toBeNull()
    expect(events.data[0]!.after).toMatchObject({
      id: created.id,
      stage: 'qualification',
      version: 1,
    })
  })

  it('commits valid transitions with audit and rejects invalid terminal transitions', async () => {
    const service = new PrismaOpportunityWorkflowService(prisma)
    const audit = new PrismaAuditRepository(prisma)
    const created = await service.create(
      {
        name: 'Lifecycle Opportunity',
        accountName: 'Lifecycle Co',
        amountMinor: 900000,
        currency: 'BRL',
        expectedCloseDate: '2026-12-15',
      },
      { principal, requestId: crypto.randomUUID() },
    )
    ids.push(created.id)

    const discovery = await service.transition(
      created.id,
      { targetStage: 'discovery', expectedVersion: 1 },
      { principal, requestId: crypto.randomUUID() },
    )
    expect(discovery).toMatchObject({ stage: 'discovery', version: 2 })

    const lost = await service.transition(
      created.id,
      { targetStage: 'lost', expectedVersion: 2, lossReason: '  Budget frozen  ' },
      { principal, requestId: crypto.randomUUID() },
    )
    expect(lost).toMatchObject({ stage: 'lost', version: 3, lossReason: 'Budget frozen' })

    const beforeEvents = await audit.list({ subjectType: 'opportunity', subjectId: created.id, limit: 10 })
    await expect(
      service.transition(
        created.id,
        { targetStage: 'qualification', expectedVersion: 3 },
        { principal, requestId: crypto.randomUUID() },
      ),
    ).rejects.toMatchObject({ code: 'WORKFLOW_INVALID_TRANSITION', statusCode: 409 })
    const afterEvents = await audit.list({ subjectType: 'opportunity', subjectId: created.id, limit: 10 })
    expect(afterEvents.data).toHaveLength(beforeEvents.data.length)
    expect((await prisma.opportunity.findUniqueOrThrow({ where: { id: created.id } })).version).toBe(3)
  })

  it('allows at most one concurrent transition for one expectedVersion', async () => {
    const service = new PrismaOpportunityWorkflowService(prisma)
    const created = await service.create(
      {
        name: 'Concurrent Opportunity',
        accountName: 'Concurrent Co',
        amountMinor: 100000,
        currency: 'BRL',
        expectedCloseDate: '2026-10-10',
      },
      { principal, requestId: crypto.randomUUID() },
    )
    ids.push(created.id)

    const results = await Promise.allSettled([
      service.transition(
        created.id,
        { targetStage: 'discovery', expectedVersion: 1 },
        { principal, requestId: crypto.randomUUID() },
      ),
      service.transition(
        created.id,
        { targetStage: 'lost', expectedVersion: 1, lossReason: 'Concurrent loss' },
        { principal, requestId: crypto.randomUUID() },
      ),
    ])

    expect(results.filter((result) => result.status === 'fulfilled')).toHaveLength(1)
    expect(results.filter((result) => result.status === 'rejected')).toHaveLength(1)
    const rejected = results.find((result) => result.status === 'rejected')
    expect(rejected && rejected.status === 'rejected' ? rejected.reason : null).toMatchObject({
      code: 'WORKFLOW_CONFLICT',
      statusCode: 409,
    })
    expect((await prisma.opportunity.findUniqueOrThrow({ where: { id: created.id } })).version).toBe(2)
  })

  it('rolls back create and transition when audit persistence fails', async () => {
    const failing = new PrismaOpportunityWorkflowService(prisma, async () => {
      throw new Error('simulated audit failure')
    })
    const rollbackName = `Rollback Opportunity ${Date.now()}`

    await expect(
      failing.create(
        {
          name: rollbackName,
          accountName: 'Rollback Co',
          amountMinor: 1000,
          currency: 'BRL',
          expectedCloseDate: '2026-10-20',
        },
        { principal, requestId: crypto.randomUUID() },
      ),
    ).rejects.toMatchObject({ code: 'infrastructure', statusCode: 500 })
    expect(await prisma.opportunity.findFirst({ where: { name: rollbackName } })).toBeNull()

    const healthy = new PrismaOpportunityWorkflowService(prisma)
    const created = await healthy.create(
      {
        name: 'Rollback Opportunity Transition',
        accountName: 'Rollback Co',
        amountMinor: 2000,
        currency: 'BRL',
        expectedCloseDate: '2026-10-21',
      },
      { principal, requestId: crypto.randomUUID() },
    )
    ids.push(created.id)

    await expect(
      failing.transition(
        created.id,
        { targetStage: 'discovery', expectedVersion: 1 },
        { principal, requestId: crypto.randomUUID() },
      ),
    ).rejects.toMatchObject({ code: 'infrastructure', statusCode: 500 })
    const persisted = await prisma.opportunity.findUniqueOrThrow({ where: { id: created.id } })
    expect(persisted.stage).toBe('qualification')
    expect(persisted.version).toBe(1)
  })
})
