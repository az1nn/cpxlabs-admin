import { defineResource } from '@cpxlabs-admin/contracts'

export const customerResource = defineResource({
  name: 'customers',
  label: 'Customers',
  routes: {
    list: '/customers',
    create: '/customers/new',
    show: '/customers/:id',
    edit: '/customers/:id/edit',
  },
  capabilities: {
    list: 'customers.read',
    show: 'customers.read',
    create: 'customers.create',
    edit: 'customers.update',
    delete: 'customers.delete',
  },
  navigation: {
    group: 'CRM',
    order: 10,
  },
})
