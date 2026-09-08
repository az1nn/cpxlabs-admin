import { Button } from '@cpxlabs-admin/ui'
import {
  tableFeatures,
  useTable,
  type ColumnDef,
  type RowData,
} from '@tanstack/react-table'

const dataGridFeatures = tableFeatures({})

export type DataGridColumnDef<TData extends RowData> = ColumnDef<
  typeof dataGridFeatures,
  TData
>

export type DataGridSort = {
  field: string
  direction: 'asc' | 'desc'
}

type DataGridProps<TData extends RowData> = {
  rows: TData[]
  columns: Array<DataGridColumnDef<TData>>
  rowCount: number
  page: number
  pageSize: number
  sort: DataGridSort
  sortableColumns: ReadonlySet<string>
  isFetching: boolean
  getRowId: (row: TData) => string
  onPageChange: (page: number) => void
  onSortChange: (sort: DataGridSort) => void
}

export function DataGrid<TData extends RowData>({
  rows,
  columns,
  rowCount,
  page,
  pageSize,
  sort,
  sortableColumns,
  isFetching,
  getRowId,
  onPageChange,
  onSortChange,
}: DataGridProps<TData>) {
  const table = useTable({
    features: dataGridFeatures,
    columns,
    data: rows,
    getRowId,
  })

  const pageCount = Math.max(1, Math.ceil(rowCount / pageSize))
  const safePage = Math.min(page, pageCount)

  const toggleSort = (field: string) => {
    onSortChange({
      field,
      direction: sort.field === field && sort.direction === 'asc' ? 'desc' : 'asc',
    })
  }

  return (
    <div className="overflow-hidden rounded-lg border bg-card shadow-sm" aria-busy={isFetching}>
      <div className="flex min-h-10 items-center border-b bg-muted/25 px-4 text-xs text-muted-foreground" aria-live="polite">
        {isFetching ? 'Refreshing data…' : `${rowCount} records`}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="border-b bg-muted/35">
                {headerGroup.headers.map((header) => {
                  const sortable = sortableColumns.has(header.column.id)
                  const active = sort.field === header.column.id
                  const ariaSort = active
                    ? sort.direction === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : undefined

                  return (
                    <th
                      key={header.id}
                      className="h-11 whitespace-nowrap px-4 text-left text-xs font-semibold text-muted-foreground"
                      aria-sort={ariaSort}
                    >
                      {header.isPlaceholder ? null : sortable ? (
                        <button
                          className="inline-flex items-center gap-1.5 rounded-sm outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/50"
                          type="button"
                          onClick={() => toggleSort(header.column.id)}
                        >
                          <table.FlexRender header={header} />
                          <span aria-hidden="true">
                            {active ? (sort.direction === 'asc' ? '↑' : '↓') : '↕'}
                          </span>
                        </button>
                      ) : (
                        <table.FlexRender header={header} />
                      )}
                    </th>
                  )
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td className="h-36 px-4 text-center text-sm text-muted-foreground" colSpan={columns.length}>
                  No records match the current filters.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="border-b last:border-b-0 hover:bg-muted/20">
                  {row.getAllCells().map((cell) => (
                    <td key={cell.id} className="whitespace-nowrap px-4 py-3.5 align-middle">
                      <table.FlexRender cell={cell} />
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col gap-3 border-t px-4 py-3 text-sm sm:flex-row sm:items-center sm:justify-between">
        <span className="text-muted-foreground">
          Page {safePage} of {pageCount}
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            type="button"
            disabled={safePage <= 1}
            onClick={() => onPageChange(safePage - 1)}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            type="button"
            disabled={safePage >= pageCount}
            onClick={() => onPageChange(safePage + 1)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  )
}
