export type AuditAction =
  | 'customers.create'
  | 'customers.update'
  | 'customers.delete'

export type AuditSubjectType = 'customer'

export type CustomerAuditSnapshot = {
  id: string
  name: string
  email: string
  company: string
  status: 'lead' | 'active' | 'inactive'
  updatedAt: string
}

export type AuditEventDto = {
  id: string
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
  occurredAt: string
}

export type AuditEventListQuery = {
  actorId?: string
  action?: AuditAction
  subjectType?: AuditSubjectType
  subjectId?: string
  limit?: number
  cursor?: string
}

export type AuditEventListResponse = {
  data: AuditEventDto[]
  nextCursor?: string
}
