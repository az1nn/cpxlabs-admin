const statusSchema = { type: 'string', enum: ['lead', 'active', 'inactive'] } as const

export const customerSchema = {
  type: 'object',
  additionalProperties: false,
  required: ['id', 'name', 'email', 'company', 'status', 'updatedAt'],
  properties: {
    id: { type: 'string' },
    name: { type: 'string' },
    email: { type: 'string' },
    company: { type: 'string' },
    status: statusSchema,
    updatedAt: { type: 'string' },
  },
} as const

export const customerInputSchema = {
  type: 'object',
  additionalProperties: false,
  required: ['name', 'email', 'company', 'status'],
  properties: {
    name: { type: 'string', minLength: 1 },
    email: { type: 'string', format: 'email' },
    company: { type: 'string', minLength: 1 },
    status: statusSchema,
  },
} as const

export const customerParamsSchema = {
  type: 'object',
  additionalProperties: false,
  required: ['customerId'],
  properties: {
    customerId: { type: 'string', minLength: 1 },
  },
} as const

export const customerListQuerySchema = {
  type: 'object',
  additionalProperties: false,
  required: ['page', 'pageSize'],
  properties: {
    page: { type: 'integer', minimum: 1 },
    pageSize: { type: 'integer', minimum: 1, maximum: 100 },
    search: { type: 'string' },
    sort: { type: 'string', enum: ['name', 'company', 'status', 'updatedAt'] },
    direction: { type: 'string', enum: ['asc', 'desc'] },
    'filter.status': statusSchema,
  },
} as const

export const customerListResponseSchema = {
  type: 'object',
  additionalProperties: false,
  required: ['data', 'total'],
  properties: {
    data: { type: 'array', items: customerSchema },
    total: { type: 'integer', minimum: 0 },
  },
} as const
