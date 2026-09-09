import { Card, CardContent, CardHeader, CardTitle, PageHeader } from '@cpxlabs-admin/ui'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { useAuthorization } from '../../platform/authorization/authorization-provider'
import { appOpportunityService } from './app-opportunity-service'
import { OpportunityForm } from './opportunity-form'
import { opportunityKeys } from './opportunity.queries'
import type { OpportunityFormValues } from './opportunity.schema'

const emptyOpportunity: OpportunityFormValues = {
  name: '',
  accountName: '',
  amount: 0,
  currency: 'BRL',
  expectedCloseDate: '',
}

type OpportunityCreatePageProps = {
  onCreated: (id: string) => void
  onCancel: () => void
}

export function OpportunityCreatePage({ onCreated, onCancel }: OpportunityCreatePageProps) {
  const authorization = useAuthorization()
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (values: OpportunityFormValues) => appOpportunityService.create({
      name: values.name.trim(),
      accountName: values.accountName.trim(),
      amountMinor: Math.round(values.amount * 100),
      currency: values.currency.trim().toUpperCase(),
      expectedCloseDate: values.expectedCloseDate,
    }),
    onSuccess: async (opportunity) => {
      await queryClient.invalidateQueries({ queryKey: opportunityKeys.all })
      onCreated(opportunity.id)
    },
  })

  if (!authorization.can('opportunities.create')) {
    return (
      <section className="grid max-w-3xl gap-6">
        <PageHeader eyebrow="CRM / Opportunities" title="New opportunity" />
        <Card className="p-5" role="alert">
          <h2 className="m-0 text-sm font-semibold">Creation is not available for your role.</h2>
          <p className="mb-0 mt-1 text-sm text-muted-foreground">The API remains authoritative if this route is accessed directly.</p>
        </Card>
      </section>
    )
  }

  return (
    <section className="grid max-w-3xl gap-6">
      <PageHeader
        eyebrow="CRM / Opportunities"
        title="New opportunity"
        description="Create the commercial record; workflow stage and version are assigned by the server."
      />
      <Card>
        <CardHeader><CardTitle>Opportunity information</CardTitle></CardHeader>
        <CardContent>
          <OpportunityForm
            defaultValues={emptyOpportunity}
            isSubmitting={mutation.isPending}
            {...(mutation.isError ? { submitError: mutation.error.message } : {})}
            onSubmit={async (values) => mutation.mutateAsync(values).then(() => undefined)}
            onCancel={onCancel}
          />
        </CardContent>
      </Card>
    </section>
  )
}
