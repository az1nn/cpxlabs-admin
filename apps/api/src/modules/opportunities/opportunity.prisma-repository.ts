import type { Opportunity as PrismaOpportunity, Prisma } from '../../generated/prisma/client.js'
import type { AppPrismaClient } from '../../platform/database/prisma.js'
import { AppError } from '../../platform/errors.js'
import type { OpportunityRepository } from './opportunity.repository.js'
import type { Opportunity, OpportunityListParams, OpportunityListResult } from './opportunity.types.js'

function safeAmount(value: bigint) {
  const amount = Number(value)
  if (!Number.isSafeInteger(amount)) {
    throw new AppError({ code: 'infrastructure', statusCode: 500, message: 'Opportunity amount exceeds safe JSON range' })
  }
  return amount
}

export function mapPrismaOpportunity(row: PrismaOpportunity): Opportunity {
  return {
    id: row.id,
    name: row.name,
    accountName: row.accountName,
    amountMinor: safeAmount(row.amountMinor),
    currency: row.currency,
    expectedCloseDate: row.expectedCloseDate.toISOString().slice(0, 10),
    stage: row.stage,
    version: row.version,
    lossReason: row.lossReason,
    createdAt: row.createdAt.toISOString(),
    updatedAt: row.updatedAt.toISOString(),
  }
}

export function toOpportunityDate(value: string) {
  const date = new Date(`${value}T00:00:00.000Z`)
  if (Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== value) {
    throw new AppError({ code: 'validation', statusCode: 400, message: 'Invalid expected close date' })
  }
  return date
}

export class PrismaOpportunityRepository implements OpportunityRepository {
  constructor(private readonly prisma: AppPrismaClient) {}

  async list(params: OpportunityListParams): Promise<OpportunityListResult> {
    const page = params.page ?? 1
    const pageSize = params.pageSize ?? 25
    const where: Prisma.OpportunityWhereInput = {
      ...(params.search
        ? {
            OR: [
              { name: { contains: params.search, mode: 'insensitive' } },
              { accountName: { contains: params.search, mode: 'insensitive' } },
            ],
          }
        : {}),
      ...(params.stage ? { stage: params.stage } : {}),
    }
    const direction = params.direction ?? 'desc'
    const orderBy: Prisma.OpportunityOrderByWithRelationInput = (() => {
      switch (params.sort) {
        case 'name': return { name: direction }
        case 'accountName': return { accountName: direction }
        case 'amountMinor': return { amountMinor: direction }
        case 'expectedCloseDate': return { expectedCloseDate: direction }
        case 'stage': return { stage: direction }
        default: return { updatedAt: direction }
      }
    })()

    const [rows, total] = await Promise.all([
      this.prisma.opportunity.findMany({
        where,
        orderBy,
        skip: (page - 1) * pageSize,
        take: pageSize,
      }),
      this.prisma.opportunity.count({ where }),
    ])
    return { data: rows.map(mapPrismaOpportunity), total }
  }

  async get(id: string): Promise<Opportunity> {
    const row = await this.prisma.opportunity.findUnique({ where: { id } })
    if (!row) {
      throw new AppError({ code: 'not_found', statusCode: 404, message: 'Opportunity not found' })
    }
    return mapPrismaOpportunity(row)
  }
}
