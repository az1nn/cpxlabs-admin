import { Card, CardContent, CardHeader, CardTitle, PageHeader } from '@cpxlabs-admin/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { useDataProvider } from '../../platform/data/data-provider-context'
import { CustomerForm } from './customer-form'
import { customerDetailQueryOptions, customerKeys } from './customer.queries'
import type { Customer, CustomerInput } from './customer.types'

type CustomerEditPageProps = {
  customerId: string
  onSaved: () => void
  onCancel: () => void
}

export function CustomerEditPage({ customerId, onSaved, onCancel }: CustomerEditPageProps) {
  const provider = useDataProvider()
  const queryClient = useQueryClient()
  const query = useQuery(customerDetailQueryOptions(provider, customerId))

  const mutation = useMutation({
    mutationFn: (input: CustomerInput) => provider.update<Customer>('customers', customerId, input),
    onSuccess: async (customer) => {
      queryClient.setQueryData(customerKeys.detail(customer.id), customer)
      await queryClient.invalidateQueries({ queryKey: customerKeys.lists() })
      onSaved()
    },
  })

  if (query.isPending) {
    return <p className="text-sm text-muted-foreground">Loading customer…</p>
  }

  if (query.isError) {
    return (
      <Card className="border-destructive/30 bg-destructive/5 p-5" role="alert">
        <p className="m-0 text-sm text-destructive">{query.error.message}</p>
      </Card>
    )
  }

  const customer = query.data
  const defaults: CustomerInput = {
    name: customer.name,
    email: customer.email,
    company: customer.company,
    status: customer.status,
  }

  return (
    <section className="grid max-w-3xl gap-6">
      <PageHeader
        eyebrow="CRM / Customers"
        title={`Edit ${customer.name}`}
        description="Changes are submitted through the DataProvider mutation boundary."
      />

      <Card>
        <CardHeader>
          <CardTitle>Customer information</CardTitle>
        </CardHeader>
        <CardContent>
          <CustomerForm
            defaultValues={defaults}
            submitLabel="Save changes"
            isSubmitting={mutation.isPending}
            {...(mutation.isError ? { submitError: mutation.error.message } : {})}
            onSubmit={async (input) => mutation.mutateAsync(input).then(() => undefined)}
            onCancel={onCancel}
          />
        </CardContent>
      </Card>
    </section>
  )
}
