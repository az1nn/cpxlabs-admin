const opportunityStages = ['qualification', 'discovery', 'proposal', 'negotiation', 'won', 'lost'] as const

export const opportunitySchema = {
  type: 'object',
  additionalProperties: false,
  required: [
    'id', 'name', 'accountName', 'amountMinor', 'currency', 'expectedCloseDate',
    'stage', 'version', 'lossReason', 'createdAt', 'updatedAt',
  ],
  properties: {
    id: { type: 'string' },
    name: { type: 'string' },
    accountName: { type: 'string' },
    amountMinor: { type: 'integer', minimum: 0 },
    currency: { type: 'string', pattern: '^[A-Z]{3}$' },
    expectedCloseDate: { type: 'string', pattern: '^\\d{4}-\\d{2}-\\d{2}$' },
    stage: { type: 'string', enum: [...opportunityStages] },
    version: { type: 'integer', minimum: 1 },
    lossReason: { anyOf: [{ type: 'string' }, { type: 'null' }] },
    createdAt: { type: 'string', format: 'date-time' },
    updatedAt: { type: 'string', format: 'date-time' },
  },
} as const

export const opportunityCreateSchema = {
  type: 'object',
  additionalProperties: false,
  required: ['name', 'accountName', 'amountMinor', 'currency', 'expectedCloseDate'],
  properties: {
    name: { type: 'string', minLength: 1, maxLength: 160 },
    accountName: { type: 'string', minLength: 1, maxLength: 160 },
    amountMinor: { type: 'integer', minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
    currency: { type: 'string', pattern: '^[A-Z]{3}$' },
    expectedCloseDate: { type: 'string', pattern: '^\\d{4}-\\d{2}-\\d{2}$' },
  },
} as const

export const opportunityTransitionSchema = {
  type: 'object',
  additionalProperties: false,
  required: ['targetStage', 'expectedVersion'],
  properties: {
    targetStage: { type: 'string', enum: [...opportunityStages] },
    expectedVersion: { type: 'integer', minimum: 1 },
    lossReason: { type: 'string', maxLength: 500 },
  },
} as const

export const opportunityParamsSchema = {
  type: 'object',
  additionalProperties: false,
  required: ['opportunityId'],
  properties: { opportunityId: { type: 'string', minLength: 1 } },
} as const

export const opportunityListQuerySchema = {
  type: 'object',
  additionalProperties: false,
  properties: {
    page: { type: 'integer', minimum: 1, default: 1 },
    pageSize: { type: 'integer', minimum: 1, maximum: 100, default: 25 },
    search: { type: 'string' },
    sort: {
      type: 'string',
      enum: ['name', 'accountName', 'amountMinor', 'expectedCloseDate', 'stage', 'updatedAt'],
    },
    direction: { type: 'string', enum: ['asc', 'desc'] },
    'filter.stage': { type: 'string', enum: [...opportunityStages] },
  },
} as const

export const opportunityListResponseSchema = {
  type: 'object',
  additionalProperties: false,
  required: ['data', 'total'],
  properties: {
    data: { type: 'array', items: opportunitySchema },
    total: { type: 'integer', minimum: 0 },
  },
} as const
