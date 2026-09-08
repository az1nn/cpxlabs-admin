export type SortDirection = 'asc' | 'desc'

export type ListParams = {
  page: number
  pageSize: number
  sort?: {
    field: string
    direction: SortDirection
  }
  filters?: Readonly<Record<string, unknown>>
  search?: string
}

export type ListResult<T> = {
  data: readonly T[]
  total: number
}

export interface DataProvider {
  getList<T>(resource: string, params: ListParams): Promise<ListResult<T>>
  getOne<T>(resource: string, id: string): Promise<T>
  create<T>(resource: string, input: unknown): Promise<T>
  update<T>(resource: string, id: string, input: unknown): Promise<T>
  delete(resource: string, id: string): Promise<void>
}
