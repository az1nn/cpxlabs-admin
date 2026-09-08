import { createPrincipal } from '@cpxlabs-admin/authorization'

export const demoPrincipal = createPrincipal({
  id: 'demo-admin',
  email: 'demo@cpxlabs.local',
  name: 'Demo Admin',
  role: 'admin',
})
