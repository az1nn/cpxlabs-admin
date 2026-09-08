import Fastify from 'fastify'

import { InMemoryCustomerRepository, type CustomerRepository } from './modules/customers/customer.repository.js'
import { customerRoutes } from './modules/customers/customer.routes.js'
import type { AppAuth } from './platform/authentication/auth.js'
import { registerAuthenticationRoutes } from './platform/authentication/fastify-auth.js'
import { registerApplicationSessionRoute, type RequestContextResolver } from './platform/authentication/session.js'
import type { AuthorizationGuards } from './platform/authorization/guards.js'
import { createUnauthenticatedGuards } from './platform/authorization/guards.js'
import { installErrorHandler } from './platform/errors.js'

export type BuildAppOptions = {
  customerRepository?: CustomerRepository
  authorization?: AuthorizationGuards
  authentication?: {
    auth: AppAuth
    resolveRequestContext: RequestContextResolver
  }
}

export function buildApp(options: BuildAppOptions = {}) {
  const app = Fastify({
    logger: process.env.NODE_ENV !== 'test',
  })

  installErrorHandler(app)

  app.get('/health', async () => ({ status: 'ok' }))

  if (options.authentication) {
    void registerAuthenticationRoutes(app, options.authentication.auth)
    void registerApplicationSessionRoute(
      app,
      options.authentication.resolveRequestContext,
    )
  }

  app.register(customerRoutes, {
    repository: options.customerRepository ?? new InMemoryCustomerRepository(),
    authorization: options.authorization ?? createUnauthenticatedGuards(),
  })

  return app
}
