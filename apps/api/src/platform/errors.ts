import type { ApiErrorCode, ApiErrorEnvelope } from '@cpxlabs-admin/contracts'
import type { FastifyError, FastifyInstance } from 'fastify'

export class AppError extends Error {
  readonly code: ApiErrorCode
  readonly statusCode: number
  readonly details: unknown

  constructor(options: {
    code: ApiErrorCode
    statusCode: number
    message: string
    details?: unknown
  }) {
    super(options.message)
    this.name = 'AppError'
    this.code = options.code
    this.statusCode = options.statusCode
    this.details = options.details
  }
}

export function installErrorHandler(app: FastifyInstance) {
  app.setErrorHandler((error: FastifyError, request, reply) => {
    if (error.validation) {
      const body: ApiErrorEnvelope = {
        error: {
          code: 'validation',
          message: 'Request validation failed',
          details: error.validation,
          requestId: request.id,
        },
      }
      return reply.status(400).send(body)
    }

    if (error instanceof AppError) {
      const body: ApiErrorEnvelope = {
        error: {
          code: error.code,
          message: error.message,
          ...(error.details !== undefined ? { details: error.details } : {}),
          requestId: request.id,
        },
      }
      return reply.status(error.statusCode).send(body)
    }

    request.log.error({ err: error }, 'Unhandled request error')
    const body: ApiErrorEnvelope = {
      error: {
        code: 'infrastructure',
        message: 'Internal server error',
        requestId: request.id,
      },
    }
    return reply.status(500).send(body)
  })
}
