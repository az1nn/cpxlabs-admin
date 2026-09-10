import { z } from 'zod'

import { majorAmountToMinorUnits } from './opportunity-money'

export const opportunityFormSchema = z.object({
  name: z.string().trim().min(1, 'Name is required').max(160),
  accountName: z.string().trim().min(1, 'Account name is required').max(160),
  amount: z
    .string()
    .trim()
    .min(1, 'Amount is required')
    .regex(/^\d+(?:\.\d+)?$/, 'Use a non-negative decimal amount with a dot separator'),
  currency: z.string().trim().toUpperCase().regex(/^[A-Z]{3}$/, 'Use a three-letter currency code'),
  expectedCloseDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Expected close date is required'),
}).superRefine((values, context) => {
  try {
    majorAmountToMinorUnits(values.amount, values.currency)
  } catch (error) {
    context.addIssue({
      code: 'custom',
      path: ['amount'],
      message: error instanceof Error ? error.message : 'Amount cannot be represented in minor units',
    })
  }
})

export type OpportunityFormValues = z.infer<typeof opportunityFormSchema>
