import { loadEnvFile } from 'node:process'

import { createPrismaClient } from './prisma.js'

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

const databaseUrl =
  process.env.DATABASE_URL ??
  'postgresql://postgres:postgres@127.0.0.1:5432/cpxlabs_admin'

const prisma = createPrismaClient(databaseUrl)

try {
  await prisma.customer.upsert({
    where: { email: 'ops@acme.example' },
    update: {
      name: 'Acme Brasil',
      company: 'Acme',
      status: 'active',
    },
    create: {
      id: 'cus_001',
      name: 'Acme Brasil',
      email: 'ops@acme.example',
      company: 'Acme',
      status: 'active',
    },
  })

  await prisma.customer.upsert({
    where: { email: 'admin@northstar.example' },
    update: {
      name: 'Northstar Retail',
      company: 'Northstar',
      status: 'lead',
    },
    create: {
      id: 'cus_002',
      name: 'Northstar Retail',
      email: 'admin@northstar.example',
      company: 'Northstar',
      status: 'lead',
    },
  })
} finally {
  await prisma.$disconnect()
}
