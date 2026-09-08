import type { Capability } from '@cpxlabs-admin/contracts'

export type Principal = {
  id: string
  capabilities: ReadonlySet<Capability>
}

export type AuthorizationDecision = {
  allowed: boolean
  capability: Capability
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
