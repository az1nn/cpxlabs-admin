import type { OpportunityStage } from '@cpxlabs-admin/contracts'
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, PageHeader } from '@cpxlabs-admin/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { appOpportunityService } from './app-opportunity-service'
import { OpportunityServiceError } from './opportunity.service'
import { OpportunityWorkflowPanel } from './opportunity-workflow-panel'
import { opportunityDetailQueryOptions, opportunityKeys } from './opportunity.queries'

const stageVariant: Record<OpportunityStage, 'default' | 'secondary' | 'warning' | 'success' | 'destructive' | 'outline'> = {
  qualification: 'secondary',
  discovery: 'outline',
  proposal: 'default',
  negotiation: 'warning',
  won: 'success',
  lost: 'destructive',
}

function formatMoney(amountMinor: number, currency: string) {
  try {
    return new Intl.NumberFormat('en', { style: 'currency', currency }).format(amountMinor / 100)
  } catch {
    return `${currency} ${(amountMinor / 100).toFixed(2)}`
  }
}

type OpportunityDetailPageProps = {
  opportunityId: string
  onBack: () => void
}

export function OpportunityDetailPage({ opportunityId, onBack }: OpportunityDetailPageProps) {
  const queryClient = useQueryClient()
  const query = useQuery(opportunityDetailQueryOptions(appOpportunityService, opportunityId))
  const [conflictMessage, setConflictMessage] = useState<string>()

  const mutation = useMutation({
    mutationFn: (input: { targetStage: OpportunityStage; expectedVersion: number; lossReason?: string }) =>
      appOpportunityService.transition(opportunityId, input),
    onSuccess: async (opportunity) => {
      setConflictMessage(undefined)
      queryClient.setQueryData(opportunityKeys.detail(opportunityId), opportunity)
      await queryClient.invalidateQueries({ queryKey: opportunityKeys.lists() })
    },
    onError: async (error) => {
      if (error instanceof OpportunityServiceError && error.code === 'WORKFLOW_CONFLICT') {
        setConflictMessage('This opportunity changed after you loaded it. The latest server state has been refreshed; review it before issuing another command.')
        await queryClient.refetchQueries({ queryKey: opportunityKeys.detail(opportunityId), exact: true })
        await queryClient.invalidateQueries({ queryKey: opportunityKeys.lists() })
      }
    },
  })

  if (query.isPending) {
    return <Card className="p-5 text-sm text-muted-foreground">Loading opportunity…</Card>
  }

  if (query.isError) {
    return (
      <Card className="border-destructive/30 bg-destructive/5 p-5" role="alert">
        <h1 className="m-0 text-base font-semibold text-destructive">Unable to load opportunity.</h1>
        <p className="mb-4 mt-1 text-sm text-muted-foreground">{query.error.message}</p>
        <Button variant="outline" onClick={onBack}>Back to opportunities</Button>
      </Card>
    )
  }

  const opportunity = query.data

  return (
    <section className="grid gap-6">
      <PageHeader
        eyebrow="CRM / Opportunities"
        title={opportunity.name}
        description={`${opportunity.accountName} · version ${opportunity.version}`}
        actions={<Button variant="outline" onClick={onBack}>Back</Button>}
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Opportunity details</CardTitle></CardHeader>
          <CardContent className="grid gap-5 sm:grid-cols-2">
            <div>
              <p className="m-0 text-xs font-medium uppercase tracking-wide text-muted-foreground">Stage</p>
              <div className="mt-2"><Badge variant={stageVariant[opportunity.stage]}>{opportunity.stage}</Badge></div>
            </div>
            <div>
              <p className="m-0 text-xs font-medium uppercase tracking-wide text-muted-foreground">Value</p>
              <p className="mb-0 mt-1 text-sm font-medium">{formatMoney(opportunity.amountMinor, opportunity.currency)}</p>
            </div>
            <div>
              <p className="m-0 text-xs font-medium uppercase tracking-wide text-muted-foreground">Expected close</p>
              <p className="mb-0 mt-1 text-sm">{opportunity.expectedCloseDate}</p>
            </div>
            <div>
              <p className="m-0 text-xs font-medium uppercase tracking-wide text-muted-foreground">Version</p>
              <p className="mb-0 mt-1 text-sm">{opportunity.version}</p>
            </div>
            {opportunity.lossReason ? (
              <div className="sm:col-span-2">
                <p className="m-0 text-xs font-medium uppercase tracking-wide text-muted-foreground">Loss reason</p>
                <p className="mb-0 mt-1 text-sm">{opportunity.lossReason}</p>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Lifecycle metadata</CardTitle></CardHeader>
          <CardContent className="grid gap-4 text-sm">
            <div><span className="text-muted-foreground">Created</span><br />{new Date(opportunity.createdAt).toLocaleString()}</div>
            <div><span className="text-muted-foreground">Updated</span><br />{new Date(opportunity.updatedAt).toLocaleString()}</div>
          </CardContent>
        </Card>
      </div>

      <OpportunityWorkflowPanel
        opportunity={opportunity}
        isPending={mutation.isPending}
        {...(conflictMessage ? { conflictMessage } : {})}
        {...(mutation.isError && (!(mutation.error instanceof OpportunityServiceError) || mutation.error.code !== 'WORKFLOW_CONFLICT')
          ? { errorMessage: mutation.error.message }
          : {})}
        onTransition={async (targetStage, lossReason) => {
          await mutation.mutateAsync({
            targetStage,
            expectedVersion: opportunity.version,
            ...(lossReason ? { lossReason } : {}),
          }).then(() => undefined)
        }}
      />
    </section>
  )
}
