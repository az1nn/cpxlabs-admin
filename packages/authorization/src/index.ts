import type { ApplicationRole, Capability } from '@cpxlabs-admin/contracts'

const roleCapabilities = {
  admin: new Set<Capability>([
    'customers.read',
    'customers.create',
    'customers.update',
    'customers.delete',
    'opportunities.read',
    'opportunities.create',
    'opportunities.transition',
    'audit.read',
  ]),
  manager: new Set<Capability>([
    'customers.read',
    'customers.create',
    'customers.update',
    'opportunities.read',
    'opportunities.create',
    'opportunities.transition',
  ]),
  viewer: new Set<Capability>(['customers.read', 'opportunities.read']),
} satisfies Record<ApplicationRole, ReadonlySet<Capability>>

export type Principal = {
  id: string
  email: string
  name: string
  role: ApplicationRole
  capabilities: ReadonlySet<Capability>
}

export type RequestContext = {
  principal: Principal
  tenant?: string
}

export type AuthorizationDecision = {
  allowed: boolean
  capability: Capability
}

export function capabilitiesForRole(role: ApplicationRole): ReadonlySet<Capability> {
  return roleCapabilities[role]
}

export function createPrincipal(input: Omit<Principal, 'capabilities'>): Principal {
  return {
    ...input,
    capabilities: capabilitiesForRole(input.role),
  }
}

export function can(principal: Principal | null, capability: Capability): boolean {
  return principal?.capabilities.has(capability) ?? false
}

export function authorize(
  principal: Principal | null,
  capability: Capability,
): AuthorizationDecision {
  return {
    allowed: can(principal, capability),
    capability,
  }
}
