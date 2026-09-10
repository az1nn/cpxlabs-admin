import type { OpportunityListQuery } from '@cpxlabs-admin/contracts'
import { keepPreviousData, queryOptions } from '@tanstack/react-query'

import type { OpportunityService } from './opportunity.service'

export const opportunityKeys = {
  all: ['opportunities'] as const,
  lists: () => [...opportunityKeys.all, 'list'] as const,
  list: (query: OpportunityListQuery) => [...opportunityKeys.lists(), query] as const,
  details: () => [...opportunityKeys.all, 'detail'] as const,
  detail: (id: string) => [...opportunityKeys.details(), id] as const,
}

export function opportunityListQueryOptions(
  service: OpportunityService,
  query: OpportunityListQuery,
) {
  return queryOptions({
    queryKey: opportunityKeys.list(query),
    queryFn: () => service.list(query),
    placeholderData: keepPreviousData,
  })
}

export function opportunityDetailQueryOptions(service: OpportunityService, id: string) {
  return queryOptions({
    queryKey: opportunityKeys.detail(id),
    queryFn: () => service.get(id),
  })
}
