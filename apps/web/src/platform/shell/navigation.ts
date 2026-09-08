import type { Capability } from '@cpxlabs-admin/contracts'

import type { ResourceRegistry } from '../resources/resource-registry'

export type NavigationItem = {
  resource: string
  label: string
  href: string
  group: string
  order: number
}

export function getNavigationItems(
  registry: ResourceRegistry,
  can: (capability: Capability) => boolean,
): readonly NavigationItem[] {
  return registry
    .list()
    .flatMap((resource): NavigationItem[] => {
      const href = resource.routes.list
      const requiredCapability = resource.capabilities?.list

      if (!href || resource.navigation?.hidden) {
        return []
      }

      if (requiredCapability && !can(requiredCapability)) {
        return []
      }

      return [
        {
          resource: resource.name,
          label: resource.label,
          href,
          group: resource.navigation?.group ?? 'General',
          order: resource.navigation?.order ?? Number.MAX_SAFE_INTEGER,
        },
      ]
    })
    .sort((left, right) => {
      const groupOrder = left.group.localeCompare(right.group)
      if (groupOrder !== 0) return groupOrder
      if (left.order !== right.order) return left.order - right.order
      return left.label.localeCompare(right.label)
    })
}
