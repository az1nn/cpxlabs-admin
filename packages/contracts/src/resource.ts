export type Capability = `${string}.${string}`

export type ResourceRoutes = {
  list?: string
  create?: string
  show?: string
  edit?: string
}

export type ResourceCapabilities = {
  list?: Capability
  show?: Capability
  create?: Capability
  edit?: Capability
  delete?: Capability
}

export type ResourceNavigation = {
  group?: string
  order?: number
  hidden?: boolean
}

export type ResourceDefinition = {
  name: string
  label: string
  routes: ResourceRoutes
  capabilities?: ResourceCapabilities
  navigation?: ResourceNavigation
}

export function defineResource<const T extends ResourceDefinition>(resource: T): T {
  return resource
}
