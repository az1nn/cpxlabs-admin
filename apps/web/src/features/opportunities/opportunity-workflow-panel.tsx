import type { OpportunityDto, OpportunityStage } from '@cpxlabs-admin/contracts'
import { Button, Card, Input } from '@cpxlabs-admin/ui'
import { useState } from 'react'

import { useAuthorization } from '../../platform/authorization/authorization-provider'

const stageLabel: Record<OpportunityStage, string> = {
  qualification: 'Qualification',
  discovery: 'Discovery',
  proposal: 'Proposal',
  negotiation: 'Negotiation',
  won: 'Won',
  lost: 'Lost',
}

export function suggestedOpportunityTargets(stage: OpportunityStage): readonly OpportunityStage[] {
  switch (stage) {
    case 'qualification': return ['discovery', 'lost']
    case 'discovery': return ['proposal', 'lost']
    case 'proposal': return ['negotiation', 'lost']
    case 'negotiation': return ['won', 'lost']
    case 'won':
    case 'lost':
      return []
  }
}

type OpportunityWorkflowPanelProps = {
  opportunity: OpportunityDto
  isPending: boolean
  errorMessage?: string
  conflictMessage?: string
  onTransition: (targetStage: OpportunityStage, lossReason?: string) => Promise<void> | void
}

export function OpportunityWorkflowPanel({
  opportunity,
  isPending,
  errorMessage,
  conflictMessage,
  onTransition,
}: OpportunityWorkflowPanelProps) {
  const authorization = useAuthorization()
  const [lossReason, setLossReason] = useState('')
  const targets = suggestedOpportunityTargets(opportunity.stage)

  if (!authorization.can('opportunities.transition')) return null

  if (targets.length === 0) {
    return (
      <Card className="p-5" aria-label="Opportunity workflow">
        <h2 className="m-0 text-base font-semibold">Workflow</h2>
        <p className="mb-0 mt-2 text-sm text-muted-foreground">
          {stageLabel[opportunity.stage]} is terminal in the reference workflow. No transition controls are available.
        </p>
      </Card>
    )
  }

  const forwardTargets = targets.filter((stage) => stage !== 'lost')
  const canLose = targets.includes('lost')

  return (
    <Card className="grid gap-4 p-5" aria-label="Opportunity workflow">
      <div>
        <h2 className="m-0 text-base font-semibold">Workflow</h2>
        <p className="mb-0 mt-1 text-sm text-muted-foreground">
          Suggested actions are derived from the current state. The API validates every command authoritatively.
        </p>
      </div>

      {conflictMessage ? (
        <div className="rounded-md border border-warning/30 bg-warning/5 px-3 py-2 text-sm" role="alert">
          {conflictMessage}
        </div>
      ) : null}
      {errorMessage ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive" role="alert">
          {errorMessage}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2">
        {forwardTargets.map((target) => (
          <Button
            key={target}
            disabled={isPending}
            onClick={() => void onTransition(target)}
          >
            Move to {stageLabel[target]}
          </Button>
        ))}
      </div>

      {canLose ? (
        <div className="grid gap-2 border-t pt-4">
          <label htmlFor="opportunity-loss-reason" className="text-sm font-medium">Loss reason</label>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              id="opportunity-loss-reason"
              value={lossReason}
              maxLength={500}
              placeholder="Required before marking lost"
              onChange={(event) => setLossReason(event.target.value)}
            />
            <Button
              variant="destructive"
              disabled={isPending || !lossReason.trim()}
              onClick={() => void onTransition('lost', lossReason.trim())}
            >
              Mark lost
            </Button>
          </div>
        </div>
      ) : null}
    </Card>
  )
}
