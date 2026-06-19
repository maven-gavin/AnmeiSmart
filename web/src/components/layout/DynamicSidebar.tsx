'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronDown } from 'lucide-react'
import { getMenuIcon } from '@/utils/menuIcons'
import { useFilteredMenuItems } from '@/components/layout/useFilteredMenuItems'
import { isMenuPathActive } from '@/utils/menuPath'
import type { MenuItem } from '@/types/menu'

function SidebarLink({ item, indented = false }: { item: MenuItem; indented?: boolean }) {
  const pathname = usePathname()
  const isActive = isMenuPathActive(pathname, item.path)
  const Icon = getMenuIcon(item.icon)

  return (
    <Link
      href={item.path}
      className={`flex items-center rounded-md px-3 py-2 text-sm font-medium ${
        indented ? 'ml-4' : ''
      } ${
        isActive
          ? 'bg-orange-50 text-orange-700'
          : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
      }`}
    >
      {!indented && (
        <span className={`mr-3 ${isActive ? 'text-orange-500' : 'text-gray-500'}`}>
          <Icon />
        </span>
      )}
      {indented && <span className="mr-3 w-5" />}
      {item.label}
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
    <div className="space-y-1">
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        className={`flex w-full items-center rounded-md px-3 py-2 text-sm font-medium ${
          isGroupActive
            ? 'bg-orange-50 text-orange-700'
            : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
        }`}
      >
        <span className={`mr-3 ${isGroupActive ? 'text-orange-500' : 'text-gray-500'}`}>
          <Icon />
        </span>
        <span className="flex-1 text-left">{item.label}</span>
        <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </button>
      {expanded && (
        <div className="space-y-1 border-l border-gray-100 ml-5 pl-1">
          {children.map((child) => (
            <SidebarLink key={child.id} item={child} indented />
          ))}
        </div>
      )}
    </div>
  )
}

export default function DynamicSidebar() {
  const filteredMenuItems = useFilteredMenuItems()

  return (
    <div className="w-64 flex-shrink-0 bg-white shadow-sm">
      <nav className="flex h-full flex-col border-r border-gray-200 p-4">
        <div className="space-y-1">
          {filteredMenuItems.map((item) =>
            item.children?.length ? (
              <SidebarGroup key={item.id} item={item} />
            ) : (
              <SidebarLink key={item.id} item={item} />
            ),
          )}
        </div>
      </nav>
    </div>
  )
}
