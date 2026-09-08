import type { ResourceDefinition } from '@cpxlabs-admin/contracts'

export class ResourceRegistry {
  readonly #resources: readonly ResourceDefinition[]
  readonly #byName: ReadonlyMap<string, ResourceDefinition>

  constructor(resources: readonly ResourceDefinition[]) {
    const byName = new Map<string, ResourceDefinition>()

    for (const resource of resources) {
      if (byName.has(resource.name)) {
        throw new Error(`Duplicate resource registration: ${resource.name}`)
      }

      byName.set(resource.name, resource)
    }

    this.#resources = Object.freeze([...resources])
    this.#byName = byName
  }

  list(): readonly ResourceDefinition[] {
    return this.#resources
  }

  get(name: string): ResourceDefinition | undefined {
    return this.#byName.get(name)
  }

  require(name: string): ResourceDefinition {
    const resource = this.get(name)

    if (!resource) {
      throw new Error(`Unknown resource: ${name}`)
    }

    return resource
  }
}
