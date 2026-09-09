import type { FastifyRequest } from 'fastify'

export type SecurityEvent =
  | 'authentication.failed'
  | 'authentication.required'
  | 'access.disabled'
  | 'authorization.forbidden'

export function emitSecurityEvent(
  request: FastifyRequest,
  event: SecurityEvent,
  metadata: Record<string, string | number | boolean | undefined> = {},
) {
  request.log.warn(
    {
      securityEvent: event,
      requestId: request.id,
      method: request.method,
      path: request.url.split('?')[0],
      ...metadata,
    },
    'Security event',
  )
}
