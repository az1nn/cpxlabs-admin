import type { OpportunityStage } from '@cpxlabs-admin/contracts'
import { Badge } from '@cpxlabs-admin/ui'

const stageVariant: Record<OpportunityStage, 'default' | 'secondary' | 'warning' | 'success' | 'destructive' | 'outline'> = {
  qualification: 'secondary',
  discovery: 'outline',
  proposal: 'default',
  negotiation: 'warning',
  won: 'success',
  lost: 'destructive',
}

type OpportunityStageBadgeProps = {
  stage: OpportunityStage
}

export function OpportunityStageBadge({ stage }: OpportunityStageBadgeProps) {
  return <Badge variant={stageVariant[stage]} aria-label={`Stage: ${stage}`}>{stage}</Badge>
}
