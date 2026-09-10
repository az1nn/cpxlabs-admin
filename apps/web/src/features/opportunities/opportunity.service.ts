import type {
  ApiErrorCode,
  ApiErrorEnvelope,
  OpportunityCreateInput,
  OpportunityDto,
  OpportunityListQuery,
  OpportunityListResponse,
  OpportunityStage,
  OpportunityTransitionInput,
} from '@cpxlabs-admin/contracts'

export class OpportunityServiceError extends Error {
  readonly status: number
  readonly code: ApiErrorCode
  readonly details: unknown
  readonly requestId?: string

  constructor(options: {
    status: number
    code: ApiErrorCode
    message: string
    details?: unknown
    requestId?: string
  }) {
    super(options.message)
    this.name = 'OpportunityServiceError'
    this.status = options.status
    this.code = options.code
    this.details = options.details
    if (options.requestId !== undefined) this.requestId = options.requestId
  }
}

export interface OpportunityService {
  list(query: OpportunityListQuery): Promise<OpportunityListResponse>
  get(id: string): Promise<OpportunityDto>
  create(input: OpportunityCreateInput): Promise<OpportunityDto>
  transition(id: string, input: OpportunityTransitionInput): Promise<OpportunityDto>
}

type FetchLike = typeof fetch

async function parseError(response: Response): Promise<OpportunityServiceError> {
  let envelope: ApiErrorEnvelope | undefined
  try {
    envelope = (await response.json()) as ApiErrorEnvelope
  } catch {
    // Non-JSON upstream failures still map to a stable domain service error.
  }

  return new OpportunityServiceError({
    status: response.status,
    code: envelope?.error.code ?? 'unknown',
    message: envelope?.error.message ?? `Request failed with status ${response.status}`,
    ...(envelope?.error.details !== undefined ? { details: envelope.error.details } : {}),
    ...(envelope?.error.requestId !== undefined ? { requestId: envelope.error.requestId } : {}),
  })
}

async function request<T>(fetcher: FetchLike, input: string, init?: RequestInit): Promise<T> {
  const response = await fetcher(input, {
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
    ...init,
  })

  if (!response.ok) throw await parseError(response)
  return response.json() as Promise<T>
}

function listUrl(baseUrl: string, query: OpportunityListQuery) {
  const params = new URLSearchParams()
  params.set('page', String(query.page ?? 1))
  params.set('pageSize', String(query.pageSize ?? 25))
  if (query.search) params.set('search', query.search)
  if (query.sort) params.set('sort', query.sort)
  if (query.direction) params.set('direction', query.direction)
  if (query.stage) params.set('filter.stage', query.stage)
  return `${baseUrl}/opportunities?${params.toString()}`
}

export function createHttpOpportunityService(options: {
  baseUrl: string
  fetch?: FetchLike
}): OpportunityService {
  const fetcher = options.fetch ?? globalThis.fetch.bind(globalThis)
  const baseUrl = options.baseUrl.replace(/\/$/, '')

  return {
    list(query) {
      return request<OpportunityListResponse>(fetcher, listUrl(baseUrl, query))
    },
    get(id) {
      return request<OpportunityDto>(fetcher, `${baseUrl}/opportunities/${encodeURIComponent(id)}`)
    },
    create(input) {
      return request<OpportunityDto>(fetcher, `${baseUrl}/opportunities`, {
        method: 'POST',
        body: JSON.stringify(input),
      })
    },
    transition(id, input) {
      return request<OpportunityDto>(
        fetcher,
        `${baseUrl}/opportunities/${encodeURIComponent(id)}/commands/transition`,
        { method: 'POST', body: JSON.stringify(input) },
      )
    },
  }
}

function allowedTargets(stage: OpportunityStage): readonly OpportunityStage[] {
  switch (stage) {
    case 'qualification': return ['discovery', 'lost']
    case 'discovery': return ['proposal', 'lost']
    case 'proposal': return ['negotiation', 'lost']
    case 'negotiation': return ['won', 'lost']
    case 'won':
    case 'lost':
      return []
  }
}

function compareValue(left: string | number, right: string | number) {
  return left < right ? -1 : left > right ? 1 : 0
}

export function createDemoOpportunityService(seed?: readonly OpportunityDto[]): OpportunityService {
  let rows: OpportunityDto[] = seed ? [...seed] : [
    {
      id: 'opp_demo_001',
      name: 'Enterprise Renewal',
      accountName: 'Acme Brasil',
      amountMinor: 12_500_000,
      currency: 'BRL',
      expectedCloseDate: '2026-11-30',
      stage: 'proposal',
      version: 3,
      lossReason: null,
      createdAt: '2026-09-01T12:00:00.000Z',
      updatedAt: '2026-09-09T12:00:00.000Z',
    },
  ]

  const getRow = (id: string) => {
    const row = rows.find((item) => item.id === id)
    if (!row) throw new OpportunityServiceError({ status: 404, code: 'not_found', message: 'Opportunity not found' })
    return row
  }

  return {
    async list(query) {
      const page = query.page ?? 1
      const pageSize = query.pageSize ?? 25
      const needle = query.search?.trim().toLowerCase()
      let visible = rows.filter((row) =>
        (!needle || row.name.toLowerCase().includes(needle) || row.accountName.toLowerCase().includes(needle)) &&
        (!query.stage || row.stage === query.stage),
      )
      const sort = query.sort ?? 'updatedAt'
      const direction = query.direction ?? 'desc'
      visible = [...visible].sort((left, right) => {
        const result = compareValue(left[sort], right[sort])
        return direction === 'asc' ? result : -result
      })
      return {
        data: visible.slice((page - 1) * pageSize, page * pageSize),
        total: visible.length,
      }
    },
    async get(id) {
      return getRow(id)
    },
    async create(input) {
      const now = new Date().toISOString()
      const created: OpportunityDto = {
        id: crypto.randomUUID(),
        ...input,
        currency: input.currency.trim().toUpperCase(),
        stage: 'qualification',
        version: 1,
        lossReason: null,
        createdAt: now,
        updatedAt: now,
      }
      rows = [created, ...rows]
      return created
    },
    async transition(id, input) {
      const current = getRow(id)
      if (current.version !== input.expectedVersion) {
        throw new OpportunityServiceError({
          status: 409,
          code: 'WORKFLOW_CONFLICT',
          message: 'The opportunity changed since it was loaded',
          details: { expectedVersion: input.expectedVersion, currentVersion: current.version },
        })
      }
      if (!allowedTargets(current.stage).includes(input.targetStage)) {
        throw new OpportunityServiceError({
          status: 409,
          code: 'WORKFLOW_INVALID_TRANSITION',
          message: 'The requested opportunity transition is not allowed',
        })
      }
      const lossReason = input.targetStage === 'lost' ? input.lossReason?.trim() : undefined
      if (input.targetStage === 'lost' && !lossReason) {
        throw new OpportunityServiceError({
          status: 409,
          code: 'WORKFLOW_INVALID_TRANSITION',
          message: 'A loss reason is required when an opportunity is lost',
        })
      }
      const updated: OpportunityDto = {
        ...current,
        stage: input.targetStage,
        version: current.version + 1,
        lossReason: input.targetStage === 'lost' ? lossReason ?? null : null,
        updatedAt: new Date().toISOString(),
      }
      rows = rows.map((row) => row.id === id ? updated : row)
      return updated
    },
  }
}
