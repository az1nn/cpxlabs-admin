import type {
  OpportunityCreateInput,
  OpportunityDto,
  OpportunityListQuery,
  OpportunityListResponse,
  OpportunityStage,
  OpportunityTransitionInput,
} from '@cpxlabs-admin/contracts'

export type Opportunity = OpportunityDto
export type OpportunityInput = OpportunityCreateInput
export type OpportunityTransitionCommand = OpportunityTransitionInput
export type OpportunityListParams = OpportunityListQuery
export type OpportunityListResult = OpportunityListResponse
export type { OpportunityStage }
