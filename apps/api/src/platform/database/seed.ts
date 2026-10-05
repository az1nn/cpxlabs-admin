import type { ApplicationRole } from '@cpxlabs-admin/contracts'
import { loadEnvFile } from 'node:process'

import { PrismaAccessProfileRepository } from '../authorization/access-profile.repository.js'
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

async function seedCustomers() {
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
}

async function seedReferenceAccessProfiles() {
  const accessProfiles = new PrismaAccessProfileRepository(prisma)
  const configured: Array<{
    userId: string | undefined
    role: ApplicationRole
    envName: string
  }> = [
    {
      userId: process.env.SEED_CLERK_ADMIN_USER_ID?.trim(),
      role: 'admin',
      envName: 'SEED_CLERK_ADMIN_USER_ID',
    },
    {
      userId: process.env.SEED_CLERK_MANAGER_USER_ID?.trim(),
      role: 'manager',
      envName: 'SEED_CLERK_MANAGER_USER_ID',
    },
    {
      userId: process.env.SEED_CLERK_VIEWER_USER_ID?.trim(),
      role: 'viewer',
      envName: 'SEED_CLERK_VIEWER_USER_ID',
    },
  ]

  const present = configured.filter(
    (entry): entry is typeof entry & { userId: string } => Boolean(entry.userId),
  )

  if (present.length === 0) {
    console.warn(
      'Skipping reference access profiles because no SEED_CLERK_*_USER_ID is configured.',
    )
    return
  }

  for (const entry of present) {
    await accessProfiles.upsert({
      userId: entry.userId,
      role: entry.role,
      status: 'active',
    })
  }

  const missing = configured
    .filter((entry) => !entry.userId)
    .map((entry) => entry.envName)
  if (missing.length > 0) {
    console.warn(`Reference access profiles not seeded for: ${missing.join(', ')}`)
  }
}

try {
  await seedCustomers()
  await seedReferenceAccessProfiles()
} finally {
  await prisma.$disconnect()
}
