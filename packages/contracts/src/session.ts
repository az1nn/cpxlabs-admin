import type { Capability } from './resource'

export type ApplicationRole = 'admin' | 'manager' | 'viewer'

export type SessionPrincipalDto = {
  id: string
  email: string
  name: string
  role: ApplicationRole
  capabilities: readonly Capability[]
}

export type SessionResponse = {
  principal: SessionPrincipalDto
}
