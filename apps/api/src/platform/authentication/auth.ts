import { betterAuth } from 'better-auth'
import { prismaAdapter } from 'better-auth/adapters/prisma'

import type { PrismaClient } from '../../generated/prisma/client.js'

export type CreateAuthOptions = {
  prisma: PrismaClient
  baseURL: string
  secret: string
  trustedOrigins: readonly string[]
  allowSignUp?: boolean
}

export function createAuth(options: CreateAuthOptions) {
  return betterAuth({
    appName: 'CPXLabs Admin',
    baseURL: options.baseURL,
    basePath: '/api/auth',
    secret: options.secret,
    database: prismaAdapter(options.prisma, {
      provider: 'postgresql',
    }),
    trustedOrigins: [...options.trustedOrigins],
    emailAndPassword: {
      enabled: true,
      disableSignUp: !(options.allowSignUp ?? false),
      minPasswordLength: 8,
      maxPasswordLength: 128,
    },
    session: {
      expiresIn: 60 * 60 * 24 * 7,
      updateAge: 60 * 60 * 24,
    },
    rateLimit: {
      enabled: true,
    },
  })
}

export type AppAuth = ReturnType<typeof createAuth>
