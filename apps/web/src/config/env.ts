import { z } from 'zod'

const envSchema = z.object({
  VITE_DATA_PROVIDER: z.enum(['demo', 'http']).default('demo'),
  VITE_API_BASE_URL: z.string().trim().default('/api'),
  VITE_AUTH_MODE: z.enum(['demo', 'server']).optional(),
})

const parsed = envSchema.safeParse(import.meta.env)

if (!parsed.success) {
  throw new Error(`Invalid application environment: ${z.prettifyError(parsed.error)}`)
}

if (parsed.data.VITE_DATA_PROVIDER === 'http' && !parsed.data.VITE_API_BASE_URL) {
  throw new Error('VITE_API_BASE_URL is required when VITE_DATA_PROVIDER=http')
}

export const env = {
  ...parsed.data,
  VITE_AUTH_MODE:
    parsed.data.VITE_AUTH_MODE ??
    (parsed.data.VITE_DATA_PROVIDER === 'demo' ? 'demo' : 'server'),
} as const
