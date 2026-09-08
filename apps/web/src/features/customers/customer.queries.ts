import type { DataProvider, ListParams } from '@cpxlabs-admin/contracts'
import { keepPreviousData, queryOptions } from '@tanstack/react-query'

import type { Customer } from './customer.types'

export const customerKeys = {
  all: ['customers'] as const,
  list: (params: ListParams) => [...customerKeys.all, 'list', params] as const,
}

export function customerListQueryOptions(
  provider: DataProvider,
  params: ListParams,
) {
  return queryOptions({
    queryKey: customerKeys.list(params),
    queryFn: () => provider.getList<Customer>('customers', params),
    placeholderData: keepPreviousData,
  })
}
