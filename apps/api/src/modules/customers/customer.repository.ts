import { AppError } from '../../platform/errors.js'
import type {
  Customer,
  CustomerInput,
  CustomerListParams,
} from './customer.types.js'

export type CustomerListResult = {
  data: Customer[]
  total: number
}

export interface CustomerRepository {
  list(params: CustomerListParams): Promise<CustomerListResult>
  get(id: string): Promise<Customer>
  create(input: CustomerInput): Promise<Customer>
  update(id: string, input: CustomerInput): Promise<Customer>
  delete(id: string): Promise<void>
}

const seedCustomers: Customer[] = [
  {
    id: 'cus_001',
    name: 'Acme Brasil',
    email: 'ops@acme.example',
    company: 'Acme',
    status: 'active',
    updatedAt: '2026-09-08T09:12:00-03:00',
  },
  {
    id: 'cus_002',
    name: 'Northstar Retail',
    email: 'admin@northstar.example',
    company: 'Northstar',
    status: 'lead',
    updatedAt: '2026-09-07T16:40:00-03:00',
  },
]

function compareCustomers(left: Customer, right: Customer, field: NonNullable<CustomerListParams['sort']>) {
  return left[field].localeCompare(right[field])
}

export class InMemoryCustomerRepository implements CustomerRepository {
  private customers = seedCustomers.map((customer) => ({ ...customer }))
  private sequence = 100

  async list(params: CustomerListParams): Promise<CustomerListResult> {
    let result = [...this.customers]
    const search = params.search?.trim().toLocaleLowerCase()

    if (search) {
      result = result.filter((customer) =>
        [customer.name, customer.email, customer.company].some((value) =>
          value.toLocaleLowerCase().includes(search),
        ),
      )
    }

    if (params.status) {
      result = result.filter((customer) => customer.status === params.status)
    }

    if (params.sort) {
      const direction = params.direction === 'desc' ? -1 : 1
      result.sort((left, right) => compareCustomers(left, right, params.sort!) * direction)
    }

    const total = result.length
    const offset = (params.page - 1) * params.pageSize
    return { data: result.slice(offset, offset + params.pageSize), total }
  }

  async get(id: string): Promise<Customer> {
    const customer = this.customers.find((candidate) => candidate.id === id)
    if (!customer) {
      throw new AppError({ code: 'not_found', statusCode: 404, message: 'Customer not found' })
    }
    return customer
  }

  async create(input: CustomerInput): Promise<Customer> {
    const customer: Customer = {
      id: `cus_${++this.sequence}`,
      ...input,
      updatedAt: new Date().toISOString(),
    }
    this.customers = [customer, ...this.customers]
    return customer
  }

  async update(id: string, input: CustomerInput): Promise<Customer> {
    await this.get(id)
    const customer: Customer = {
      id,
      ...input,
      updatedAt: new Date().toISOString(),
    }
    this.customers = this.customers.map((candidate) => (candidate.id === id ? customer : candidate))
    return customer
  }

  async delete(id: string): Promise<void> {
    await this.get(id)
    this.customers = this.customers.filter((candidate) => candidate.id !== id)
  }
}
