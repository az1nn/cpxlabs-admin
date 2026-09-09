import { z } from 'zod'

export const opportunityListSearchSchema = z.object({
  page: z.coerce.number().int().positive().catch(1),
  pageSize: z.coerce.number().int().min(10).max(100).catch(25),
  search: z.string().catch(''),
  stage: z.enum(['all', 'qualification', 'discovery', 'proposal', 'negotiation', 'won', 'lost']).catch('all'),
  sort: z.enum(['name', 'accountName', 'amountMinor', 'expectedCloseDate', 'stage', 'updatedAt']).catch('updatedAt'),
  direction: z.enum(['asc', 'desc']).catch('desc'),
})

export type OpportunityListSearch = z.infer<typeof opportunityListSearchSchema>
