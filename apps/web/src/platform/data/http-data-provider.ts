import type {
  ApiErrorEnvelope,
  DataProvider,
  ListParams,
  ListResult,
} from '@cpxlabs-admin/contracts'

export class HttpDataProviderError extends Error {
  readonly status: number
  readonly code: string
  readonly details: unknown
  readonly requestId?: string

  constructor(options: {
    status: number
    code: string
    message: string
    details?: unknown
    requestId?: string
  }) {
    super(options.message)
    this.name = 'HttpDataProviderError'
    this.status = options.status
    this.code = options.code
    this.details = options.details
    if (options.requestId !== undefined) {
      this.requestId = options.requestId
    }
  }
}

type FetchLike = typeof fetch

type HttpDataProviderOptions = {
  baseUrl: string
  fetch?: FetchLike
}

function buildListUrl(baseUrl: string, resource: string, params: ListParams): string {
  const url = new URL(`${baseUrl}/${encodeURIComponent(resource)}`, window.location.origin)
  url.searchParams.set('page', String(params.page))
  url.searchParams.set('pageSize', String(params.pageSize))

  if (params.search) {
    url.searchParams.set('search', params.search)
  }

  if (params.sort) {
    url.searchParams.set('sort', params.sort.field)
    url.searchParams.set('direction', params.sort.direction)
  }

  for (const [key, value] of Object.entries(params.filters ?? {})) {
    if (value !== undefined && value !== null) {
      url.searchParams.set(`filter.${key}`, String(value))
    }
  }

  return url.toString()
}

async function parseError(response: Response): Promise<HttpDataProviderError> {
  let envelope: ApiErrorEnvelope | undefined

  try {
    envelope = (await response.json()) as ApiErrorEnvelope
  } catch {
    // Non-JSON upstream errors are mapped to the stable application error type below.
  }

  return new HttpDataProviderError({
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

  if (!response.ok) {
    throw await parseError(response)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export function createHttpDataProvider({
  baseUrl,
  fetch: fetchOverride,
}: HttpDataProviderOptions): DataProvider {
  const fetcher = fetchOverride ?? globalThis.fetch.bind(globalThis)
  const normalizedBaseUrl = baseUrl.replace(/\/$/, '')

  return {
    getList<T>(resource: string, params: ListParams): Promise<ListResult<T>> {
      return request<ListResult<T>>(fetcher, buildListUrl(normalizedBaseUrl, resource, params))
    },

    getOne<T>(resource: string, id: string): Promise<T> {
      return request<T>(fetcher, `${normalizedBaseUrl}/${encodeURIComponent(resource)}/${encodeURIComponent(id)}`)
    },

    create<T>(resource: string, input: unknown): Promise<T> {
      return request<T>(fetcher, `${normalizedBaseUrl}/${encodeURIComponent(resource)}`, {
        method: 'POST',
        body: JSON.stringify(input),
      })
    },

    update<T>(resource: string, id: string, input: unknown): Promise<T> {
      return request<T>(fetcher, `${normalizedBaseUrl}/${encodeURIComponent(resource)}/${encodeURIComponent(id)}`, {
        method: 'PATCH',
        body: JSON.stringify(input),
      })
    },

    delete(resource: string, id: string): Promise<void> {
      return request<void>(fetcher, `${normalizedBaseUrl}/${encodeURIComponent(resource)}/${encodeURIComponent(id)}`, {
        method: 'DELETE',
      })
    },
  }
}
