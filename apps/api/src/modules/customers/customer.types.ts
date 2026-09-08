export type CustomerStatus = 'lead' | 'active' | 'inactive'

export type Customer = {
  id: string
  name: string
  email: string
  company: string
  status: CustomerStatus
  updatedAt: string
}

export type CustomerInput = Omit<Customer, 'id' | 'updatedAt'>

export type CustomerListParams = {
  page: number
  pageSize: number
  search?: string
  sort?: 'name' | 'company' | 'status' | 'updatedAt'
  direction?: 'asc' | 'desc'
  status?: CustomerStatus
}
