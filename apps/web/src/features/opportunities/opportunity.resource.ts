import { defineResource } from '@cpxlabs-admin/contracts'

export const opportunityResource = defineResource({
  name: 'opportunities',
  label: 'Opportunities',
  routes: {
    list: '/opportunities',
    create: '/opportunities/new',
    show: '/opportunities/:id',
  },
  capabilities: {
    list: 'opportunities.read',
    show: 'opportunities.read',
    create: 'opportunities.create',
  },
  navigation: {
    group: 'CRM',
    order: 20,
  },
})
