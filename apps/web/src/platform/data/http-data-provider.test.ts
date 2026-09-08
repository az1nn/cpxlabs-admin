import { describe, expect, it, vi } from 'vitest'

import { createHttpDataProvider } from './http-data-provider'

describe('HttpDataProvider', () => {
  it('serializes list state into the HTTP contract', async () => {
    const fetcher = vi.fn(async (_input: string | URL | Request) =>
      new Response(JSON.stringify({ data: [], total: 0 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    const provider = createHttpDataProvider({ baseUrl: '/api', fetch: fetcher as typeof fetch })

    await provider.getList('customers', {
      page: 2,
      pageSize: 25,
      search: 'acme',
      sort: { field: 'name', direction: 'desc' },
      filters: { status: 'active' },
    })

    const requestUrl = String(fetcher.mock.calls[0]?.[0])
    const url = new URL(requestUrl)
    expect(url.pathname).toBe('/api/customers')
    expect(Object.fromEntries(url.searchParams)).toEqual({
      page: '2',
      pageSize: '25',
      search: 'acme',
      sort: 'name',
      direction: 'desc',
      'filter.status': 'active',
    })
  })

  it('maps API error envelopes to a stable application error', async () => {
    const fetcher = vi.fn(async (_input: string | URL | Request) =>
      new Response(
        JSON.stringify({
          error: {
            code: 'authorization',
            message: 'Forbidden',
            requestId: 'req_123',
          },
        }),
        { status: 403, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    const provider = createHttpDataProvider({ baseUrl: '/api', fetch: fetcher as typeof fetch })

    const action = provider.getOne('customers', 'cus_001')

    await expect(action).rejects.toMatchObject({
      status: 403,
      code: 'authorization',
      message: 'Forbidden',
      requestId: 'req_123',
    })
  })
})
