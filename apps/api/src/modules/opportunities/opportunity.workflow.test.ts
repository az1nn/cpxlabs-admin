import { describe, expect, it } from 'vitest'

import {
  allowedOpportunityTargets,
  normalizeOpportunityTransition,
  OpportunityTransitionError,
} from './opportunity.workflow.js'

const forwardCases = [
  ['qualification', 'discovery'],
  ['discovery', 'proposal'],
  ['proposal', 'negotiation'],
  ['negotiation', 'won'],
] as const

describe('opportunity lifecycle', () => {
  it.each(forwardCases)('accepts %s → %s', (current, target) => {
    expect(normalizeOpportunityTransition(current, target, undefined)).toEqual({
      stage: target,
      lossReason: null,
    })
  })

  it.each(['qualification', 'discovery', 'proposal', 'negotiation'] as const)(
    'allows %s → lost with a normalized reason',
    (current) => {
      expect(normalizeOpportunityTransition(current, 'lost', '  Budget cancelled  ')).toEqual({
        stage: 'lost',
        lossReason: 'Budget cancelled',
      })
    },
  )

  it.each([
    ['qualification', 'proposal'],
    ['discovery', 'qualification'],
    ['proposal', 'discovery'],
    ['negotiation', 'proposal'],
    ['won', 'lost'],
    ['lost', 'qualification'],
  ] as const)('rejects invalid %s → %s transitions', (current, target) => {
    expect(() => normalizeOpportunityTransition(current, target, undefined)).toThrow(
      OpportunityTransitionError,
    )
  })

  it('requires a non-blank loss reason', () => {
    expect(() => normalizeOpportunityTransition('proposal', 'lost', '   ')).toThrow(
      OpportunityTransitionError,
    )
  })

  it('exposes terminal states with no next targets', () => {
    expect(allowedOpportunityTargets('won')).toEqual([])
    expect(allowedOpportunityTargets('lost')).toEqual([])
  })
})
