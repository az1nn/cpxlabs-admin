import type { FastifyInstance } from 'fastify'

import { InMemoryCustomerRepository } from './customer.repository.js'
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

export async function customerRoutes(app: FastifyInstance) {
  const repository = new InMemoryCustomerRepository()

  app.get<{ Querystring: CustomerListQuery }>('/api/customers', {
    schema: {
      querystring: customerListQuerySchema,
      response: { 200: customerListResponseSchema },
    },
  }, async (request) => {
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
  }, async (request) => repository.get(request.params.customerId))

  app.post<{ Body: CustomerInput }>('/api/customers', {
    schema: {
      body: customerInputSchema,
      response: { 201: customerSchema },
    },
  }, async (request, reply) => {
    const customer = repository.create(request.body)
    return reply.status(201).send(customer)
  })

  app.patch<{ Params: CustomerParams; Body: CustomerInput }>('/api/customers/:customerId', {
    schema: {
      params: customerParamsSchema,
      body: customerInputSchema,
      response: { 200: customerSchema },
    },
  }, async (request) => repository.update(request.params.customerId, request.body))

  app.delete<{ Params: CustomerParams }>('/api/customers/:customerId', {
    schema: { params: customerParamsSchema },
  }, async (request, reply) => {
    repository.delete(request.params.customerId)
    return reply.status(204).send()
  })
}
