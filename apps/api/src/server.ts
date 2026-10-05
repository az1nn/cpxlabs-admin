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
  { createClerkIdentityProvider, registerClerkAuthentication },
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
  import('./platform/authentication/clerk-identity-provider.js'),
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

const clerkPublishableKey = process.env.CLERK_PUBLISHABLE_KEY?.trim()
if (!clerkPublishableKey) {
  await telemetry.shutdown()
  throw new Error('CLERK_PUBLISHABLE_KEY is required by the authenticated reference API')
}

const clerkSecretKey = process.env.CLERK_SECRET_KEY?.trim()
if (!clerkSecretKey) {
  await telemetry.shutdown()
  throw new Error('CLERK_SECRET_KEY is required by the authenticated reference API')
}

const port = Number(process.env.PORT ?? 3001)
const host = process.env.HOST ?? '0.0.0.0'

const prisma = createPrismaClient(databaseUrl)
const customerRepository = new PrismaCustomerRepository(prisma)
const auditRepository = new PrismaAuditRepository(prisma)
const customerMutationService = new PrismaCustomerMutationService(prisma)
const opportunityRepository = new PrismaOpportunityRepository(prisma)
const opportunityWorkflow = new PrismaOpportunityWorkflowService(prisma)
const accessProfiles = new PrismaAccessProfileRepository(prisma)
const identityProvider = createClerkIdentityProvider()
const resolveRequestContext = createRequestContextResolver({
  identityProvider,
  accessProfiles,
})
const authorization = createAuthorizationGuards(resolveRequestContext)

const app = buildApp({
  customerRepository,
  customerMutationService,
  opportunityRepository,
  opportunityWorkflow,
  auditRepository,
  authorization,
  authentication: {
    register: (instance) =>
      registerClerkAuthentication(instance, {
        publishableKey: clerkPublishableKey,
        secretKey: clerkSecretKey,
      }),
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
