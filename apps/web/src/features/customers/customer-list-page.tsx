import type { ListParams } from '@cpxlabs-admin/contracts'
import { useQuery } from '@tanstack/react-query'

import {
  DataGrid,
  type DataGridColumnDef,
  type DataGridSort,
} from '../../components/data-grid/data-grid'
import { useDataProvider } from '../../platform/data/data-provider-context'
import type { CustomerListSearch } from './customer-list-search'
import { customerListQueryOptions } from './customer.queries'
import type { Customer, CustomerStatus } from './customer.types'

const dateFormatter = new Intl.DateTimeFormat('en', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

const columns: Array<DataGridColumnDef<Customer>> = [
  {
    accessorKey: 'name',
    header: 'Customer',
  },
  {
    accessorKey: 'company',
    header: 'Company',
  },
  {
    accessorKey: 'email',
    header: 'Email',
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: (info) => {
      const status = info.getValue<CustomerStatus>()
      return <span className={`badge ${status}`}>{status}</span>
    },
  },
  {
    accessorKey: 'updatedAt',
    header: 'Updated',
    cell: (info) => dateFormatter.format(new Date(info.getValue<string>())),
  },
]

const sortableColumns = new Set(['name', 'company', 'status', 'updatedAt'])

type CustomerListPageProps = {
  search: CustomerListSearch
  onSearchChange: (patch: Partial<CustomerListSearch>) => void
}

export function CustomerListPage({
  search,
  onSearchChange,
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

  const updateSort = (sort: DataGridSort) => {
    onSearchChange({
      page: 1,
      sort: sort.field as CustomerListSearch['sort'],
      direction: sort.direction,
    })
  }

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <p className="eyebrow">CRM</p>
          <h1>Customers</h1>
          <p className="page-description">
            Reference resource using URL state, TanStack Query and a server-oriented
            DataProvider contract.
          </p>
        </div>
      </div>

      <div className="filter-bar" aria-label="Customer filters">
        <div className="field grow">
          <label htmlFor="customer-search">Search</label>
          <input
            id="customer-search"
            type="search"
            value={search.search}
            placeholder="Name, company or email"
            onChange={(event) =>
              onSearchChange({ page: 1, search: event.target.value })
            }
          />
        </div>

        <div className="field">
          <label htmlFor="customer-status">Status</label>
          <select
            id="customer-status"
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
          </select>
        </div>

        <div className="field">
          <label htmlFor="customer-page-size">Rows</label>
          <select
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
          </select>
        </div>
      </div>

      {query.isError ? (
        <div className="surface-card" role="alert">
          <strong>Unable to load customers.</strong>
          <p>{query.error.message}</p>
        </div>
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
