import type { DataProvider, ListParams, ListResult } from '@cpxlabs-admin/contracts'

import type { Customer, CustomerInput } from '../../features/customers/customer.types'

let customers: Customer[] = [
  { id: 'cus_001', name: 'Acme Brasil', email: 'ops@acme.example', company: 'Acme', status: 'active', updatedAt: '2026-09-08T09:12:00-03:00' },
  { id: 'cus_002', name: 'Northstar Retail', email: 'admin@northstar.example', company: 'Northstar', status: 'lead', updatedAt: '2026-09-07T16:40:00-03:00' },
  { id: 'cus_003', name: 'Atlas Logistics', email: 'it@atlas.example', company: 'Atlas', status: 'active', updatedAt: '2026-09-06T14:02:00-03:00' },
  { id: 'cus_004', name: 'Blue Harbor', email: 'finance@blueharbor.example', company: 'Blue Harbor', status: 'inactive', updatedAt: '2026-09-05T10:20:00-03:00' },
  { id: 'cus_005', name: 'Lumina Health', email: 'ops@lumina.example', company: 'Lumina', status: 'lead', updatedAt: '2026-09-04T12:18:00-03:00' },
  { id: 'cus_006', name: 'Vertex Systems', email: 'admin@vertex.example', company: 'Vertex', status: 'active', updatedAt: '2026-09-03T17:32:00-03:00' },
  { id: 'cus_007', name: 'Cedar Finance', email: 'team@cedar.example', company: 'Cedar', status: 'active', updatedAt: '2026-09-02T11:46:00-03:00' },
  { id: 'cus_008', name: 'Orbit Foods', email: 'contact@orbit.example', company: 'Orbit', status: 'inactive', updatedAt: '2026-09-01T08:15:00-03:00' },
  { id: 'cus_009', name: 'Nova Works', email: 'ops@nova.example', company: 'Nova', status: 'lead', updatedAt: '2026-08-29T15:24:00-03:00' },
  { id: 'cus_010', name: 'Pioneer Energy', email: 'admin@pioneer.example', company: 'Pioneer', status: 'active', updatedAt: '2026-08-27T13:08:00-03:00' },
  { id: 'cus_011', name: 'Summit Labs', email: 'hello@summit.example', company: 'Summit', status: 'active', updatedAt: '2026-08-25T09:52:00-03:00' },
  { id: 'cus_012', name: 'Ember Studio', email: 'team@ember.example', company: 'Ember', status: 'inactive', updatedAt: '2026-08-21T18:05:00-03:00' },
]

let sequence = 100

function compareCustomers(a: Customer, b: Customer, field: string): number {
  switch (field) {
    case 'name': return a.name.localeCompare(b.name)
    case 'company': return a.company.localeCompare(b.company)
    case 'status': return a.status.localeCompare(b.status)
    case 'updatedAt': return a.updatedAt.localeCompare(b.updatedAt)
    default: return 0
  }
}

function assertCustomerResource(resource: string) {
  if (resource !== 'customers') {
    throw new Error(`Demo provider does not implement resource: ${resource}`)
  }
}

function getCustomer(id: string) {
  const customer = customers.find((candidate) => candidate.id === id)
  if (!customer) {
    throw new Error(`Customer not found: ${id}`)
  }
  return customer
}

async function listCustomers<T>(params: ListParams): Promise<ListResult<T>> {
  let result = [...customers]
  const search = params.search?.trim().toLocaleLowerCase()

  if (search) {
    result = result.filter((customer) =>
      [customer.name, customer.email, customer.company].some((value) =>
        value.toLocaleLowerCase().includes(search),
      ),
    )
  }

  const status = params.filters?.['status']
  if (typeof status === 'string') {
    result = result.filter((customer) => customer.status === status)
  }

  if (params.sort) {
    const direction = params.sort.direction === 'asc' ? 1 : -1
    result.sort((left, right) => compareCustomers(left, right, params.sort!.field) * direction)
  }

  const total = result.length
  const offset = Math.max(0, (params.page - 1) * params.pageSize)
  const page = result.slice(offset, offset + params.pageSize)

  return { data: page as unknown as readonly T[], total }
}

export const demoDataProvider: DataProvider = {
  async getList<T>(resource: string, params: ListParams): Promise<ListResult<T>> {
    assertCustomerResource(resource)
    return listCustomers<T>(params)
  },

  async getOne<T>(resource: string, id: string): Promise<T> {
    assertCustomerResource(resource)
    return getCustomer(id) as unknown as T
  },

  async create<T>(resource: string, input: unknown): Promise<T> {
    assertCustomerResource(resource)
    const values = input as CustomerInput
    const customer: Customer = {
      id: `cus_${++sequence}`,
      ...values,
      updatedAt: new Date().toISOString(),
    }
    customers = [customer, ...customers]
    return customer as unknown as T
  },

  async update<T>(resource: string, id: string, input: unknown): Promise<T> {
    assertCustomerResource(resource)
    getCustomer(id)
    const values = input as CustomerInput
    const updated: Customer = {
      id,
      ...values,
      updatedAt: new Date().toISOString(),
    }
    customers = customers.map((customer) => (customer.id === id ? updated : customer))
    return updated as unknown as T
  },

  async delete(resource: string, id: string): Promise<void> {
    assertCustomerResource(resource)
    getCustomer(id)
    customers = customers.filter((customer) => customer.id !== id)
  },
}
