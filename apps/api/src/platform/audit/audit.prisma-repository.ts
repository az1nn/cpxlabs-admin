import type {
  AuditEventDto,
  AuditEventListQuery,
  AuditEventListResponse,
  AuditSnapshot,
} from '@cpxlabs-admin/contracts'

import type { AuditEvent as PrismaAuditEvent, Prisma } from '../../generated/prisma/client.js'
import type { AppPrismaClient } from '../database/prisma.js'
import { AppError } from '../errors.js'
import type { AuditEventInput, AuditRepository } from './audit.repository.js'

type CursorPosition = { occurredAt: string; id: string }

function encodeCursor(event: PrismaAuditEvent) {
  return Buffer.from(
    JSON.stringify({ occurredAt: event.occurredAt.toISOString(), id: event.id } satisfies CursorPosition),
  ).toString('base64url')
}

function decodeCursor(cursor: string | undefined): CursorPosition | null {
  if (!cursor) return null
  try {
    const value = JSON.parse(Buffer.from(cursor, 'base64url').toString('utf8')) as Partial<CursorPosition>
    if (typeof value.occurredAt !== 'string' || typeof value.id !== 'string') return null
    if (Number.isNaN(Date.parse(value.occurredAt))) return null
    return { occurredAt: value.occurredAt, id: value.id }
  } catch {
    return null
  }
}

function toSnapshot(value: Prisma.JsonValue | null): AuditSnapshot | null {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) return null
  return value as unknown as AuditSnapshot
}

function mapAuditEvent(event: PrismaAuditEvent): AuditEventDto {
  return {
    id: event.id,
    actor: {
      id: event.actorId,
      email: event.actorEmail,
      name: event.actorName,
    },
    action: event.action as AuditEventDto['action'],
    subject: {
      type: event.subjectType as AuditEventDto['subject']['type'],
      id: event.subjectId,
    },
    before: toSnapshot(event.before),
    after: toSnapshot(event.after),
    correlationId: event.correlationId,
    tenantId: event.tenantId,
    occurredAt: event.occurredAt.toISOString(),
  }
}

export function auditCreateData(input: AuditEventInput): Prisma.AuditEventCreateInput {
  return {
    actorId: input.actorId,
    actorEmail: input.actorEmail,
    actorName: input.actorName,
    action: input.action,
    subjectType: input.subjectType,
    subjectId: input.subjectId,
    correlationId: input.correlationId,
    tenantId: input.tenantId,
    ...(input.before === null
      ? {}
      : { before: input.before as unknown as Prisma.InputJsonValue }),
    ...(input.after === null
      ? {}
      : { after: input.after as unknown as Prisma.InputJsonValue }),
  }
}

export class PrismaAuditRepository implements AuditRepository {
  constructor(private readonly prisma: AppPrismaClient) {}

  async append(input: AuditEventInput): Promise<AuditEventDto> {
    try {
      return mapAuditEvent(await this.prisma.auditEvent.create({ data: auditCreateData(input) }))
    } catch {
      throw new AppError({
        code: 'infrastructure',
        statusCode: 500,
        message: 'Audit event could not be persisted',
      })
    }
  }

  async list(query: AuditEventListQuery): Promise<AuditEventListResponse> {
    const limit = Math.min(Math.max(query.limit ?? 50, 1), 100)
    const cursor = decodeCursor(query.cursor)
    if (query.cursor && !cursor) {
      throw new AppError({ code: 'validation', statusCode: 400, message: 'Invalid audit cursor' })
    }

    const where: Prisma.AuditEventWhereInput = {
      ...(query.actorId ? { actorId: query.actorId } : {}),
      ...(query.action ? { action: query.action } : {}),
      ...(query.subjectType ? { subjectType: query.subjectType } : {}),
      ...(query.subjectId ? { subjectId: query.subjectId } : {}),
      ...(cursor
        ? {
            OR: [
              { occurredAt: { lt: new Date(cursor.occurredAt) } },
              {
                occurredAt: new Date(cursor.occurredAt),
                id: { lt: cursor.id },
              },
            ],
          }
        : {}),
    }

    const rows = await this.prisma.auditEvent.findMany({
      where,
      orderBy: [{ occurredAt: 'desc' }, { id: 'desc' }],
      take: limit + 1,
    })
    const hasMore = rows.length > limit
    const visible = hasMore ? rows.slice(0, limit) : rows
    return {
      data: visible.map(mapAuditEvent),
      nextCursor:
        hasMore && visible.length > 0
          ? encodeCursor(visible[visible.length - 1]!)
          : null,
    }
  }
}
