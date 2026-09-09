import type { Principal } from '@cpxlabs-admin/authorization'
import type { Prisma } from '../../generated/prisma/client.js'
import type { AuditRepository } from '../../platform/audit/audit.repository.js'
import { auditCreateData } from '../../platform/audit/audit.prisma-repository.js'
import type { AppPrismaClient } from '../../platform/database/prisma.js'
import { AppError } from '../../platform/errors.js'
import { normalizeOpportunityCreateInput, opportunityAuditInput } from './opportunity.audit.js'
import { mapPrismaOpportunity, toOpportunityDate } from './opportunity.prisma-repository.js'
import { InMemoryOpportunityRepository } from './opportunity.repository.js'
import type {
  Opportunity,
  OpportunityInput,
  OpportunityTransitionCommand,
} from './opportunity.types.js'
import { normalizeOpportunityTransition, OpportunityTransitionError } from './opportunity.workflow.js'

export type OpportunityCommandContext = {
  principal: Principal
  requestId: string
  tenantId?: string
}

export interface OpportunityWorkflowService {
  create(input: OpportunityInput, context: OpportunityCommandContext): Promise<Opportunity>
  transition(
    id: string,
    command: OpportunityTransitionCommand,
    context: OpportunityCommandContext,
  ): Promise<Opportunity>
}

function invalidTransition(error: OpportunityTransitionError): AppError {
  return new AppError({
    code: 'WORKFLOW_INVALID_TRANSITION',
    statusCode: 409,
    message: error.message || 'The requested opportunity transition is not allowed',
  })
}

function workflowConflict(expectedVersion: number, currentVersion: number): AppError {
  return new AppError({
    code: 'WORKFLOW_CONFLICT',
    statusCode: 409,
    message: 'The opportunity changed since it was loaded',
    details: { expectedVersion, currentVersion },
  })
}

export class InMemoryOpportunityWorkflowService implements OpportunityWorkflowService {
  constructor(
    private readonly opportunities: InMemoryOpportunityRepository,
    private readonly audit: AuditRepository,
  ) {}

  async create(input: OpportunityInput, context: OpportunityCommandContext) {
    const opportunity = this.opportunities.createForWorkflow(normalizeOpportunityCreateInput(input))
    try {
      await this.audit.append(
        opportunityAuditInput(
          'opportunities.create',
          opportunity.id,
          context.principal,
          context.requestId,
          context.tenantId,
          null,
          opportunity,
        ),
      )
      return opportunity
    } catch (error) {
      throw error
    }
  }

  async transition(
    id: string,
    command: OpportunityTransitionCommand,
    context: OpportunityCommandContext,
  ) {
    const before = await this.opportunities.get(id)
    if (before.version !== command.expectedVersion) {
      throw workflowConflict(command.expectedVersion, before.version)
    }

    let next: { stage: Opportunity['stage']; lossReason: string | null }
    try {
      next = normalizeOpportunityTransition(before.stage, command.targetStage, command.lossReason)
    } catch (error) {
      if (error instanceof OpportunityTransitionError) throw invalidTransition(error)
      throw error
    }

    const after: Opportunity = {
      ...before,
      stage: next.stage,
      lossReason: next.lossReason,
      version: before.version + 1,
      updatedAt: new Date().toISOString(),
    }
    this.opportunities.replaceForWorkflow(after)
    try {
      await this.audit.append(
        opportunityAuditInput(
          'opportunities.stage.change',
          id,
          context.principal,
          context.requestId,
          context.tenantId,
          before,
          after,
        ),
      )
      return after
    } catch (error) {
      this.opportunities.replaceForWorkflow(before)
      throw error
    }
  }
}

export type OpportunityAuditTransactionWriter = (
  transaction: Prisma.TransactionClient,
  input: ReturnType<typeof opportunityAuditInput>,
) => Promise<void>

const defaultAuditWriter: OpportunityAuditTransactionWriter = async (transaction, input) => {
  await transaction.auditEvent.create({ data: auditCreateData(input) })
}

function mapWorkflowPersistenceError(error: unknown): never {
  if (error instanceof AppError) throw error
  throw new AppError({
    code: 'infrastructure',
    statusCode: 500,
    message: 'Opportunity workflow command could not be committed',
  })
}

export class PrismaOpportunityWorkflowService implements OpportunityWorkflowService {
  constructor(
    private readonly prisma: AppPrismaClient,
    private readonly writeAudit: OpportunityAuditTransactionWriter = defaultAuditWriter,
  ) {}

  async create(input: OpportunityInput, context: OpportunityCommandContext): Promise<Opportunity> {
    const normalized = normalizeOpportunityCreateInput(input)
    try {
      return await this.prisma.$transaction(async (transaction) => {
        const created = mapPrismaOpportunity(
          await transaction.opportunity.create({
            data: {
              name: normalized.name,
              accountName: normalized.accountName,
              amountMinor: BigInt(normalized.amountMinor),
              currency: normalized.currency,
              expectedCloseDate: toOpportunityDate(normalized.expectedCloseDate),
              stage: 'qualification',
              version: 1,
              lossReason: null,
            },
          }),
        )
        await this.writeAudit(
          transaction,
          opportunityAuditInput(
            'opportunities.create',
            created.id,
            context.principal,
            context.requestId,
            context.tenantId,
            null,
            created,
          ),
        )
        return created
      })
    } catch (error) {
      return mapWorkflowPersistenceError(error)
    }
  }

  async transition(
    id: string,
    command: OpportunityTransitionCommand,
    context: OpportunityCommandContext,
  ): Promise<Opportunity> {
    try {
      return await this.prisma.$transaction(async (transaction) => {
        const currentRow = await transaction.opportunity.findUnique({ where: { id } })
        if (!currentRow) {
          throw new AppError({ code: 'not_found', statusCode: 404, message: 'Opportunity not found' })
        }
        const before = mapPrismaOpportunity(currentRow)
        if (before.version !== command.expectedVersion) {
          throw workflowConflict(command.expectedVersion, before.version)
        }

        let next: { stage: Opportunity['stage']; lossReason: string | null }
        try {
          next = normalizeOpportunityTransition(before.stage, command.targetStage, command.lossReason)
        } catch (error) {
          if (error instanceof OpportunityTransitionError) throw invalidTransition(error)
          throw error
        }

        const updated = await transaction.opportunity.updateMany({
          where: { id, version: command.expectedVersion },
          data: {
            stage: next.stage,
            lossReason: next.lossReason,
            version: { increment: 1 },
          },
        })

        if (updated.count !== 1) {
          const fresh = await transaction.opportunity.findUnique({ where: { id } })
          if (!fresh) {
            throw new AppError({ code: 'not_found', statusCode: 404, message: 'Opportunity not found' })
          }
          throw workflowConflict(command.expectedVersion, fresh.version)
        }

        const afterRow = await transaction.opportunity.findUnique({ where: { id } })
        if (!afterRow) {
          throw new AppError({ code: 'infrastructure', statusCode: 500, message: 'Opportunity transition result was not found' })
        }
        const after = mapPrismaOpportunity(afterRow)
        await this.writeAudit(
          transaction,
          opportunityAuditInput(
            'opportunities.stage.change',
            id,
            context.principal,
            context.requestId,
            context.tenantId,
            before,
            after,
          ),
        )
        return after
      })
    } catch (error) {
      return mapWorkflowPersistenceError(error)
    }
  }
}
