import type { FastifyRequest } from 'fastify'

export type SecurityEvent =
  | 'authentication.failed'
  | 'authentication.required'
  | 'access.disabled'
  | 'authorization.forbidden'

const sensitiveMetadataKey = /authorization|cookie|password|secret|token/i

function sanitizeMetadata(
  metadata: Record<string, string | number | boolean | undefined>,
) {
  return Object.fromEntries(
    Object.entries(metadata).filter(([key]) => !sensitiveMetadataKey.test(key)),
  )
}

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
      ...sanitizeMetadata(metadata),
    },
    'Security event',
  )
}
