import Fastify from 'fastify'

import { InMemoryCustomerRepository, type CustomerRepository } from './modules/customers/customer.repository.js'
import { customerRoutes } from './modules/customers/customer.routes.js'
import { installErrorHandler } from './platform/errors.js'

export type BuildAppOptions = {
  customerRepository?: CustomerRepository
}

export function buildApp(options: BuildAppOptions = {}) {
  const app = Fastify({
    logger: process.env.NODE_ENV !== 'test',
  })

  installErrorHandler(app)

  app.get('/health', async () => ({ status: 'ok' }))
  app.register(customerRoutes, {
    repository: options.customerRepository ?? new InMemoryCustomerRepository(),
  })

  return app
}
