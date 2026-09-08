import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
  PageHeader,
} from '@cpxlabs-admin/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Can } from '../../platform/authorization/authorization-provider'
import { useDataProvider } from '../../platform/data/data-provider-context'
import { customerDetailQueryOptions, customerKeys } from './customer.queries'
import type { CustomerStatus } from './customer.types'

const statusVariant: Record<CustomerStatus, 'success' | 'warning' | 'secondary'> = {
  active: 'success',
  lead: 'warning',
  inactive: 'secondary',
}

type CustomerDetailPageProps = {
  customerId: string
  onBack: () => void
  onEdit: () => void
  onDeleted: () => void
}

export function CustomerDetailPage({
  customerId,
  onBack,
  onEdit,
  onDeleted,
}: CustomerDetailPageProps) {
  const provider = useDataProvider()
  const queryClient = useQueryClient()
  const query = useQuery(customerDetailQueryOptions(provider, customerId))

  const deleteMutation = useMutation({
    mutationFn: () => provider.delete('customers', customerId),
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: customerKeys.detail(customerId) })
      await queryClient.invalidateQueries({ queryKey: customerKeys.lists() })
      onDeleted()
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

  return (
    <section className="grid max-w-4xl gap-6">
      <PageHeader
        eyebrow="CRM / Customers"
        title={customer.name}
        description={`Customer ID ${customer.id}`}
        actions={
          <>
            <Button variant="outline" onClick={onBack}>Back</Button>
            <Can capability="customers.update">
              <Button variant="outline" onClick={onEdit}>Edit</Button>
            </Can>
            <Can capability="customers.delete">
              <Dialog>
                <DialogTrigger render={<Button variant="destructive" />}>Delete</DialogTrigger>
                <DialogContent>
                  <div className="grid gap-2">
                    <DialogTitle className="text-lg font-semibold">Delete customer?</DialogTitle>
                    <DialogDescription className="text-sm leading-6 text-muted-foreground">
                      This removes {customer.name} from the current data provider. This action cannot be undone.
                    </DialogDescription>
                  </div>
                  {deleteMutation.isError ? (
                    <p className="m-0 text-sm text-destructive" role="alert">{deleteMutation.error.message}</p>
                  ) : null}
                  <div className="flex justify-end gap-2">
                    <DialogClose render={<Button variant="outline" />}>Cancel</DialogClose>
                    <Button
                      variant="destructive"
                      disabled={deleteMutation.isPending}
                      onClick={() => deleteMutation.mutate()}
                    >
                      {deleteMutation.isPending ? 'Deleting…' : 'Delete customer'}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </Can>
          </>
        }
      />

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Customer profile</CardTitle>
            <CardDescription>Reference show view for resource-oriented applications.</CardDescription>
          </div>
          <Badge variant={statusVariant[customer.status]}>{customer.status}</Badge>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Company</dt>
              <dd className="m-0 mt-1 text-sm font-medium">{customer.company}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Email</dt>
              <dd className="m-0 mt-1 text-sm font-medium">{customer.email}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Status</dt>
              <dd className="m-0 mt-1 text-sm font-medium capitalize">{customer.status}</dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Updated</dt>
              <dd className="m-0 mt-1 text-sm font-medium">{new Date(customer.updatedAt).toLocaleString()}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </section>
  )
}
