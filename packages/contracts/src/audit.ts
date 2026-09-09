import type { OpportunityStage } from './opportunity'

export type AuditAction =
  | 'customers.create'
  | 'customers.update'
  | 'customers.delete'
  | 'opportunities.create'
  | 'opportunities.stage.change'

export type AuditSubjectType = 'customer' | 'opportunity'

export type CustomerAuditSnapshot = {
  id: string
  name: string
  email: string
  company: string
  status: 'lead' | 'active' | 'inactive'
  updatedAt: string
}

export type OpportunityAuditSnapshot = {
  id: string
  name: string
  accountName: string
  amountMinor: number
  currency: string
  expectedCloseDate: string
  stage: OpportunityStage
  version: number
  lossReason: string | null
  updatedAt: string
}

export type AuditSnapshot = CustomerAuditSnapshot | OpportunityAuditSnapshot

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
  before: AuditSnapshot | null
  after: AuditSnapshot | null
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
