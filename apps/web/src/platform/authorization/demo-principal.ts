import type { Principal } from '@cpxlabs-admin/authorization'
import type { Capability } from '@cpxlabs-admin/contracts'

const capabilities = new Set<Capability>([
  'customers.read',
  'customers.create',
  'customers.update',
  'customers.delete',
])

export const demoPrincipal: Principal = {
  id: 'demo-admin',
  capabilities,
}
