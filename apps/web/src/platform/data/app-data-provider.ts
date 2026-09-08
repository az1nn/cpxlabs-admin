import type { DataProvider } from '@cpxlabs-admin/contracts'

import { env } from '../../config/env'
import { demoDataProvider } from './demo-data-provider'
import { createHttpDataProvider } from './http-data-provider'

export function createAppDataProvider(): DataProvider {
  if (env.VITE_DATA_PROVIDER === 'http') {
    return createHttpDataProvider({ baseUrl: env.VITE_API_BASE_URL })
  }

  return demoDataProvider
}

export const appDataProvider = createAppDataProvider()
