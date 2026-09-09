import type { FastifyInstance } from 'fastify'

import type { AuthorizationGuards } from '../../platform/authorization/guards.js'
import type { CustomerMutationContext, CustomerMutationService } from './customer.mutation-service.js'
import type { CustomerRepository } from './customer.repository.js'
import {
  customerInputSchema,
  customerListQuerySchema,
  customerListResponseSchema,
  customerParamsSchema,
  customerSchema,
} from './customer.schemas.js'
import type { CustomerInput, CustomerListParams, CustomerStatus } from './customer.types.js'

type CustomerParams = { customerId: string }
type CustomerListQuery = {
  page: number
  pageSize: number
  search?: string
  sort?: CustomerListParams['sort']
  direction?: CustomerListParams['direction']
  'filter.status'?: CustomerStatus
}

export type CustomerRoutesOptions = {
  repository: CustomerRepository
  mutationService: CustomerMutationService
  authorization: AuthorizationGuards
}

function mutationContext(
  requestId: string,
  principal: CustomerMutationContext['principal'],
  tenant: string | undefined,
): CustomerMutationContext {
  return {
    principal,
    requestId,
    ...(tenant !== undefined ? { tenantId: tenant } : {}),
  }
}

export async function customerRoutes(app: FastifyInstance, options: CustomerRoutesOptions) {
  const { repository, mutationService, authorization } = options

  app.get<{ Querystring: CustomerListQuery }>('/api/customers', {
    schema: {
      querystring: customerListQuerySchema,
      response: { 200: customerListResponseSchema },
    },
  }, async (request) => {
    await authorization.requireCapability(request, 'customers.read')
    const query = request.query
    return repository.list({
      page: query.page,
      pageSize: query.pageSize,
      ...(query.search !== undefined ? { search: query.search } : {}),
      ...(query.sort !== undefined ? { sort: query.sort } : {}),
      ...(query.direction !== undefined ? { direction: query.direction } : {}),
      ...(query['filter.status'] !== undefined ? { status: query['filter.status'] } : {}),
    })
  })

  app.get<{ Params: CustomerParams }>('/api/customers/:customerId', {
    schema: {
      params: customerParamsSchema,
      response: { 200: customerSchema },
    },
  }, async (request) => {
    await authorization.requireCapability(request, 'customers.read')
    return repository.get(request.params.customerId)
  })

  app.post<{ Body: CustomerInput }>('/api/customers', {
    schema: {
      body: customerInputSchema,
      response: { 201: customerSchema },
    },
  }, async (request, reply) => {
    const context = await authorization.requireCapability(request, 'customers.create')
    const customer = await mutationService.create(
      request.body,
      mutationContext(request.id, context.principal, context.tenant),
    )
    return reply.status(201).send(customer)
  })

  app.patch<{ Params: CustomerParams; Body: CustomerInput }>('/api/customers/:customerId', {
    schema: {
      params: customerParamsSchema,
      body: customerInputSchema,
      response: { 200: customerSchema },
    },
  }, async (request) => {
    const context = await authorization.requireCapability(request, 'customers.update')
    return mutationService.update(
      request.params.customerId,
      request.body,
      mutationContext(request.id, context.principal, context.tenant),
    )
  })

  app.delete<{ Params: CustomerParams }>('/api/customers/:customerId', {
    schema: { params: customerParamsSchema },
  }, async (request, reply) => {
    const context = await authorization.requireCapability(request, 'customers.delete')
    await mutationService.delete(
      request.params.customerId,
      mutationContext(request.id, context.principal, context.tenant),
    )
    return reply.status(204).send()
  })
}
