/** 判断菜单路径是否激活，避免 /admin/datahub 误匹配 /admin/datahub/watchlist */
export function isMenuPathActive(pathname: string, path: string): boolean {
  const normalizedPath = path.endsWith('/') && path.length > 1 ? path.slice(0, -1) : path
  const normalizedPathname = pathname.endsWith('/') && pathname.length > 1 ? pathname.slice(0, -1) : pathname

  if (normalizedPath === '/admin/datahub') {
    return normalizedPathname === '/admin/datahub'
  }

  if (normalizedPath === '/admin/datahub/monitor') {
    return normalizedPathname === '/admin/datahub/monitor' || normalizedPathname.startsWith('/admin/datahub/monitor/')
  }

  if (normalizedPath === '/admin/datahub/watchlist') {
    return normalizedPathname === '/admin/datahub/watchlist' || normalizedPathname.startsWith('/admin/datahub/watchlist/')
  }

  return normalizedPathname === normalizedPath || normalizedPathname.startsWith(`${normalizedPath}/`)
}
