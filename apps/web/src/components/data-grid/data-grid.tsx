import { tableFeatures, useTable, type ColumnDef } from '@tanstack/react-table'

const dataGridFeatures = tableFeatures({})

export type DataGridColumnDef<TData> = ColumnDef<typeof dataGridFeatures, TData>

export type DataGridSort = {
  field: string
  direction: 'asc' | 'desc'
}

type DataGridProps<TData> = {
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

export function DataGrid<TData>({
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
    <div className="data-panel" aria-busy={isFetching}>
      <div className="table-status" aria-live="polite">
        {isFetching ? 'Refreshing data…' : `${rowCount} records`}
      </div>

      <div className="table-scroll">
        <table className="data-table">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const sortable = sortableColumns.has(header.column.id)
                  const active = sort.field === header.column.id
                  const ariaSort = active
                    ? sort.direction === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : undefined

                  return (
                    <th key={header.id} aria-sort={ariaSort}>
                      {header.isPlaceholder ? null : sortable ? (
                        <button
                          className="sort-button"
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
                <td className="empty-cell" colSpan={columns.length}>
                  No records match the current filters.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr key={row.id}>
                  {row.getAllCells().map((cell) => (
                    <td key={cell.id}>
                      <table.FlexRender cell={cell} />
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <span>
          Page {safePage} of {pageCount}
        </span>
        <div className="pagination-actions">
          <button
            className="secondary-button"
            type="button"
            disabled={safePage <= 1}
            onClick={() => onPageChange(safePage - 1)}
          >
            Previous
          </button>
          <button
            className="secondary-button"
            type="button"
            disabled={safePage >= pageCount}
            onClick={() => onPageChange(safePage + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
