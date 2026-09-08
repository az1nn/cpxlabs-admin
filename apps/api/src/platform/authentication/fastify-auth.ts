import { fromNodeHeaders } from 'better-auth/node'
import type { FastifyInstance } from 'fastify'

import type { AppAuth } from './auth.js'

export async function registerAuthenticationRoutes(
  app: FastifyInstance,
  auth: AppAuth,
) {
  app.route({
    method: ['GET', 'POST'],
    url: '/api/auth/*',
    async handler(request, reply) {
      const host = request.headers.host ?? '127.0.0.1'
      const protocol = request.headers['x-forwarded-proto'] ?? 'http'
      const forwardedProtocol = Array.isArray(protocol) ? protocol[0] : protocol
      const url = new URL(request.url, `${forwardedProtocol}://${host}`)

      const authRequest = new Request(url, {
        method: request.method,
        headers: fromNodeHeaders(request.headers),
        ...(request.body !== undefined
          ? { body: JSON.stringify(request.body) }
          : {}),
      })

      const response = await auth.handler(authRequest)
      reply.status(response.status)

      const getSetCookie = Reflect.get(response.headers, 'getSetCookie')
      if (typeof getSetCookie === 'function') {
        const cookies = getSetCookie.call(response.headers) as string[]
        if (cookies.length > 0) {
          reply.header('set-cookie', cookies)
        }
      }

      response.headers.forEach((value, key) => {
        if (key.toLowerCase() !== 'set-cookie') {
          reply.header(key, value)
        }
      })

      const body = await response.text()
      return reply.send(body.length > 0 ? body : null)
    },
  })
}
