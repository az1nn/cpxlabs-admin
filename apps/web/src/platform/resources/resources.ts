import { customerResource } from '../../features/customers/customer.resource'
import { ResourceRegistry } from './resource-registry'

export const resourceRegistry = new ResourceRegistry([customerResource])
