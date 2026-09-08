import { createPrincipal, type RequestContext } from '@cpxlabs-admin/authorization'
import type { SessionResponse } from '@cpxlabs-admin/contracts'
import { fromNodeHeaders } from 'better-auth/node'
import type { FastifyInstance, FastifyRequest } from 'fastify'

import { AppError } from '../errors.js'
import type { AccessProfileRepository } from '../authorization/access-profile.repository.js'
import { emitSecurityEvent } from './security-events.js'
import type { AppAuth } from './auth.js'

export type RequestContextResolver = (
  request: FastifyRequest,
) => Promise<RequestContext>

export function createRequestContextResolver(options: {
  auth: AppAuth
  accessProfiles: AccessProfileRepository
}): RequestContextResolver {
  return async (request) => {
    const providerSession = await options.auth.api.getSession({
      headers: fromNodeHeaders(request.headers),
    })

    if (!providerSession) {
      emitSecurityEvent(request, 'authentication.required')
      throw new AppError({
        code: 'AUTHENTICATION_REQUIRED',
        statusCode: 401,
        message: 'Authentication is required',
      })
    }

    const accessProfile = await options.accessProfiles.getByUserId(providerSession.user.id)
    if (!accessProfile || accessProfile.status !== 'active') {
      emitSecurityEvent(request, 'access.disabled', {
        userId: providerSession.user.id,
      })
      throw new AppError({
        code: 'ACCESS_DISABLED',
        statusCode: 403,
        message: 'Application access is not available',
      })
    }

    return {
      principal: createPrincipal({
        id: providerSession.user.id,
        email: providerSession.user.email,
        name: providerSession.user.name,
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
