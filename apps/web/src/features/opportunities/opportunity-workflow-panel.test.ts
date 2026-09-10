import { describe, expect, it } from 'vitest'

import { suggestedOpportunityTargets } from './opportunity-workflow-panel'

describe('Opportunity workflow presentation', () => {
  it('suggests only the reference forward target plus loss from non-terminal stages', () => {
    expect(suggestedOpportunityTargets('qualification')).toEqual(['discovery', 'lost'])
    expect(suggestedOpportunityTargets('discovery')).toEqual(['proposal', 'lost'])
    expect(suggestedOpportunityTargets('proposal')).toEqual(['negotiation', 'lost'])
    expect(suggestedOpportunityTargets('negotiation')).toEqual(['won', 'lost'])
  })

  it('suppresses actions for terminal states', () => {
    expect(suggestedOpportunityTargets('won')).toEqual([])
    expect(suggestedOpportunityTargets('lost')).toEqual([])
  })
})
