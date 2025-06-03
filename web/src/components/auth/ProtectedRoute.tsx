'use client';

import { useState, useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { UserRole } from '@/types/auth';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRoles?: UserRole[];
}

/**
 * 保护路由组件，确保用户已登录并拥有所需权限
 */
export default function ProtectedRoute({ children, requiredRoles }: ProtectedRouteProps) {
  const { user, loading } = useAuthContext();
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    // 如果正在加载用户信息，暂时不处理
    if (loading) return;

    // 如果用户未登录且当前页面不是登录页，重定向到登录页
    if (!user && !pathname.startsWith('/login')) {
      router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
      return;
    }

    // 如果指定了所需角色，检查用户是否拥有这些角色
    if (user && requiredRoles && requiredRoles.length > 0) {
      const hasRequiredRole = requiredRoles.some(role => 
        user.roles.includes(role)
      );

      if (!hasRequiredRole) {
        // 用户没有所需角色权限，重定向到首页或访问拒绝页面
        router.push('/access-denied');
        return;
      }
    }

    setIsAuthorized(true);
  }, [user, loading, pathname, router, requiredRoles]);

  // 显示加载状态
  if (loading || !isAuthorized) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
          <p className="text-gray-600">正在加载...</p>
        </div>
      </div>
    );
  }

  // 用户已登录并有权限，渲染子组件
  return <>{children}</>;
} 