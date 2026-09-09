import { randomUUID } from 'node:crypto'

import { AppError } from '../../platform/errors.js'
import type {
  Opportunity,
  OpportunityInput,
  OpportunityListParams,
  OpportunityListResult,
} from './opportunity.types.js'

export interface OpportunityRepository {
  list(params: OpportunityListParams): Promise<OpportunityListResult>
  get(id: string): Promise<Opportunity>
}

export class InMemoryOpportunityRepository implements OpportunityRepository {
  private opportunities: Opportunity[]

  constructor(seed: Opportunity[] = []) {
    this.opportunities = seed.length > 0 ? [...seed] : [
      {
        id: 'opp_001',
        name: 'Enterprise Renewal',
        accountName: 'Acme Brasil',
        amountMinor: 12_500_000,
        currency: 'BRL',
        expectedCloseDate: '2026-11-30',
        stage: 'qualification',
        version: 1,
        lossReason: null,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ]
  }

  async list(params: OpportunityListParams): Promise<OpportunityListResult> {
    const page = params.page ?? 1
    const pageSize = params.pageSize ?? 25
    const search = params.search?.trim().toLowerCase()
    let rows = this.opportunities.filter((item) =>
      (!search || item.name.toLowerCase().includes(search) || item.accountName.toLowerCase().includes(search)) &&
      (!params.stage || item.stage === params.stage),
    )
    const sort = params.sort ?? 'updatedAt'
    const direction = params.direction ?? 'desc'
    rows = [...rows].sort((left, right) => {
      const a = left[sort]
      const b = right[sort]
      const comparison = a < b ? -1 : a > b ? 1 : 0
      return direction === 'asc' ? comparison : -comparison
    })
    return {
      data: rows.slice((page - 1) * pageSize, page * pageSize),
      total: rows.length,
    }
  }

  async get(id: string): Promise<Opportunity> {
    const opportunity = this.opportunities.find((item) => item.id === id)
    if (!opportunity) {
      throw new AppError({ code: 'not_found', statusCode: 404, message: 'Opportunity not found' })
    }
    return opportunity
  }

  createForWorkflow(input: OpportunityInput): Opportunity {
    const now = new Date().toISOString()
    const opportunity: Opportunity = {
      id: randomUUID(),
      ...input,
      stage: 'qualification',
      version: 1,
      lossReason: null,
      createdAt: now,
      updatedAt: now,
    }
    this.opportunities = [opportunity, ...this.opportunities]
    return opportunity
  }

  replaceForWorkflow(opportunity: Opportunity) {
    const index = this.opportunities.findIndex((item) => item.id === opportunity.id)
    if (index < 0) {
      throw new AppError({ code: 'not_found', statusCode: 404, message: 'Opportunity not found' })
    }
    this.opportunities[index] = opportunity
  }

  deleteForWorkflow(id: string) {
    this.opportunities = this.opportunities.filter((item) => item.id !== id)
  }
}
