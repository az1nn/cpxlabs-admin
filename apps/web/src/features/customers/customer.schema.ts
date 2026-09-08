import { z } from 'zod'

export const customerInputSchema = z.object({
  name: z.string().trim().min(2, 'Name must contain at least 2 characters.').max(120),
  email: z.string().trim().email('Enter a valid email address.').max(180),
  company: z.string().trim().min(2, 'Company must contain at least 2 characters.').max(120),
  status: z.enum(['lead', 'active', 'inactive']),
})
