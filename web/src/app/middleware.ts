import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// 中间件函数
export function middleware(request: NextRequest) {
  // 获取当前路径
  const { pathname } = request.nextUrl
  
  // 获取存储的token
  const token = request.cookies.get('auth_token')?.value
  const authUser = request.cookies.get('auth_user')?.value
  
  // 不需要身份验证的路径
  const publicPaths = ['/login', '/register', '/forgot-password', '/reset-password', '/api']
  const isPublicPath = publicPaths.some(path => pathname.startsWith(path))
  
  // 处理静态资源路径
  if (
    pathname.startsWith('/_next') || 
    pathname.startsWith('/favicon.ico') ||
    pathname.startsWith('/assets')
  ) {
    return NextResponse.next()
  }
  
  // 如果路径需要验证但没有token，重定向到登录页
  if (!isPublicPath && (!token || !authUser)) {
    console.log(`[Middleware] 未登录，重定向到登录页: ${pathname}`)
    const url = new URL('/login', request.url)
    url.searchParams.set('redirect', pathname)
    return NextResponse.redirect(url)
  }
  
  // 如果已登录并访问登录页，重定向到首页
  if (pathname === '/login' && token && authUser) {
    console.log('[Middleware] 已登录，重定向到首页')
    return NextResponse.redirect(new URL('/', request.url))
  }
  
  // 正常请求继续处理
  return NextResponse.next()
}

// 配置匹配路径，排除API路由和静态资源
export const config = {
  matcher: [
    // 需要进行身份验证检查的路径
    '/((?!_next/static|_next/image|favicon.ico|api/).*)',
  ],
} 