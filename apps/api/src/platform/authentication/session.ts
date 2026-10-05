import { createPrincipal, type RequestContext } from '@cpxlabs-admin/authorization'
import type { SessionResponse } from '@cpxlabs-admin/contracts'
import type { FastifyInstance, FastifyRequest } from 'fastify'

import { AppError } from '../errors.js'
import type { AccessProfileRepository } from '../authorization/access-profile.repository.js'
import { emitSecurityEvent } from './security-events.js'
import type { IdentityProvider } from './identity-provider.js'

export type RequestContextResolver = (
  request: FastifyRequest,
) => Promise<RequestContext>

function authenticationRequired(request: FastifyRequest): never {
  emitSecurityEvent(request, 'authentication.required')
  throw new AppError({
    code: 'AUTHENTICATION_REQUIRED',
    statusCode: 401,
    message: 'Authentication is required',
  })
}

function hasBearerToken(request: FastifyRequest): boolean {
  const authorization = request.headers.authorization
  if (!authorization) return false

  const [scheme, token, ...rest] = authorization.trim().split(/\s+/)
  return scheme?.toLowerCase() === 'bearer' && Boolean(token) && rest.length === 0
}

export function createRequestContextResolver(options: {
  identityProvider: IdentityProvider
  accessProfiles: AccessProfileRepository
}): RequestContextResolver {
  return async (request) => {
    if (!hasBearerToken(request)) {
      return authenticationRequired(request)
    }

    const identity = await options.identityProvider.authenticate(request)
    if (!identity) {
      return authenticationRequired(request)
    }

    const accessProfile = await options.accessProfiles.getByUserId(identity.id)
    if (!accessProfile || accessProfile.status !== 'active') {
      emitSecurityEvent(request, 'access.disabled', {
        userId: identity.id,
      })
      throw new AppError({
        code: 'ACCESS_DISABLED',
        statusCode: 403,
        message: 'Application access is not available',
      })
    }

    return {
      principal: createPrincipal({
        id: identity.id,
        email: identity.email,
        name: identity.name,
        role: accessProfile.role,
      }),
    }
  }
}

export async function registerApplicationSessionRoute(
  app: FastifyInstance,
  resolveRequestContext: RequestContextResolver,
) {
  app.get('/api/session', async (request) => {
    const context = await resolveRequestContext(request)
    const response: SessionResponse = {
      principal: {
        id: context.principal.id,
        email: context.principal.email,
        name: context.principal.name,
        role: context.principal.role,
        capabilities: [...context.principal.capabilities],
      },
    }
    return response
  })
}
