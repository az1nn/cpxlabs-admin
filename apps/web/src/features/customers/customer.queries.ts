import type { DataProvider, ListParams } from '@cpxlabs-admin/contracts'
import { keepPreviousData, queryOptions } from '@tanstack/react-query'

import type { Customer } from './customer.types'

export const customerKeys = {
  all: ['customers'] as const,
  lists: () => [...customerKeys.all, 'list'] as const,
  list: (params: ListParams) => [...customerKeys.lists(), params] as const,
  details: () => [...customerKeys.all, 'detail'] as const,
  detail: (id: string) => [...customerKeys.details(), id] as const,
}

export function customerListQueryOptions(provider: DataProvider, params: ListParams) {
  return queryOptions({
    queryKey: customerKeys.list(params),
    queryFn: () => provider.getList<Customer>('customers', params),
    placeholderData: keepPreviousData,
  })
}

export function customerDetailQueryOptions(provider: DataProvider, id: string) {
  return queryOptions({
    queryKey: customerKeys.detail(id),
    queryFn: () => provider.getOne<Customer>('customers', id),
  })
}
