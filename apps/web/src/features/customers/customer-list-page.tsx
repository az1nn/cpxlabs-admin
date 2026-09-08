import type { ListParams } from '@cpxlabs-admin/contracts'
import { Badge, Button, Card, PageHeader, Select, Input } from '@cpxlabs-admin/ui'
import { useQuery } from '@tanstack/react-query'

import {
  DataGrid,
  type DataGridColumnDef,
  type DataGridSort,
} from '../../components/data-grid/data-grid'
import { Can } from '../../platform/authorization/authorization-provider'
import { useDataProvider } from '../../platform/data/data-provider-context'
import type { CustomerListSearch } from './customer-list-search'
import { customerListQueryOptions } from './customer.queries'
import type { Customer, CustomerStatus } from './customer.types'

const dateFormatter = new Intl.DateTimeFormat('en', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

const sortableColumns = new Set(['name', 'company', 'status', 'updatedAt'])

const statusVariant: Record<CustomerStatus, 'success' | 'warning' | 'secondary'> = {
  active: 'success',
  lead: 'warning',
  inactive: 'secondary',
}

type CustomerListPageProps = {
  search: CustomerListSearch
  onSearchChange: (patch: Partial<CustomerListSearch>) => void
  onCreate: () => void
  onOpen: (id: string) => void
}

export function CustomerListPage({
  search,
  onSearchChange,
  onCreate,
  onOpen,
}: CustomerListPageProps) {
  const provider = useDataProvider()

  const params: ListParams = {
    page: search.page,
    pageSize: search.pageSize,
    sort: {
      field: search.sort,
      direction: search.direction,
    },
    ...(search.search.trim() ? { search: search.search.trim() } : {}),
    ...(search.status !== 'all' ? { filters: { status: search.status } } : {}),
  }

  const query = useQuery(customerListQueryOptions(provider, params))
  const rows = query.data?.data ? [...query.data.data] : []
  const rowCount = query.data?.total ?? 0

  const columns: Array<DataGridColumnDef<Customer>> = [
    {
      accessorKey: 'name',
      header: 'Customer',
      cell: (info) => (
        <button
          type="button"
          className="font-medium text-foreground underline-offset-4 hover:underline"
          onClick={() => onOpen(info.row.original.id)}
        >
          {info.getValue<string>()}
        </button>
      ),
    },
    { accessorKey: 'company', header: 'Company' },
    { accessorKey: 'email', header: 'Email' },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: (info) => {
        const status = info.getValue<CustomerStatus>()
        return <Badge variant={statusVariant[status]}>{status}</Badge>
      },
    },
    {
      accessorKey: 'updatedAt',
      header: 'Updated',
      cell: (info) => dateFormatter.format(new Date(info.getValue<string>())),
    },
  ]

  const updateSort = (sort: DataGridSort) => {
    onSearchChange({
      page: 1,
      sort: sort.field as CustomerListSearch['sort'],
      direction: sort.direction,
    })
  }

  return (
    <section className="grid gap-6">
      <PageHeader
        eyebrow="CRM"
        title="Customers"
        description="Reference resource using URL state, TanStack Query, typed capabilities and a server-oriented DataProvider contract."
        actions={
          <Can capability="customers.create">
            <Button onClick={onCreate}>New customer</Button>
          </Can>
        }
      />

      <Card className="flex flex-col gap-4 p-4 sm:flex-row sm:items-end" aria-label="Customer filters">
        <div className="grid flex-1 gap-1.5">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="customer-search">
            Search
          </label>
          <Input
            id="customer-search"
            type="search"
            value={search.search}
            placeholder="Name, company or email"
            onChange={(event) => onSearchChange({ page: 1, search: event.target.value })}
          />
        </div>

        <div className="grid gap-1.5 sm:w-44">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="customer-status-filter">
            Status
          </label>
          <Select
            id="customer-status-filter"
            value={search.status}
            onChange={(event) =>
              onSearchChange({
                page: 1,
                status: event.target.value as CustomerListSearch['status'],
              })
            }
          >
            <option value="all">All</option>
            <option value="lead">Lead</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </Select>
        </div>

        <div className="grid gap-1.5 sm:w-32">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="customer-page-size">
            Rows
          </label>
          <Select
            id="customer-page-size"
            value={search.pageSize}
            onChange={(event) =>
              onSearchChange({ page: 1, pageSize: Number(event.target.value) })
            }
          >
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </Select>
        </div>
      </Card>

      {query.isError ? (
        <Card className="border-destructive/30 bg-destructive/5 p-5" role="alert">
          <h2 className="m-0 text-sm font-semibold text-destructive">Unable to load customers.</h2>
          <p className="mb-0 mt-1 text-sm text-muted-foreground">{query.error.message}</p>
        </Card>
      ) : (
        <DataGrid
          rows={rows}
          columns={columns}
          rowCount={rowCount}
          page={search.page}
          pageSize={search.pageSize}
          sort={{ field: search.sort, direction: search.direction }}
          sortableColumns={sortableColumns}
          isFetching={query.isFetching}
          getRowId={(customer) => customer.id}
          onPageChange={(page) => onSearchChange({ page })}
          onSortChange={updateSort}
        />
      )}
    </section>
  )
}
