import type { FastifyRequest } from 'fastify'
import { describe, expect, it, vi } from 'vitest'

import { emitSecurityEvent } from './security-events.js'

describe('emitSecurityEvent', () => {
  it('emits structured request context while dropping secret-like metadata', () => {
    const warn = vi.fn()
    const request = {
      id: 'req-security-1',
      method: 'POST',
      url: '/api/auth/sign-in/email?debug=true',
      log: { warn },
    } as unknown as FastifyRequest

    emitSecurityEvent(request, 'authentication.failed', {
      userId: 'usr_123',
      password: 'must-not-log',
      sessionToken: 'must-not-log',
      authorization: 'must-not-log',
    })

    expect(warn).toHaveBeenCalledTimes(1)
    expect(warn).toHaveBeenCalledWith(
      {
        securityEvent: 'authentication.failed',
        requestId: 'req-security-1',
        method: 'POST',
        path: '/api/auth/sign-in/email',
        userId: 'usr_123',
      },
      'Security event',
    )
  })
})
