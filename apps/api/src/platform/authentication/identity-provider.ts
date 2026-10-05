import type { FastifyRequest } from 'fastify'

export type AuthenticatedIdentity = {
  id: string
  email: string
  name: string
}

export type IdentityProvider = {
  authenticate(request: FastifyRequest): Promise<AuthenticatedIdentity | null>
}
