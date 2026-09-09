import Fastify from 'fastify'

import { InMemoryCustomerMutationService, type CustomerMutationService } from './modules/customers/customer.mutation-service.js'
import { InMemoryCustomerRepository, type CustomerRepository } from './modules/customers/customer.repository.js'
import { customerRoutes } from './modules/customers/customer.routes.js'
import { InMemoryAuditRepository, type AuditRepository } from './platform/audit/audit.repository.js'
import { auditRoutes } from './platform/audit/audit.routes.js'
import type { AppAuth } from './platform/authentication/auth.js'
import { registerAuthenticationRoutes } from './platform/authentication/fastify-auth.js'
import { registerApplicationSessionRoute, type RequestContextResolver } from './platform/authentication/session.js'
import type { AuthorizationGuards } from './platform/authorization/guards.js'
import { createUnauthenticatedGuards } from './platform/authorization/guards.js'
import { installErrorHandler } from './platform/errors.js'
import { createRequestId, installCorrelation } from './platform/observability/correlation.js'

export type BuildAppOptions = {
  customerRepository?: CustomerRepository
  customerMutationService?: CustomerMutationService
  auditRepository?: AuditRepository
  authorization?: AuthorizationGuards
  authentication?: {
    auth: AppAuth
    resolveRequestContext: RequestContextResolver
  }
}

export function buildApp(options: BuildAppOptions = {}) {
  const app = Fastify({
    logger: process.env.NODE_ENV !== 'test',
    genReqId: createRequestId,
  })

  installCorrelation(app)
  installErrorHandler(app)

  app.get('/health', { config: { otel: false } }, async () => ({ status: 'ok' }))

  if (options.authentication) {
    void registerAuthenticationRoutes(app, options.authentication.auth)
    void registerApplicationSessionRoute(
      app,
      options.authentication.resolveRequestContext,
    )
  }

  const customerRepository = options.customerRepository ?? new InMemoryCustomerRepository()
  const auditRepository = options.auditRepository ?? new InMemoryAuditRepository()
  const customerMutationService =
    options.customerMutationService ??
    new InMemoryCustomerMutationService(customerRepository, auditRepository)
  const authorization = options.authorization ?? createUnauthenticatedGuards()

  app.register(customerRoutes, {
    repository: customerRepository,
    mutationService: customerMutationService,
    authorization,
  })
  app.register(auditRoutes, {
    repository: auditRepository,
    authorization,
  })

  return app
}
