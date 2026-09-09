import { describe, expect, it, vi } from 'vitest'

import { resolveTelemetryConfig, startTelemetry, type TelemetrySdkFactory } from './telemetry.js'

describe('telemetry configuration', () => {
  it('is disabled by default and does not initialize an SDK', async () => {
    const factory = vi.fn<TelemetrySdkFactory>()
    expect(resolveTelemetryConfig({})).toEqual({ enabled: false })

    const telemetry = await startTelemetry({}, factory)
    expect(telemetry.enabled).toBe(false)
    expect(factory).not.toHaveBeenCalled()
    await expect(telemetry.shutdown()).resolves.toBeUndefined()
  })

  it('normalizes an enabled OTLP configuration and manages SDK lifecycle', async () => {
    const start = vi.fn()
    const shutdown = vi.fn(async () => undefined)
    const factory = vi.fn<TelemetrySdkFactory>(() => ({ start, shutdown }))
    const env = {
      OTEL_ENABLED: 'true',
      OTEL_EXPORTER_OTLP_ENDPOINT: 'http://collector:4318/',
      OTEL_SERVICE_NAME: 'reference-api',
    }

    expect(resolveTelemetryConfig(env)).toEqual({
      enabled: true,
      endpoint: 'http://collector:4318',
      serviceName: 'reference-api',
    })

    const telemetry = await startTelemetry(env, factory)
    expect(telemetry.enabled).toBe(true)
    expect(factory).toHaveBeenCalledWith({
      enabled: true,
      endpoint: 'http://collector:4318',
      serviceName: 'reference-api',
    })
    expect(start).toHaveBeenCalledOnce()
    await telemetry.shutdown()
    expect(shutdown).toHaveBeenCalledOnce()
  })

  it('degrades to disabled telemetry if SDK bootstrap fails', async () => {
    const onError = vi.fn()
    const telemetry = await startTelemetry(
      { OTEL_ENABLED: 'true' },
      () => {
        throw new Error('bootstrap failed')
      },
      onError,
    )

    expect(telemetry.enabled).toBe(false)
    expect(onError).toHaveBeenCalledOnce()
    await expect(telemetry.shutdown()).resolves.toBeUndefined()
  })
})
