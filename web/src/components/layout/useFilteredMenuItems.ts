import { useMemo } from 'react'
import { useAuthContext } from '@/contexts/AuthContext'
import { usePermission } from '@/hooks/usePermission'
import { menuConfig } from '@/config/menuConfig'
import { MenuItem } from '@/types/menu'

function canAccessMenuItem(
  item: MenuItem,
  isAdmin: boolean,
  hasResource: (resource: string) => boolean,
  hasAnyRole: (roles?: MenuItem['roles']) => boolean,
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
  hasAnyRole: (roles?: MenuItem['roles']) => boolean,
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
}

/** 分组只剩一个可见子项时，提升为一级菜单，避免无意义的折叠 */
function flattenSingleChildGroups(items: MenuItem[]): MenuItem[] {
  return items.flatMap((item) => {
    if (item.children?.length === 1) {
      return flattenSingleChildGroups(item.children)
    }
    if (item.children?.length) {
      return [{ ...item, children: flattenSingleChildGroups(item.children) }]
    }
    return [item]
  })
}

function sortMenuItems(items: MenuItem[]): MenuItem[] {
  return [...items]
    .sort((a, b) => (b.priority || 0) - (a.priority || 0))
    .map((item) =>
      item.children?.length ? { ...item, children: sortMenuItems(item.children) } : item,
    )
}

export function useFilteredMenuItems(): MenuItem[] {
  const { user } = useAuthContext()
  const { hasResource, hasAnyRole, isAdmin } = usePermission()

  return useMemo(() => {
    if (!user) return []

    const filtered = isAdmin
      ? menuConfig.items
      : filterMenuItems(menuConfig.items, isAdmin, hasResource, hasAnyRole)

    return sortMenuItems(flattenSingleChildGroups(filtered))
  }, [user, isAdmin, hasResource, hasAnyRole])
}

/** 扁平化菜单项，供移动端等场景使用 */
export function flattenMenuItems(items: MenuItem[]): MenuItem[] {
  const result: MenuItem[] = []
  for (const item of items) {
    if (item.children?.length) {
      result.push(...flattenMenuItems(item.children))
    } else if (!item.groupOnly) {
      result.push(item)
    }
  }
  return result
}
