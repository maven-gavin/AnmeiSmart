'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { getMenuIcon } from '@/utils/menuIcons';
import { useFilteredMenuItems } from '@/components/layout/useFilteredMenuItems';

export default function DynamicSidebar() {
  const pathname = usePathname();
  const filteredMenuItems = useFilteredMenuItems();

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