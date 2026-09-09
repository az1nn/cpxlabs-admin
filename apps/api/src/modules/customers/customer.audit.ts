import type { CustomerAuditSnapshot } from '@cpxlabs-admin/contracts'

import type { Customer } from './customer.types.js'

export function toCustomerAuditSnapshot(customer: Customer): CustomerAuditSnapshot {
  return {
    id: customer.id,
    name: customer.name,
    email: customer.email,
    company: customer.company,
    status: customer.status,
    updatedAt: customer.updatedAt,
  }
}
