import { useMemo } from 'react'
import { useAuthContext } from '@/contexts/AuthContext'
import { usePermission } from '@/hooks/usePermission'
import { menuConfig } from '@/config/menuConfig'
import { MenuItem } from '@/types/menu'

function canAccessMenuItem(
  item: MenuItem,
  isAdmin: boolean,
  hasResource: (resource: string) => boolean,
  hasAnyRole: (roles: MenuItem['roles']) => boolean,
): boolean {
  if (item.permission) {
    const resourceName = `menu:${item.id}`
    return hasResource(resourceName)
  }

  if (item.roles && item.roles.length > 0) {
    return hasAnyRole(item.roles)
  }

  return true
}

function filterMenuItems(
  items: MenuItem[],
  isAdmin: boolean,
  hasResource: (resource: string) => boolean,
  hasAnyRole: (roles: MenuItem['roles']) => boolean,
): MenuItem[] {
  return items
    .map((item) => {
      if (item.children?.length) {
        const children = filterMenuItems(item.children, isAdmin, hasResource, hasAnyRole)
        if (children.length === 0) return null
        return { ...item, children }
      }

      if (isAdmin || canAccessMenuItem(item, isAdmin, hasResource, hasAnyRole)) {
        return item
      }
      return null
    })
    .filter((item): item is MenuItem => item !== null)
    .sort((a, b) => {
      const priorityA = a.priority || 0
      const priorityB = b.priority || 0
      return priorityB - priorityA
    })
}

export function useFilteredMenuItems(): MenuItem[] {
  const { user } = useAuthContext()
  const { hasResource, hasAnyRole, isAdmin } = usePermission()

  return useMemo(() => {
    if (!user) return []

    if (isAdmin) {
      return menuConfig.items.slice().sort((a, b) => {
        const priorityA = a.priority || 0
        const priorityB = b.priority || 0
        return priorityB - priorityA
      })
    }

    return filterMenuItems(menuConfig.items, isAdmin, hasResource, hasAnyRole)
  }, [user, isAdmin, hasResource, hasAnyRole])
}

/** 扁平化菜单项，供移动端等场景使用 */
export function flattenMenuItems(items: MenuItem[]): MenuItem[] {
  const result: MenuItem[] = []
  for (const item of items) {
    if (item.children?.length) {
      result.push(...flattenMenuItems(item.children))
    } else {
      result.push(item)
    }
  }
  return result
}
