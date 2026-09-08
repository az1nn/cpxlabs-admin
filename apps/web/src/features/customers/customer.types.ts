export type CustomerStatus = 'lead' | 'active' | 'inactive'

export type Customer = {
  id: string
  name: string
  email: string
  company: string
  status: CustomerStatus
  updatedAt: string
}

export type CustomerInput = Pick<Customer, 'name' | 'email' | 'company' | 'status'>
