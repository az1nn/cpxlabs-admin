import type { Principal } from '@cpxlabs-admin/authorization'
import type { AuditAction } from '@cpxlabs-admin/contracts'

import type { Customer as PrismaCustomer, Prisma } from '../../generated/prisma/client.js'
import type { AuditEventInput, AuditRepository } from '../../platform/audit/audit.repository.js'
import { auditCreateData } from '../../platform/audit/audit.prisma-repository.js'
import type { AppPrismaClient } from '../../platform/database/prisma.js'
import { AppError } from '../../platform/errors.js'
import { toCustomerAuditSnapshot } from './customer.audit.js'
import type { CustomerRepository } from './customer.repository.js'
import type { Customer, CustomerInput } from './customer.types.js'

export type CustomerMutationContext = {
  principal: Principal
  requestId: string
  tenantId?: string
}

export interface CustomerMutationService {
  create(input: CustomerInput, context: CustomerMutationContext): Promise<Customer>
  update(id: string, input: CustomerInput, context: CustomerMutationContext): Promise<Customer>
  delete(id: string, context: CustomerMutationContext): Promise<void>
}

function auditInput(
  action: AuditAction,
  subjectId: string,
  context: CustomerMutationContext,
  before: Customer | null,
  after: Customer | null,
): AuditEventInput {
  return {
    actorId: context.principal.id,
    actorEmail: context.principal.email,
    actorName: context.principal.name,
    action,
    subjectType: 'customer',
    subjectId,
    before: before ? toCustomerAuditSnapshot(before) : null,
    after: after ? toCustomerAuditSnapshot(after) : null,
    correlationId: context.requestId,
    tenantId: context.tenantId ?? null,
  }
}

function toInput(customer: Customer): CustomerInput {
  return {
    name: customer.name,
    email: customer.email,
    company: customer.company,
    status: customer.status,
  }
}

export class InMemoryCustomerMutationService implements CustomerMutationService {
  constructor(
    private readonly customers: CustomerRepository,
    private readonly audit: AuditRepository,
  ) {}

  async create(input: CustomerInput, context: CustomerMutationContext) {
    const customer = await this.customers.create(input)
    try {
      await this.audit.append(auditInput('customers.create', customer.id, context, null, customer))
      return customer
    } catch (error) {
      await this.customers.delete(customer.id)
      throw error
    }
  }

  async update(id: string, input: CustomerInput, context: CustomerMutationContext) {
    const before = await this.customers.get(id)
    const customer = await this.customers.update(id, input)
    try {
      await this.audit.append(auditInput('customers.update', id, context, before, customer))
      return customer
    } catch (error) {
      await this.customers.update(id, toInput(before))
      throw error
    }
  }

  async delete(id: string, context: CustomerMutationContext) {
    const before = await this.customers.get(id)
    await this.customers.delete(id)
    await this.audit.append(auditInput('customers.delete', id, context, before, null))
  }
}

function mapPrismaCustomer(customer: PrismaCustomer): Customer {
  return {
    id: customer.id,
    name: customer.name,
    email: customer.email,
    company: customer.company,
    status: customer.status,
    updatedAt: customer.updatedAt.toISOString(),
  }
}

function persistenceCode(error: unknown) {
  return typeof error === 'object' && error !== null && 'code' in error && typeof error.code === 'string'
    ? error.code
    : undefined
}

function mapMutationError(error: unknown): never {
  if (error instanceof AppError) throw error
  switch (persistenceCode(error)) {
    case 'P2002':
      throw new AppError({ code: 'conflict', statusCode: 409, message: 'Customer email already exists' })
    case 'P2025':
      throw new AppError({ code: 'not_found', statusCode: 404, message: 'Customer not found' })
    default:
      throw new AppError({
        code: 'infrastructure',
        statusCode: 500,
        message: 'Customer mutation could not be committed',
      })
  }
}

export type AuditTransactionWriter = (
  transaction: Prisma.TransactionClient,
  input: AuditEventInput,
) => Promise<void>

const defaultAuditWriter: AuditTransactionWriter = async (transaction, input) => {
  await transaction.auditEvent.create({ data: auditCreateData(input) })
}

export class PrismaCustomerMutationService implements CustomerMutationService {
  constructor(
    private readonly prisma: AppPrismaClient,
    private readonly writeAudit: AuditTransactionWriter = defaultAuditWriter,
  ) {}

  async create(input: CustomerInput, context: CustomerMutationContext): Promise<Customer> {
    try {
      return await this.prisma.$transaction(async (transaction) => {
        const customer = mapPrismaCustomer(await transaction.customer.create({ data: input }))
        await this.writeAudit(
          transaction,
          auditInput('customers.create', customer.id, context, null, customer),
        )
        return customer
      })
    } catch (error) {
      return mapMutationError(error)
    }
  }

  async update(
    id: string,
    input: CustomerInput,
    context: CustomerMutationContext,
  ): Promise<Customer> {
    try {
      return await this.prisma.$transaction(async (transaction) => {
        const previous = await transaction.customer.findUnique({ where: { id } })
        if (!previous) {
          throw new AppError({ code: 'not_found', statusCode: 404, message: 'Customer not found' })
        }
        const before = mapPrismaCustomer(previous)
        const customer = mapPrismaCustomer(
          await transaction.customer.update({ where: { id }, data: input }),
        )
        await this.writeAudit(
          transaction,
          auditInput('customers.update', id, context, before, customer),
        )
        return customer
      })
    } catch (error) {
      return mapMutationError(error)
    }
  }

  async delete(id: string, context: CustomerMutationContext): Promise<void> {
    try {
      await this.prisma.$transaction(async (transaction) => {
        const previous = await transaction.customer.findUnique({ where: { id } })
        if (!previous) {
          throw new AppError({ code: 'not_found', statusCode: 404, message: 'Customer not found' })
        }
        const before = mapPrismaCustomer(previous)
        await transaction.customer.delete({ where: { id } })
        await this.writeAudit(
          transaction,
          auditInput('customers.delete', id, context, before, null),
        )
      })
    } catch (error) {
      mapMutationError(error)
    }
  }
}
