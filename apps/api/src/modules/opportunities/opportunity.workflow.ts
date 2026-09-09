import type { OpportunityStage } from './opportunity.types.js'

const transitions = {
  qualification: ['discovery', 'lost'],
  discovery: ['proposal', 'lost'],
  proposal: ['negotiation', 'lost'],
  negotiation: ['won', 'lost'],
  won: [],
  lost: [],
} satisfies Record<OpportunityStage, readonly OpportunityStage[]>

export class OpportunityTransitionError extends Error {
  constructor(message = 'The requested opportunity transition is not allowed') {
    super(message)
    this.name = 'OpportunityTransitionError'
  }
}

export function allowedOpportunityTargets(stage: OpportunityStage): readonly OpportunityStage[] {
  return transitions[stage]
}

export function normalizeOpportunityTransition(
  currentStage: OpportunityStage,
  targetStage: OpportunityStage,
  lossReason: string | undefined,
): { stage: OpportunityStage; lossReason: string | null } {
  const allowed = transitions[currentStage] as readonly OpportunityStage[]
  if (!allowed.includes(targetStage)) {
    throw new OpportunityTransitionError()
  }

  if (targetStage === 'lost') {
    const normalized = lossReason?.trim()
    if (!normalized) {
      throw new OpportunityTransitionError('A loss reason is required when an opportunity is lost')
    }
    return { stage: targetStage, lossReason: normalized }
  }

  return { stage: targetStage, lossReason: null }
}
