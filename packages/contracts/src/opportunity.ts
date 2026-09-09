export type OpportunityStage =
  | 'qualification'
  | 'discovery'
  | 'proposal'
  | 'negotiation'
  | 'won'
  | 'lost'

export type OpportunityDto = {
  id: string
  name: string
  accountName: string
  amountMinor: number
  currency: string
  expectedCloseDate: string
  stage: OpportunityStage
  version: number
  lossReason: string | null
  createdAt: string
  updatedAt: string
}

export type OpportunityCreateInput = Pick<
  OpportunityDto,
  'name' | 'accountName' | 'amountMinor' | 'currency' | 'expectedCloseDate'
>

export type OpportunityTransitionInput = {
  targetStage: OpportunityStage
  expectedVersion: number
  lossReason?: string
}

export type OpportunityListQuery = {
  page?: number
  pageSize?: number
  search?: string
  sort?: 'name' | 'accountName' | 'amountMinor' | 'expectedCloseDate' | 'stage' | 'updatedAt'
  direction?: 'asc' | 'desc'
  stage?: OpportunityStage
}

export type OpportunityListResponse = {
  data: OpportunityDto[]
  total: number
}
