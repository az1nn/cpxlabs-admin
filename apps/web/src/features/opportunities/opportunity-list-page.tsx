import type { OpportunityDto, OpportunityListQuery, OpportunityStage } from '@cpxlabs-admin/contracts'
import { Badge, Button, Card, Input, PageHeader, Select } from '@cpxlabs-admin/ui'
import { useQuery } from '@tanstack/react-query'

import { DataGrid, type DataGridColumnDef, type DataGridSort } from '../../components/data-grid/data-grid'
import { Can } from '../../platform/authorization/authorization-provider'
import { appOpportunityService } from './app-opportunity-service'
import type { OpportunityListSearch } from './opportunity-list-search'
import { opportunityListQueryOptions } from './opportunity.queries'

const sortableColumns = new Set(['name', 'accountName', 'amountMinor', 'expectedCloseDate', 'stage', 'updatedAt'])

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

type OpportunityListPageProps = {
  search: OpportunityListSearch
  onSearchChange: (patch: Partial<OpportunityListSearch>) => void
  onCreate: () => void
  onOpen: (id: string) => void
}

export function OpportunityListPage({ search, onSearchChange, onCreate, onOpen }: OpportunityListPageProps) {
  const queryParams: OpportunityListQuery = {
    page: search.page,
    pageSize: search.pageSize,
    sort: search.sort,
    direction: search.direction,
    ...(search.search.trim() ? { search: search.search.trim() } : {}),
    ...(search.stage !== 'all' ? { stage: search.stage } : {}),
  }
  const query = useQuery(opportunityListQueryOptions(appOpportunityService, queryParams))
  const rows = query.data?.data ? [...query.data.data] : []

  const columns: Array<DataGridColumnDef<OpportunityDto>> = [
    {
      accessorKey: 'name',
      header: 'Opportunity',
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
    { accessorKey: 'accountName', header: 'Account' },
    {
      accessorKey: 'amountMinor',
      header: 'Value',
      cell: (info) => formatMoney(info.getValue<number>(), info.row.original.currency),
    },
    {
      accessorKey: 'stage',
      header: 'Stage',
      cell: (info) => {
        const stage = info.getValue<OpportunityStage>()
        return <Badge variant={stageVariant[stage]}>{stage}</Badge>
      },
    },
    { accessorKey: 'expectedCloseDate', header: 'Expected close' },
    { accessorKey: 'version', header: 'Version' },
  ]

  const updateSort = (sort: DataGridSort) => onSearchChange({
    page: 1,
    sort: sort.field as OpportunityListSearch['sort'],
    direction: sort.direction,
  })

  return (
    <section className="grid gap-6">
      <PageHeader
        eyebrow="CRM"
        title="Opportunities"
        description="A domain workflow resource: URL-owned list state, server-owned lifecycle and explicit command mutations."
        actions={
          <Can capability="opportunities.create">
            <Button onClick={onCreate}>New opportunity</Button>
          </Can>
        }
      />

      <Card className="flex flex-col gap-4 p-4 sm:flex-row sm:items-end" aria-label="Opportunity filters">
        <div className="grid flex-1 gap-1.5">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="opportunity-search">Search</label>
          <Input
            id="opportunity-search"
            type="search"
            value={search.search}
            placeholder="Opportunity or account"
            onChange={(event) => onSearchChange({ page: 1, search: event.target.value })}
          />
        </div>
        <div className="grid gap-1.5 sm:w-48">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="opportunity-stage-filter">Stage</label>
          <Select
            id="opportunity-stage-filter"
            value={search.stage}
            onChange={(event) => onSearchChange({ page: 1, stage: event.target.value as OpportunityListSearch['stage'] })}
          >
            <option value="all">All stages</option>
            <option value="qualification">Qualification</option>
            <option value="discovery">Discovery</option>
            <option value="proposal">Proposal</option>
            <option value="negotiation">Negotiation</option>
            <option value="won">Won</option>
            <option value="lost">Lost</option>
          </Select>
        </div>
        <div className="grid gap-1.5 sm:w-32">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="opportunity-page-size">Rows</label>
          <Select
            id="opportunity-page-size"
            value={search.pageSize}
            onChange={(event) => onSearchChange({ page: 1, pageSize: Number(event.target.value) })}
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
          <h2 className="m-0 text-sm font-semibold text-destructive">Unable to load opportunities.</h2>
          <p className="mb-0 mt-1 text-sm text-muted-foreground">{query.error.message}</p>
        </Card>
      ) : (
        <DataGrid
          rows={rows}
          columns={columns}
          rowCount={query.data?.total ?? 0}
          page={search.page}
          pageSize={search.pageSize}
          sort={{ field: search.sort, direction: search.direction }}
          sortableColumns={sortableColumns}
          isFetching={query.isFetching}
          getRowId={(opportunity) => opportunity.id}
          onPageChange={(page) => onSearchChange({ page })}
          onSortChange={updateSort}
        />
      )}
    </section>
  )
}
