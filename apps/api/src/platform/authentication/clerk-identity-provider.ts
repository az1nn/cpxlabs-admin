import { clerkClient, clerkPlugin, getAuth } from '@clerk/fastify'
import type { FastifyInstance, FastifyRequest } from 'fastify'

import type {
  AuthenticatedIdentity,
  IdentityProvider,
} from './identity-provider.js'

type ClerkAuthResult = {
  isAuthenticated: boolean
  userId: string | null
}

type ClerkEmailAddress = {
  id: string
  emailAddress: string
}

type ClerkUserRecord = {
  id: string
  firstName: string | null
  lastName: string | null
  username: string | null
  primaryEmailAddressId: string | null
  emailAddresses: ClerkEmailAddress[]
}

type ClerkIdentityProviderOptions = {
  getRequestAuth?: (request: FastifyRequest) => ClerkAuthResult
  getUser?: (userId: string) => Promise<ClerkUserRecord>
}

export function createClerkIdentityProvider(
  options: ClerkIdentityProviderOptions = {},
): IdentityProvider {
  const getRequestAuth = options.getRequestAuth ?? ((request) => getAuth(request))
  const getUser =
    options.getUser ??
    (async (userId) => {
      const user = await clerkClient.users.getUser(userId)
      return {
        id: user.id,
        firstName: user.firstName,
        lastName: user.lastName,
        username: user.username,
        primaryEmailAddressId: user.primaryEmailAddressId,
        emailAddresses: user.emailAddresses.map((address) => ({
          id: address.id,
          emailAddress: address.emailAddress,
        })),
      }
    })

  return {
    async authenticate(request) {
      const auth = getRequestAuth(request)
      if (!auth.isAuthenticated || !auth.userId) {
        return null
      }

      const user = await getUser(auth.userId)
      const primaryEmail =
        user.emailAddresses.find(
          (address) => address.id === user.primaryEmailAddressId,
        ) ?? user.emailAddresses[0]

      if (!primaryEmail) {
        throw new Error('Authenticated Clerk user does not have an email address')
      }

      const displayName = [user.firstName, user.lastName]
        .filter((part): part is string => Boolean(part?.trim()))
        .join(' ')
        .trim()

      const identity: AuthenticatedIdentity = {
        id: user.id,
        email: primaryEmail.emailAddress,
        name: displayName || user.username || primaryEmail.emailAddress,
      }

      return identity
    },
  }
}

export function registerClerkAuthentication(
  app: FastifyInstance,
  options: {
    publishableKey: string
    secretKey: string
  },
) {
  app.register(clerkPlugin, {
    publishableKey: options.publishableKey,
    secretKey: options.secretKey,
    hookName: 'onRequest',
  })
}
