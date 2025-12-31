'use client';

import { useMemo } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { MoreVertical } from 'lucide-react';
import { getMenuIcon } from '@/utils/menuIcons';
import { useFilteredMenuItems } from '@/components/layout/useFilteredMenuItems';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';

const MOBILE_PRIMARY_PATHS = ['/tasks', '/chat', '/contacts', '/profile'] as const;
const MOBILE_MORE_PATHS = ['/statistics'] as const;

export function MobileBottomNav() {
  const pathname = usePathname();
  const router = useRouter();
  const items = useFilteredMenuItems();

  const { primary, more } = useMemo(() => {
    const primaryItems = MOBILE_PRIMARY_PATHS.flatMap(p => {
      const found = items.find(i => i.path === p);
      return found ? [found] : [];
    });

    const moreItems = MOBILE_MORE_PATHS.flatMap(p => {
      const found = items.find(i => i.path === p);
      return found ? [found] : [];
    });

    return {
      primary: primaryItems,
      more: moreItems
    };
  }, [items]);

  return (
    <div className="fixed bottom-0 inset-x-0 z-40 border-t border-gray-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/75 md:hidden">
      <div className="grid grid-cols-5 h-14">
        {primary.map((item) => {
          const isActive = pathname.startsWith(item.path);
          const Icon = getMenuIcon(item.icon);

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => router.push(item.path)}
              className={cn(
                "flex flex-col items-center justify-center gap-1 text-xs",
                isActive ? "text-orange-600" : "text-gray-600"
              )}
            >
              <span className={cn(isActive ? "text-orange-500" : "text-gray-500")}>
                <Icon />
              </span>
              <span className="leading-none">{item.label}</span>
            </button>
          );
        })}

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="flex flex-col items-center justify-center gap-1 text-xs text-gray-600"
              aria-label="更多菜单"
            >
              <MoreVertical className="h-5 w-5 text-gray-500" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" side="top" className="w-52 bg-white">
            {more.length === 0 ? (
              <DropdownMenuItem disabled className="text-gray-400">
                暂无更多菜单
              </DropdownMenuItem>
            ) : (
              more.map((item) => {
                const Icon = getMenuIcon(item.icon);
                const isActive = pathname.startsWith(item.path);

                return (
                  <DropdownMenuItem
                    key={item.id}
                    onClick={() => router.push(item.path)}
                    className={cn("cursor-pointer", isActive && "bg-orange-50")}
                  >
                    <span className={cn("mr-2", isActive ? "text-orange-500" : "text-gray-500")}>
                      <Icon />
                    </span>
                    <span>{item.label}</span>
                  </DropdownMenuItem>
                );
              })
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}


