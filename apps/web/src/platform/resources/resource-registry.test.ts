import { defineResource } from '@cpxlabs-admin/contracts'
import { describe, expect, it } from 'vitest'

import { ResourceRegistry } from './resource-registry'

const customers = defineResource({
  name: 'customers',
  label: 'Customers',
  routes: { list: '/customers' },
})

describe('ResourceRegistry', () => {
  it('returns registered resources by name', () => {
    const registry = new ResourceRegistry([customers])

    expect(registry.require('customers')).toBe(customers)
  })

  it('rejects duplicate resource names', () => {
    expect(() => new ResourceRegistry([customers, customers])).toThrow(
      'Duplicate resource registration: customers',
    )
  })
})
