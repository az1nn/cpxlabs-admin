import { loadEnvFile } from 'node:process'

import { buildApp } from './app.js'
import { PrismaCustomerMutationService } from './modules/customers/customer.mutation-service.js'
import { PrismaCustomerRepository } from './modules/customers/customer.prisma-repository.js'
import { PrismaAuditRepository } from './platform/audit/audit.prisma-repository.js'
import { createAuth } from './platform/authentication/auth.js'
import { createRequestContextResolver } from './platform/authentication/session.js'
import { PrismaAccessProfileRepository } from './platform/authorization/access-profile.repository.js'
import { createAuthorizationGuards } from './platform/authorization/guards.js'
import { createPrismaClient } from './platform/database/prisma.js'

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

const databaseUrl = process.env.DATABASE_URL?.trim()
if (!databaseUrl) {
  throw new Error('DATABASE_URL is required by the authenticated reference API')
}

const secret = process.env.BETTER_AUTH_SECRET?.trim()
if (!secret || secret.length < 32) {
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
  auditRepository,
  authorization,
  authentication: {
    auth,
    resolveRequestContext,
  },
})

app.addHook('onClose', async () => {
  await prisma.$disconnect()
})

try {
  await app.listen({ port, host })
} catch (error) {
  app.log.error(error)
  process.exit(1)
}
