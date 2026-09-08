import Fastify from 'fastify'

import { customerRoutes } from './modules/customers/customer.routes.js'
import { installErrorHandler } from './platform/errors.js'

export function buildApp() {
  const app = Fastify({
    logger: process.env.NODE_ENV !== 'test',
  })

  installErrorHandler(app)

  app.get('/health', async () => ({ status: 'ok' }))
  app.register(customerRoutes)

  return app
}
