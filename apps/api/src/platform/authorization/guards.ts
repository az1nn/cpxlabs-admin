import { can, type RequestContext } from '@cpxlabs-admin/authorization'
import type { Capability } from '@cpxlabs-admin/contracts'
import type { FastifyRequest } from 'fastify'

import { AppError } from '../errors.js'
import type { RequestContextResolver } from '../authentication/session.js'
import { emitSecurityEvent } from '../authentication/security-events.js'

export type AuthorizationGuards = {
  requirePrincipal(request: FastifyRequest): Promise<RequestContext>
  requireCapability(
    request: FastifyRequest,
    capability: Capability,
  ): Promise<RequestContext>
}

function authenticationRequired(request: FastifyRequest): never {
  emitSecurityEvent(request, 'authentication.required')
  throw new AppError({
    code: 'AUTHENTICATION_REQUIRED',
    statusCode: 401,
    message: 'Authentication is required',
  })
}

export function createUnauthenticatedGuards(): AuthorizationGuards {
  return {
    async requirePrincipal(request) {
      return authenticationRequired(request)
    },
    async requireCapability(request) {
      return authenticationRequired(request)
    },
  }
}

export function createAuthorizationGuards(
  resolveRequestContext: RequestContextResolver,
): AuthorizationGuards {
  return {
    requirePrincipal: resolveRequestContext,
    async requireCapability(request, capability) {
      const context = await resolveRequestContext(request)
      if (!can(context.principal, capability)) {
        emitSecurityEvent(request, 'authorization.forbidden', {
          userId: context.principal.id,
          capability,
        })
        throw new AppError({
          code: 'FORBIDDEN',
          statusCode: 403,
          message: 'The requested action is not permitted',
        })
      }
      return context
    },
  }
}
