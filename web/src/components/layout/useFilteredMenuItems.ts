import { useMemo } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import { usePermission } from '@/hooks/usePermission';
import { menuConfig } from '@/config/menuConfig';
import { MenuItem } from '@/types/menu';

export function useFilteredMenuItems(): MenuItem[] {
  const { user } = useAuthContext();
  const { hasResource, hasAnyRole, isAdmin } = usePermission();

  return useMemo(() => {
    if (!user) return [];

    // 如果是admin角色，显示所有菜单
    if (isAdmin) {
      return menuConfig.items.slice().sort((a, b) => {
        const priorityA = a.priority || 0;
        const priorityB = b.priority || 0;
        return priorityB - priorityA;
      });
    }

    return menuConfig.items
      .filter(item => {
        // 优先使用权限控制
        if (item.permission) {
          const resourceName = `menu:${item.id}`;
          return hasResource(resourceName);
        }

        // 向后兼容：基于角色的菜单控制
        if (item.roles && item.roles.length > 0) {
          return hasAnyRole(item.roles);
        }

        // 如果没有指定权限或角色，默认显示
        return true;
      })
      .sort((a, b) => {
        // 按优先级排序
        const priorityA = a.priority || 0;
        const priorityB = b.priority || 0;
        return priorityB - priorityA;
      });
  }, [user, isAdmin, hasResource, hasAnyRole]);
}


