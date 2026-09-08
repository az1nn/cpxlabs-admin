import { defineResource } from '@cpxlabs-admin/contracts'

export const customerResource = defineResource({
  name: 'customers',
  label: 'Customers',
  routes: {
    list: '/customers',
  },
  capabilities: {
    list: 'customers.read',
    create: 'customers.create',
    edit: 'customers.update',
    delete: 'customers.delete',
  },
  navigation: {
    group: 'CRM',
    order: 10,
  },
})
