import { defineResource } from '@cpxlabs-admin/contracts'
import { describe, expect, it } from 'vitest'

import { ResourceRegistry } from '../resources/resource-registry'
import { getNavigationItems } from './navigation'

describe('getNavigationItems', () => {
  it('hides resources whose list capability is denied', () => {
    const registry = new ResourceRegistry([
      defineResource({
        name: 'customers',
        label: 'Customers',
        routes: { list: '/customers' },
        capabilities: { list: 'customers.read' },
      }),
      defineResource({
        name: 'users',
        label: 'Users',
        routes: { list: '/users' },
        capabilities: { list: 'users.read' },
      }),
    ])

    const items = getNavigationItems(
      registry,
      (capability) => capability === 'customers.read',
    )

    expect(items.map((item) => item.resource)).toEqual(['customers'])
  })
})
