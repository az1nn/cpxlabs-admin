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
  actor: {
    id: string
    email: string
    name: string
  }
  action: AuditAction
  subject: {
    type: AuditSubjectType
    id: string
  }
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
  nextCursor: string | null
}
