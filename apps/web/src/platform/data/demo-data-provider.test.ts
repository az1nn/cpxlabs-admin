import { describe, expect, it } from 'vitest'

import type { Customer, CustomerInput } from '../../features/customers/customer.types'
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

  it('supports the generic CRUD contract', async () => {
    const input: CustomerInput = {
      name: 'Test Customer',
      company: 'Test Company',
      email: 'test@example.com',
      status: 'lead',
    }

    const created = await demoDataProvider.create<Customer>('customers', input)
    expect((await demoDataProvider.getOne<Customer>('customers', created.id)).name).toBe(input.name)

    const updated = await demoDataProvider.update<Customer>('customers', created.id, {
      ...input,
      status: 'active',
    })
    expect(updated.status).toBe('active')

    await demoDataProvider.delete('customers', created.id)
    await expect(demoDataProvider.getOne<Customer>('customers', created.id)).rejects.toThrow('Customer not found')
  })
})
