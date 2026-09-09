import { createPrincipal } from '@cpxlabs-admin/authorization'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { buildApp } from '../../app.js'
import { InMemoryAuditRepository } from '../audit/audit.repository.js'
import { createAuthorizationGuards } from '../authorization/guards.js'
import { startTelemetry, type TelemetrySdkFactory } from './telemetry.js'

const apps: ReturnType<typeof buildApp>[] = []
const principal = createPrincipal({
  id: 'telemetry-admin',
  email: 'telemetry-admin@example.com',
  name: 'Telemetry Admin',
  role: 'admin',
})
const authorization = createAuthorizationGuards(async () => ({ principal }))

const input = {
  name: 'Telemetry Customer',
  company: 'CPX Labs',
  status: 'lead' as const,
}

afterEach(async () => {
  await Promise.all(apps.splice(0).map((app) => app.close()))
})

async function executeMutation(audit: InMemoryAuditRepository, email: string) {
  const app = buildApp({ auditRepository: audit, authorization })
  apps.push(app)
  const response = await app.inject({
    method: 'POST',
    url: '/api/customers',
    payload: { ...input, email },
  })
  expect(response.statusCode).toBe(201)
  const events = await audit.list({ limit: 100 })
  expect(events.data).toHaveLength(1)
}

describe('telemetry isolation from domain correctness', () => {
  it('keeps customer and audit behavior correct when telemetry is disabled', async () => {
    const factory = vi.fn<TelemetrySdkFactory>()
    const telemetry = await startTelemetry({}, factory)
    const audit = new InMemoryAuditRepository()

    await executeMutation(audit, 'telemetry-disabled@example.com')

    expect(telemetry.enabled).toBe(false)
    expect(factory).not.toHaveBeenCalled()
    await telemetry.shutdown()
  })

  it('keeps customer and audit behavior correct when telemetry is enabled', async () => {
    const factory = vi.fn<TelemetrySdkFactory>(() => ({
      start: vi.fn(),
      shutdown: vi.fn(async () => undefined),
    }))
    const telemetry = await startTelemetry({ OTEL_ENABLED: 'true' }, factory)
    const audit = new InMemoryAuditRepository()

    await executeMutation(audit, 'telemetry-enabled@example.com')

    expect(telemetry.enabled).toBe(true)
    await telemetry.shutdown()
  })

  it('keeps mandatory domain and audit behavior correct when telemetry bootstrap fails', async () => {
    const telemetry = await startTelemetry(
      { OTEL_ENABLED: 'true' },
      () => {
        throw new Error('collector unavailable')
      },
      () => undefined,
    )
    const audit = new InMemoryAuditRepository()

    await executeMutation(audit, 'telemetry-failed@example.com')

    expect(telemetry.enabled).toBe(false)
    await telemetry.shutdown()
  })
})
