import { z } from 'zod'

export const customerListSearchSchema = z.object({
  page: z.coerce.number().int().positive().catch(1),
  pageSize: z.coerce.number().int().min(10).max(100).catch(25),
  search: z.string().catch(''),
  status: z.enum(['all', 'lead', 'active', 'inactive']).catch('all'),
  sort: z.enum(['name', 'company', 'status', 'updatedAt']).catch('updatedAt'),
  direction: z.enum(['asc', 'desc']).catch('desc'),
})

export type CustomerListSearch = z.infer<typeof customerListSearchSchema>
