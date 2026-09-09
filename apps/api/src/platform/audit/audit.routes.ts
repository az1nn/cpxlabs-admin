import type { AuditAction, AuditEventListQuery, AuditSubjectType } from '@cpxlabs-admin/contracts'
import type { FastifyInstance } from 'fastify'

import type { AuthorizationGuards } from '../authorization/guards.js'
import type { AuditRepository } from './audit.repository.js'

type AuditQuery = {
  limit?: number
  cursor?: string
  subjectType?: AuditSubjectType
  subjectId?: string
  actorId?: string
  action?: AuditAction
}

const auditQuerySchema = {
  type: 'object',
  additionalProperties: false,
  properties: {
    limit: { type: 'integer', minimum: 1, maximum: 100, default: 50 },
    cursor: { type: 'string', minLength: 1 },
    subjectType: { type: 'string', enum: ['customer'] },
    subjectId: { type: 'string', minLength: 1 },
    actorId: { type: 'string', minLength: 1 },
    action: {
      type: 'string',
      enum: ['customers.create', 'customers.update', 'customers.delete'],
    },
  },
} as const

export type AuditRoutesOptions = {
  repository: AuditRepository
  authorization: AuthorizationGuards
}

export async function auditRoutes(app: FastifyInstance, options: AuditRoutesOptions) {
  app.get<{ Querystring: AuditQuery }>('/api/audit-events', {
    schema: { querystring: auditQuerySchema },
  }, async (request) => {
    await options.authorization.requireCapability(request, 'audit.read')
    const query = request.query
    const repositoryQuery: AuditEventListQuery = {
      ...(query.limit !== undefined ? { limit: query.limit } : {}),
      ...(query.cursor !== undefined ? { cursor: query.cursor } : {}),
      ...(query.subjectType !== undefined ? { subjectType: query.subjectType } : {}),
      ...(query.subjectId !== undefined ? { subjectId: query.subjectId } : {}),
      ...(query.actorId !== undefined ? { actorId: query.actorId } : {}),
      ...(query.action !== undefined ? { action: query.action } : {}),
    }
    return options.repository.list(repositoryQuery)
  })
}
