import type { Customer as PrismaCustomer, Prisma } from '../../generated/prisma/client.js'
import { AppError } from '../../platform/errors.js'
import type { AppPrismaClient } from '../../platform/database/prisma.js'
import type {
  Customer,
  CustomerInput,
  CustomerListParams,
} from './customer.types.js'
import type { CustomerListResult, CustomerRepository } from './customer.repository.js'

function mapCustomer(customer: PrismaCustomer): Customer {
  return {
    id: customer.id,
    name: customer.name,
    email: customer.email,
    company: customer.company,
    status: customer.status,
    updatedAt: customer.updatedAt.toISOString(),
  }
}

function buildWhere(params: CustomerListParams): Prisma.CustomerWhereInput {
  const search = params.search?.trim()

  return {
    ...(search
      ? {
          OR: [
            { name: { contains: search, mode: 'insensitive' } },
            { email: { contains: search, mode: 'insensitive' } },
            { company: { contains: search, mode: 'insensitive' } },
          ],
        }
      : {}),
    ...(params.status ? { status: params.status } : {}),
  }
}

function buildOrderBy(params: CustomerListParams): Prisma.CustomerOrderByWithRelationInput {
  const direction = params.direction ?? 'asc'

  switch (params.sort) {
    case 'name':
      return { name: direction }
    case 'company':
      return { company: direction }
    case 'status':
      return { status: direction }
    case 'updatedAt':
      return { updatedAt: direction }
    default:
      return { updatedAt: 'desc' }
  }
}

function persistenceErrorCode(error: unknown): string | undefined {
  if (typeof error !== 'object' || error === null || !('code' in error)) {
    return undefined
  }

  return typeof error.code === 'string' ? error.code : undefined
}

function mapPersistenceError(error: unknown): never {
  switch (persistenceErrorCode(error)) {
    case 'P2002':
      throw new AppError({
        code: 'conflict',
        statusCode: 409,
        message: 'Customer email already exists',
      })
    case 'P2025':
      throw new AppError({ code: 'not_found', statusCode: 404, message: 'Customer not found' })
    default:
      throw error
  }
}

export class PrismaCustomerRepository implements CustomerRepository {
  constructor(private readonly prisma: AppPrismaClient) {}

  async list(params: CustomerListParams): Promise<CustomerListResult> {
    const where = buildWhere(params)
    const offset = (params.page - 1) * params.pageSize

    const [rows, total] = await Promise.all([
      this.prisma.customer.findMany({
        where,
        orderBy: buildOrderBy(params),
        skip: offset,
        take: params.pageSize,
      }),
      this.prisma.customer.count({ where }),
    ])

    return { data: rows.map(mapCustomer), total }
  }

  async get(id: string): Promise<Customer> {
    const customer = await this.prisma.customer.findUnique({ where: { id } })

    if (!customer) {
      throw new AppError({ code: 'not_found', statusCode: 404, message: 'Customer not found' })
    }

    return mapCustomer(customer)
  }

  async create(input: CustomerInput): Promise<Customer> {
    try {
      return mapCustomer(await this.prisma.customer.create({ data: input }))
    } catch (error) {
      return mapPersistenceError(error)
    }
  }

  async update(id: string, input: CustomerInput): Promise<Customer> {
    try {
      return mapCustomer(
        await this.prisma.customer.update({
          where: { id },
          data: input,
        }),
      )
    } catch (error) {
      return mapPersistenceError(error)
    }
  }

  async delete(id: string): Promise<void> {
    try {
      await this.prisma.customer.delete({ where: { id } })
    } catch (error) {
      mapPersistenceError(error)
    }
  }
}
