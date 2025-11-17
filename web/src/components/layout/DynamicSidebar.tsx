'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { usePermission } from '@/hooks/usePermission';
import { menuConfig } from '@/config/menuConfig';
import { getMenuIcon } from '@/utils/menuIcons';

export default function DynamicSidebar() {
  const { user } = useAuthContext();
  const { hasResource, hasRole, hasAnyRole, isAdmin } = usePermission();
  const pathname = usePathname();

  // 根据用户权限和角色过滤菜单项
  const filteredMenuItems = useMemo(() => {
    if (!user) return [];
    
    // 如果是administrator角色，显示所有菜单
    if (isAdmin) {
      return menuConfig.items.sort((a, b) => {
        const priorityA = a.priority || 0;
        const priorityB = b.priority || 0;
        return priorityB - priorityA;
      });
    }
    
    return menuConfig.items.filter(item => {
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
    }).sort((a, b) => {
      // 按优先级排序
      const priorityA = a.priority || 0;
      const priorityB = b.priority || 0;
      return priorityB - priorityA;
    });
  }, [user, isAdmin, hasResource, hasAnyRole]);

  return (
    <div className="w-64 flex-shrink-0 bg-white shadow-sm">
      <nav className="flex h-full flex-col border-r border-gray-200 p-4">
        <div className="space-y-1">
          {filteredMenuItems.map((item) => {
            const isActive = pathname.startsWith(item.path);
            const Icon = getMenuIcon(item.icon);
            
            return (
              <Link
                key={item.id}
                href={item.path}
                className={`flex items-center rounded-md px-3 py-2 text-sm font-medium ${
                  isActive
                    ? 'bg-orange-50 text-orange-700'
                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <span className={`mr-3 ${isActive ? 'text-orange-500' : 'text-gray-500'}`}>
                  <Icon />
                </span>
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
} 