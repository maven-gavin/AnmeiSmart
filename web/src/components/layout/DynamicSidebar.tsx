'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronDown } from 'lucide-react'
import { getMenuIcon } from '@/utils/menuIcons'
import { useFilteredMenuItems } from '@/components/layout/useFilteredMenuItems'
import { isMenuPathActive } from '@/utils/menuPath'
import type { MenuItem } from '@/types/menu'

function SidebarLink({ item, nested = false }: { item: MenuItem; nested?: boolean }) {
  const pathname = usePathname()
  const isActive = isMenuPathActive(pathname, item.path)
  const Icon = getMenuIcon(item.icon)

  return (
    <Link
      href={item.path}
      className={`flex items-center rounded-md py-2 text-sm font-medium transition-colors ${
        nested ? 'px-3 pl-3' : 'px-3'
      } ${
        isActive
          ? 'bg-brand-soft text-brand-deep'
          : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
      }`}
    >
      {nested ? (
        <span
          className={`mr-3 h-1.5 w-1.5 shrink-0 rounded-full ${
            isActive ? 'bg-brand-primary' : 'bg-gray-300'
          }`}
        />
      ) : (
        <span className={`mr-3 shrink-0 ${isActive ? 'text-brand-primary' : 'text-gray-500'}`}>
          <Icon />
        </span>
      )}
      <span className="truncate">{item.label}</span>
    </Link>
  )
}

function SidebarGroup({ item }: { item: MenuItem }) {
  const pathname = usePathname()
  const children = item.children ?? []
  const isGroupActive = children.some((child) => isMenuPathActive(pathname, child.path))
  const [expanded, setExpanded] = useState(isGroupActive)
  const Icon = getMenuIcon(item.icon)

  useEffect(() => {
    if (isGroupActive) setExpanded(true)
  }, [isGroupActive])

  return (
    <div className="space-y-0.5">
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
        className={`flex w-full items-center rounded-md px-3 py-2 text-sm font-medium transition-colors ${
          isGroupActive
            ? 'bg-brand-soft/70 text-brand-deep'
            : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
        }`}
      >
        <span className={`mr-3 shrink-0 ${isGroupActive ? 'text-brand-primary' : 'text-gray-500'}`}>
          <Icon />
        </span>
        <span className="flex-1 truncate text-left">{item.label}</span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-gray-400 transition-transform duration-200 ${
            expanded ? 'rotate-180' : ''
          }`}
        />
      </button>
      {expanded && (
        <div className="ml-4 space-y-0.5 border-l border-gray-200 pl-2">
          {children.map((child) => (
            <SidebarLink key={child.id} item={child} nested />
          ))}
        </div>
      )}
    </div>
  )
}

export default function DynamicSidebar() {
  const filteredMenuItems = useFilteredMenuItems()

  const { mainItems, profileItem } = useMemo(() => {
    const profile = filteredMenuItems.find((item) => item.id === 'profile')
    const main = filteredMenuItems.filter((item) => item.id !== 'profile')
    return { mainItems: main, profileItem: profile }
  }, [filteredMenuItems])

  return (
    <div className="flex h-full w-64 shrink-0 flex-col border-r border-gray-200 bg-white shadow-sm">
      <nav className="flex min-h-0 flex-1 flex-col p-3">
        <div className="min-h-0 flex-1 space-y-1 overflow-y-auto pr-1">
          {mainItems.map((item) =>
            item.children?.length ? (
              <SidebarGroup key={item.id} item={item} />
            ) : (
              <SidebarLink key={item.id} item={item} />
            ),
          )}
        </div>

        {profileItem && (
          <div className="mt-3 shrink-0 border-t border-gray-200 pt-3">
            <SidebarLink item={profileItem} />
          </div>
        )}
      </nav>
    </div>
  )
}
