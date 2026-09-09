import type { OpportunityAuditSnapshot } from '@cpxlabs-admin/contracts'

import type { AuditEventInput } from '../../platform/audit/audit.repository.js'
import type { Opportunity, OpportunityInput } from './opportunity.types.js'

export function toOpportunityAuditSnapshot(opportunity: Opportunity): OpportunityAuditSnapshot {
  return {
    id: opportunity.id,
    name: opportunity.name,
    accountName: opportunity.accountName,
    amountMinor: opportunity.amountMinor,
    currency: opportunity.currency,
    expectedCloseDate: opportunity.expectedCloseDate,
    stage: opportunity.stage,
    version: opportunity.version,
    lossReason: opportunity.lossReason,
    updatedAt: opportunity.updatedAt,
  }
}

export function opportunityAuditInput(
  action: 'opportunities.create' | 'opportunities.stage.change',
  subjectId: string,
  actor: { id: string; email: string; name: string },
  requestId: string,
  tenantId: string | undefined,
  before: Opportunity | null,
  after: Opportunity | null,
): AuditEventInput {
  return {
    actorId: actor.id,
    actorEmail: actor.email,
    actorName: actor.name,
    action,
    subjectType: 'opportunity',
    subjectId,
    before: before ? toOpportunityAuditSnapshot(before) : null,
    after: after ? toOpportunityAuditSnapshot(after) : null,
    correlationId: requestId,
    tenantId: tenantId ?? null,
  }
}

export function normalizeOpportunityCreateInput(input: OpportunityInput): OpportunityInput {
  return {
    name: input.name.trim(),
    accountName: input.accountName.trim(),
    amountMinor: input.amountMinor,
    currency: input.currency.toUpperCase(),
    expectedCloseDate: input.expectedCloseDate,
  }
}
