import { z } from 'zod'

export const opportunityFormSchema = z.object({
  name: z.string().trim().min(1, 'Name is required').max(160),
  accountName: z.string().trim().min(1, 'Account name is required').max(160),
  amount: z.number().finite().nonnegative('Amount must be zero or greater').max(Number.MAX_SAFE_INTEGER / 100),
  currency: z.string().trim().toUpperCase().regex(/^[A-Z]{3}$/, 'Use a three-letter currency code'),
  expectedCloseDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Expected close date is required'),
})

export type OpportunityFormValues = z.infer<typeof opportunityFormSchema>
