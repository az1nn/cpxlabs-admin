import { AppError } from '../../platform/errors.js'
import type {
  Customer,
  CustomerInput,
  CustomerListParams,
} from './customer.types.js'

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

export class InMemoryCustomerRepository {
  private customers = seedCustomers.map((customer) => ({ ...customer }))
  private sequence = 100

  list(params: CustomerListParams) {
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

  get(id: string): Customer {
    const customer = this.customers.find((candidate) => candidate.id === id)
    if (!customer) {
      throw new AppError({ code: 'not_found', statusCode: 404, message: 'Customer not found' })
    }
    return customer
  }

  create(input: CustomerInput): Customer {
    const customer: Customer = {
      id: `cus_${++this.sequence}`,
      ...input,
      updatedAt: new Date().toISOString(),
    }
    this.customers = [customer, ...this.customers]
    return customer
  }

  update(id: string, input: CustomerInput): Customer {
    this.get(id)
    const customer: Customer = {
      id,
      ...input,
      updatedAt: new Date().toISOString(),
    }
    this.customers = this.customers.map((candidate) => (candidate.id === id ? customer : candidate))
    return customer
  }

  delete(id: string): void {
    this.get(id)
    this.customers = this.customers.filter((candidate) => candidate.id !== id)
  }
}
