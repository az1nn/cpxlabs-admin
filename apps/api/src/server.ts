import { loadEnvFile } from 'node:process'

import { buildApp } from './app.js'
import { InMemoryCustomerRepository } from './modules/customers/customer.repository.js'
import { PrismaCustomerRepository } from './modules/customers/customer.prisma-repository.js'
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
const prisma = databaseUrl ? createPrismaClient(databaseUrl) : undefined
const customerRepository = prisma
  ? new PrismaCustomerRepository(prisma)
  : new InMemoryCustomerRepository()

const app = buildApp({ customerRepository })
const port = Number(process.env.PORT ?? 3001)
const host = process.env.HOST ?? '0.0.0.0'

if (prisma) {
  app.addHook('onClose', async () => {
    await prisma.$disconnect()
  })
}

try {
  await app.listen({ port, host })
} catch (error) {
  app.log.error(error)
  process.exit(1)
}
