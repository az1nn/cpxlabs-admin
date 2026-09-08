import { Card, CardContent, CardHeader, CardTitle, PageHeader } from '@cpxlabs-admin/ui'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { useDataProvider } from '../../platform/data/data-provider-context'
import { CustomerForm } from './customer-form'
import { customerKeys } from './customer.queries'
import type { Customer, CustomerInput } from './customer.types'

const emptyCustomer: CustomerInput = {
  name: '',
  email: '',
  company: '',
  status: 'lead',
}

type CustomerCreatePageProps = {
  onCreated: (id: string) => void
  onCancel: () => void
}

export function CustomerCreatePage({ onCreated, onCancel }: CustomerCreatePageProps) {
  const provider = useDataProvider()
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (input: CustomerInput) => provider.create<Customer>('customers', input),
    onSuccess: async (customer) => {
      await queryClient.invalidateQueries({ queryKey: customerKeys.all })
      onCreated(customer.id)
    },
  })

  return (
    <section className="grid max-w-3xl gap-6">
      <PageHeader
        eyebrow="CRM / Customers"
        title="New customer"
        description="Create a customer using the reusable schema-driven form primitive."
      />

      <Card>
        <CardHeader>
          <CardTitle>Customer information</CardTitle>
        </CardHeader>
        <CardContent>
          <CustomerForm
            defaultValues={emptyCustomer}
            submitLabel="Create customer"
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
