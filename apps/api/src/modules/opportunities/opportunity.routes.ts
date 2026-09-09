import type { FastifyInstance } from 'fastify'

import type { AuthorizationGuards } from '../../platform/authorization/guards.js'
import type { OpportunityRepository } from './opportunity.repository.js'
import {
  opportunityCreateSchema,
  opportunityListQuerySchema,
  opportunityListResponseSchema,
  opportunityParamsSchema,
  opportunitySchema,
  opportunityTransitionSchema,
} from './opportunity.schemas.js'
import type {
  OpportunityInput,
  OpportunityListParams,
  OpportunityStage,
  OpportunityTransitionCommand,
} from './opportunity.types.js'
import type { OpportunityCommandContext, OpportunityWorkflowService } from './opportunity.workflow-service.js'

type OpportunityParams = { opportunityId: string }
type OpportunityListQuery = {
  page?: number
  pageSize?: number
  search?: string
  sort?: OpportunityListParams['sort']
  direction?: OpportunityListParams['direction']
  'filter.stage'?: OpportunityStage
}

export type OpportunityRoutesOptions = {
  repository: OpportunityRepository
  workflow: OpportunityWorkflowService
  authorization: AuthorizationGuards
}

function commandContext(
  requestId: string,
  principal: OpportunityCommandContext['principal'],
  tenant: string | undefined,
): OpportunityCommandContext {
  return {
    principal,
    requestId,
    ...(tenant !== undefined ? { tenantId: tenant } : {}),
  }
}

export async function opportunityRoutes(app: FastifyInstance, options: OpportunityRoutesOptions) {
  const { repository, workflow, authorization } = options

  app.get<{ Querystring: OpportunityListQuery }>('/api/opportunities', {
    schema: {
      querystring: opportunityListQuerySchema,
      response: { 200: opportunityListResponseSchema },
    },
  }, async (request) => {
    await authorization.requireCapability(request, 'opportunities.read')
    const query = request.query
    return repository.list({
      page: query.page ?? 1,
      pageSize: query.pageSize ?? 25,
      ...(query.search !== undefined ? { search: query.search } : {}),
      ...(query.sort !== undefined ? { sort: query.sort } : {}),
      ...(query.direction !== undefined ? { direction: query.direction } : {}),
      ...(query['filter.stage'] !== undefined ? { stage: query['filter.stage'] } : {}),
    })
  })

  app.get<{ Params: OpportunityParams }>('/api/opportunities/:opportunityId', {
    schema: {
      params: opportunityParamsSchema,
      response: { 200: opportunitySchema },
    },
  }, async (request) => {
    await authorization.requireCapability(request, 'opportunities.read')
    return repository.get(request.params.opportunityId)
  })

  app.post<{ Body: OpportunityInput }>('/api/opportunities', {
    schema: {
      body: opportunityCreateSchema,
      response: { 201: opportunitySchema },
    },
  }, async (request, reply) => {
    const context = await authorization.requireCapability(request, 'opportunities.create')
    const created = await workflow.create(
      request.body,
      commandContext(request.id, context.principal, context.tenant),
    )
    return reply.status(201).send(created)
  })

  app.post<{ Params: OpportunityParams; Body: OpportunityTransitionCommand }>(
    '/api/opportunities/:opportunityId/commands/transition',
    {
      schema: {
        params: opportunityParamsSchema,
        body: opportunityTransitionSchema,
        response: { 200: opportunitySchema },
      },
    },
    async (request) => {
      const context = await authorization.requireCapability(request, 'opportunities.transition')
      return workflow.transition(
        request.params.opportunityId,
        request.body,
        commandContext(request.id, context.principal, context.tenant),
      )
    },
  )
}
