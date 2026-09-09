import { loadEnvFile } from 'node:process'

import { startTelemetry } from './platform/observability/telemetry.js'

try {
  loadEnvFile('.env')
} catch (error) {
  const code =
    typeof error === 'object' && error !== null && 'code' in error
      ? error.code
      : undefined

  if (code !== 'ENOENT') {
    throw error
  }
}

const telemetry = await startTelemetry()

const [
  { buildApp },
  { PrismaCustomerMutationService },
  { PrismaCustomerRepository },
  { PrismaOpportunityRepository },
  { PrismaOpportunityWorkflowService },
  { PrismaAuditRepository },
  { createAuth },
  { createRequestContextResolver },
  { PrismaAccessProfileRepository },
  { createAuthorizationGuards },
  { createPrismaClient },
] = await Promise.all([
  import('./app.js'),
  import('./modules/customers/customer.mutation-service.js'),
  import('./modules/customers/customer.prisma-repository.js'),
  import('./modules/opportunities/opportunity.prisma-repository.js'),
  import('./modules/opportunities/opportunity.workflow-service.js'),
  import('./platform/audit/audit.prisma-repository.js'),
  import('./platform/authentication/auth.js'),
  import('./platform/authentication/session.js'),
  import('./platform/authorization/access-profile.repository.js'),
  import('./platform/authorization/guards.js'),
  import('./platform/database/prisma.js'),
])

const databaseUrl = process.env.DATABASE_URL?.trim()
if (!databaseUrl) {
  await telemetry.shutdown()
  throw new Error('DATABASE_URL is required by the authenticated reference API')
}

const secret = process.env.BETTER_AUTH_SECRET?.trim()
if (!secret || secret.length < 32) {
  await telemetry.shutdown()
  throw new Error('BETTER_AUTH_SECRET must contain at least 32 characters')
}

const port = Number(process.env.PORT ?? 3001)
const host = process.env.HOST ?? '0.0.0.0'
const betterAuthUrl = process.env.BETTER_AUTH_URL?.trim() ?? `http://127.0.0.1:${port}`
const appOrigin = process.env.APP_ORIGIN?.trim() ?? 'http://127.0.0.1:4173'

const prisma = createPrismaClient(databaseUrl)
const customerRepository = new PrismaCustomerRepository(prisma)
const auditRepository = new PrismaAuditRepository(prisma)
const customerMutationService = new PrismaCustomerMutationService(prisma)
const opportunityRepository = new PrismaOpportunityRepository(prisma)
const opportunityWorkflow = new PrismaOpportunityWorkflowService(prisma)
const accessProfiles = new PrismaAccessProfileRepository(prisma)
const auth = createAuth({
  prisma,
  baseURL: betterAuthUrl,
  secret,
  trustedOrigins: [appOrigin],
})
const resolveRequestContext = createRequestContextResolver({ auth, accessProfiles })
const authorization = createAuthorizationGuards(resolveRequestContext)

const app = buildApp({
  customerRepository,
  customerMutationService,
  opportunityRepository,
  opportunityWorkflow,
  auditRepository,
  authorization,
  authentication: {
    auth,
    resolveRequestContext,
  },
})

app.addHook('onClose', async () => {
  await prisma.$disconnect()
  await telemetry.shutdown()
})

try {
  await app.listen({ port, host })
} catch (error) {
  app.log.error(error)
  await app.close().catch(() => undefined)
  await telemetry.shutdown().catch(() => undefined)
  process.exit(1)
}
