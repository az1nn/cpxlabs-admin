import { randomUUID } from 'node:crypto'

import type {
  AuditAction,
  AuditEventDto,
  AuditEventListQuery,
  AuditEventListResponse,
  AuditSnapshot,
  AuditSubjectType,
} from '@cpxlabs-admin/contracts'

export type AuditEventInput = {
  actorId: string
  actorEmail: string
  actorName: string
  action: AuditAction
  subjectType: AuditSubjectType
  subjectId: string
  before: AuditSnapshot | null
  after: AuditSnapshot | null
  correlationId: string
  tenantId: string | null
}

export interface AuditRepository {
  append(input: AuditEventInput): Promise<AuditEventDto>
  list(query: AuditEventListQuery): Promise<AuditEventListResponse>
}

function matches(event: AuditEventDto, query: AuditEventListQuery) {
  return (
    (query.actorId === undefined || event.actor.id === query.actorId) &&
    (query.action === undefined || event.action === query.action) &&
    (query.subjectType === undefined || event.subject.type === query.subjectType) &&
    (query.subjectId === undefined || event.subject.id === query.subjectId)
  )
}

export class InMemoryAuditRepository implements AuditRepository {
  private events: AuditEventDto[] = []

  async append(input: AuditEventInput): Promise<AuditEventDto> {
    const event: AuditEventDto = {
      id: randomUUID(),
      actor: {
        id: input.actorId,
        email: input.actorEmail,
        name: input.actorName,
      },
      action: input.action,
      subject: {
        type: input.subjectType,
        id: input.subjectId,
      },
      before: input.before,
      after: input.after,
      correlationId: input.correlationId,
      tenantId: input.tenantId,
      occurredAt: new Date().toISOString(),
    }
    this.events = [event, ...this.events]
    return event
  }

  async list(query: AuditEventListQuery): Promise<AuditEventListResponse> {
    const limit = Math.min(Math.max(query.limit ?? 50, 1), 100)
    const filtered = this.events.filter((event) => matches(event, query))
    const cursorIndex = query.cursor
      ? filtered.findIndex((event) => event.id === query.cursor)
      : -1
    const start = query.cursor ? Math.max(cursorIndex + 1, 0) : 0
    const data = filtered.slice(start, start + limit)
    const hasMore = start + limit < filtered.length
    return {
      data,
      nextCursor: hasMore && data.length > 0 ? data[data.length - 1]!.id : null,
    }
  }
}
