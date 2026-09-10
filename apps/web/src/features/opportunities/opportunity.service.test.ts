import { describe, expect, it, vi } from 'vitest'

import {
  createDemoOpportunityService,
  createHttpOpportunityService,
  OpportunityServiceError,
} from './opportunity.service'

describe('OpportunityService', () => {
  it('serializes bounded list state independently from DataProvider', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({ data: [], total: 0 }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })) as unknown as typeof fetch
    const service = createHttpOpportunityService({ baseUrl: '/api/', fetch: fetcher })

    await service.list({
      page: 2,
      pageSize: 50,
      search: 'renewal',
      stage: 'proposal',
      sort: 'amountMinor',
      direction: 'asc',
    })

    expect(fetcher).toHaveBeenCalledOnce()
    const [url, init] = vi.mocked(fetcher).mock.calls[0]!
    expect(url).toBe('/api/opportunities?page=2&pageSize=50&search=renewal&sort=amountMinor&direction=asc&filter.stage=proposal')
    expect(init).toMatchObject({ credentials: 'include' })
  })

  it('posts workflow commands to the explicit command endpoint', async () => {
    const opportunity = {
      id: 'opp_1',
      name: 'Renewal',
      accountName: 'Acme',
      amountMinor: 10000,
      currency: 'BRL',
      expectedCloseDate: '2026-12-01',
      stage: 'discovery' as const,
      version: 2,
      lossReason: null,
      createdAt: '2026-09-09T12:00:00.000Z',
      updatedAt: '2026-09-09T12:05:00.000Z',
    }
    const fetcher = vi.fn(async () => new Response(JSON.stringify(opportunity), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })) as unknown as typeof fetch
    const service = createHttpOpportunityService({ baseUrl: '/api', fetch: fetcher })

    await service.transition('opp_1', { targetStage: 'discovery', expectedVersion: 1 })

    expect(fetcher).toHaveBeenCalledWith(
      '/api/opportunities/opp_1/commands/transition',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ targetStage: 'discovery', expectedVersion: 1 }),
      }),
    )
  })

  it('preserves WORKFLOW_CONFLICT details for stale-state recovery', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      error: {
        code: 'WORKFLOW_CONFLICT',
        message: 'The opportunity changed since it was loaded',
        details: { expectedVersion: 2, currentVersion: 3 },
        requestId: 'request-123',
      },
    }), {
      status: 409,
      headers: { 'Content-Type': 'application/json' },
    })) as unknown as typeof fetch
    const service = createHttpOpportunityService({ baseUrl: '/api', fetch: fetcher })

    await expect(
      service.transition('opp_1', { targetStage: 'proposal', expectedVersion: 2 }),
    ).rejects.toMatchObject({
      name: 'OpportunityServiceError',
      status: 409,
      code: 'WORKFLOW_CONFLICT',
      details: { expectedVersion: 2, currentVersion: 3 },
      requestId: 'request-123',
    })
  })

  it('enforces optimistic versioning in demo mode too', async () => {
    const service = createDemoOpportunityService()
    const current = await service.get('opp_demo_001')
    expect(current.version).toBe(3)

    const stale = service.transition(current.id, {
      targetStage: 'negotiation',
      expectedVersion: 2,
    })

    await expect(stale).rejects.toBeInstanceOf(OpportunityServiceError)
    await expect(stale).rejects.toMatchObject({ code: 'WORKFLOW_CONFLICT' })
  })
})
