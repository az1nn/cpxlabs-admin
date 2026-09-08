import type { ApplicationRole } from '@cpxlabs-admin/contracts'
import { loadEnvFile } from 'node:process'

import { createAuth } from '../authentication/auth.js'
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

const referenceUsers: ReadonlyArray<{
  name: string
  email: string
  role: ApplicationRole
}> = [
  { name: 'Reference Admin', email: 'admin@cpxlabs.local', role: 'admin' },
  { name: 'Reference Manager', email: 'manager@cpxlabs.local', role: 'manager' },
  { name: 'Reference Viewer', email: 'viewer@cpxlabs.local', role: 'viewer' },
]

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

async function seedReferenceUsers() {
  const secret = process.env.BETTER_AUTH_SECRET?.trim()
  const password = process.env.SEED_AUTH_PASSWORD?.trim()

  if (!secret || !password) {
    console.warn(
      'Skipping reference auth users because BETTER_AUTH_SECRET or SEED_AUTH_PASSWORD is not configured.',
    )
    return
  }

  const baseURL = process.env.BETTER_AUTH_URL?.trim() ?? 'http://127.0.0.1:3001'
  const appOrigin = process.env.APP_ORIGIN?.trim() ?? 'http://127.0.0.1:4173'
  const auth = createAuth({
    prisma,
    baseURL,
    secret,
    trustedOrigins: [appOrigin],
    allowSignUp: true,
  })
  const accessProfiles = new PrismaAccessProfileRepository(prisma)

  for (const referenceUser of referenceUsers) {
    let user = await prisma.user.findUnique({
      where: { email: referenceUser.email },
    })

    if (!user) {
      const result = await auth.api.signUpEmail({
        body: {
          name: referenceUser.name,
          email: referenceUser.email,
          password,
        },
      })
      user = result.user
    }

    await accessProfiles.upsert({
      userId: user.id,
      role: referenceUser.role,
      status: 'active',
    })
  }
}

try {
  await seedCustomers()
  await seedReferenceUsers()
} finally {
  await prisma.$disconnect()
}
