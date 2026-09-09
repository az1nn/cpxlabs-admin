import { randomUUID } from 'node:crypto'

import type { FastifyInstance } from 'fastify'

export function createRequestId() {
  return randomUUID()
}

export function installCorrelation(app: FastifyInstance) {
  app.addHook('onRequest', async (request, reply) => {
    reply.header('x-request-id', request.id)
  })
}
