import { env } from '../../config/env'
import {
  createDemoOpportunityService,
  createHttpOpportunityService,
  type OpportunityService,
} from './opportunity.service'

export function createAppOpportunityService(): OpportunityService {
  if (env.VITE_DATA_PROVIDER === 'http') {
    return createHttpOpportunityService({ baseUrl: env.VITE_API_BASE_URL })
  }

  return createDemoOpportunityService()
}

export const appOpportunityService = createAppOpportunityService()
