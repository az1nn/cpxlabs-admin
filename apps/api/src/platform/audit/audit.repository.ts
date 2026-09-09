import { randomUUID } from 'node:crypto'

import type {
  AuditAction,
  AuditEventDto,
  AuditEventListQuery,
  AuditEventListResponse,
  AuditSubjectType,
  CustomerAuditSnapshot,
} from '@cpxlabs-admin/contracts'

export type AuditEventInput = {
  actorId: string
  actorEmail: string
  actorName: string
  action: AuditAction
  subjectType: AuditSubjectType
  subjectId: string
  before: CustomerAuditSnapshot | null
  after: CustomerAuditSnapshot | null
  correlationId: string
  tenantId: string | null
}

export interface AuditRepository {
  append(input: AuditEventInput): Promise<AuditEventDto>
  list(query: AuditEventListQuery): Promise<AuditEventListResponse>
}

function matches(event: AuditEventDto, query: AuditEventListQuery) {
  return (
    (query.actorId === undefined || event.actorId === query.actorId) &&
    (query.action === undefined || event.action === query.action) &&
    (query.subjectType === undefined || event.subjectType === query.subjectType) &&
    (query.subjectId === undefined || event.subjectId === query.subjectId)
  )
}

export class InMemoryAuditRepository implements AuditRepository {
  private events: AuditEventDto[] = []

  async append(input: AuditEventInput): Promise<AuditEventDto> {
    const event: AuditEventDto = {
      id: randomUUID(),
      ...input,
      occurredAt: new Date().toISOString(),
    }
    this.events = [event, ...this.events]
    return event
  }

  async list(query: AuditEventListQuery): Promise<AuditEventListResponse> {
    const limit = Math.min(Math.max(query.limit ?? 50, 1), 100)
    const filtered = this.events.filter((event) => matches(event, query))
    const start = query.cursor
      ? Math.max(filtered.findIndex((event) => event.id === query.cursor) + 1, 0)
      : 0
    const data = filtered.slice(start, start + limit)
    const hasMore = start + limit < filtered.length
    return {
      data,
      ...(hasMore && data.length > 0 ? { nextCursor: data[data.length - 1]!.id } : {}),
    }
  }
}
