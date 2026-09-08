import { describe, expect, it } from 'vitest'

import type { Customer } from '../../features/customers/customer.types'
import { demoDataProvider } from './demo-data-provider'

describe('demoDataProvider', () => {
  it('applies server-style filtering before pagination', async () => {
    const result = await demoDataProvider.getList<Customer>('customers', {
      page: 1,
      pageSize: 2,
      filters: { status: 'active' },
      sort: { field: 'name', direction: 'asc' },
    })

    expect(result.total).toBeGreaterThan(2)
    expect(result.data).toHaveLength(2)
    expect(result.data.every((customer) => customer.status === 'active')).toBe(true)
  })

  it('searches customer identity fields', async () => {
    const result = await demoDataProvider.getList<Customer>('customers', {
      page: 1,
      pageSize: 25,
      search: 'northstar',
    })

    expect(result.total).toBe(1)
    expect(result.data[0]?.name).toBe('Northstar Retail')
  })
})
