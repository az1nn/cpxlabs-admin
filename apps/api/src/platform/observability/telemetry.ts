import FastifyOtelInstrumentation from '@fastify/otel'
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'
import { HttpInstrumentation } from '@opentelemetry/instrumentation-http'
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics'
import { NodeSDK } from '@opentelemetry/sdk-node'

export type TelemetryConfig =
  | { enabled: false }
  | {
      enabled: true
      endpoint: string
      serviceName: string
    }

export type TelemetryHandle = {
  enabled: boolean
  shutdown(): Promise<void>
}

export type TelemetrySdk = {
  start(): void
  shutdown(): Promise<void>
}

export type TelemetrySdkFactory = (config: Extract<TelemetryConfig, { enabled: true }>) => TelemetrySdk

function parseEnabled(value: string | undefined) {
  return ['1', 'true', 'yes', 'on'].includes(value?.trim().toLowerCase() ?? '')
}

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, '')
}

export function resolveTelemetryConfig(env: NodeJS.ProcessEnv = process.env): TelemetryConfig {
  if (!parseEnabled(env.OTEL_ENABLED)) {
    return { enabled: false }
  }

  return {
    enabled: true,
    endpoint: trimTrailingSlash(
      env.OTEL_EXPORTER_OTLP_ENDPOINT?.trim() || 'http://127.0.0.1:4318',
    ),
    serviceName: env.OTEL_SERVICE_NAME?.trim() || 'cpxlabs-admin-api',
  }
}

function createTelemetrySdk(
  config: Extract<TelemetryConfig, { enabled: true }>,
): TelemetrySdk {
  const traceExporter = new OTLPTraceExporter({
    url: `${config.endpoint}/v1/traces`,
  })
  const metricReader = new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: `${config.endpoint}/v1/metrics`,
    }),
  })

  return new NodeSDK({
    serviceName: config.serviceName,
    traceExporter,
    metricReaders: [metricReader],
    instrumentations: [
      new HttpInstrumentation(),
      new FastifyOtelInstrumentation({
        registerOnInitialization: true,
        requestHook(span, request) {
          span.setAttribute('cpx.request_id', request.id)
        },
      }),
    ],
  })
}

export async function startTelemetry(
  env: NodeJS.ProcessEnv = process.env,
  factory: TelemetrySdkFactory = createTelemetrySdk,
  onError: (error: unknown) => void = (error) => console.error('OpenTelemetry bootstrap failed', error),
): Promise<TelemetryHandle> {
  const config = resolveTelemetryConfig(env)
  if (!config.enabled) {
    return {
      enabled: false,
      async shutdown() {},
    }
  }

  try {
    const sdk = factory(config)
    sdk.start()
    return {
      enabled: true,
      shutdown: () => sdk.shutdown(),
    }
  } catch (error) {
    onError(error)
    return {
      enabled: false,
      async shutdown() {},
    }
  }
}
