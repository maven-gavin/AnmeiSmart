'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { menuConfig } from '@/config/menuConfig';
import { getMenuIcon } from '@/utils/menuIcons';

export default function DynamicSidebar() {
  const { user } = useAuthContext();
  const pathname = usePathname();

  // 根据用户角色过滤菜单项
  const filteredMenuItems = useMemo(() => {
    if (!user?.currentRole) return [];
    
    const currentRole = user.currentRole;
    return menuConfig.items.filter(item => 
      item.roles.includes(currentRole)
    );
  }, [user]);

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