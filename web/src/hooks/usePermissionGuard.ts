'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { authService } from '@/service/authService';

export interface PermissionGuardOptions {
  requiredPermission?: string;
  requiredPermissions?: string[];
  requiredRole?: string;
  requiredRoles?: string[];
  requireAuth?: boolean;
  redirectTo?: string;
  redirectDelay?: number;
}

export function usePermissionGuard(options: PermissionGuardOptions = {}) {
  const {
    requiredPermission,
    requiredPermissions,
    requiredRole,
    requiredRoles,
    requireAuth = true,
    redirectTo = '/login',
    redirectDelay = 1500
  } = options;

  const { user, loading: authLoading } = useAuthContext();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);

  useEffect(() => {
    // 等待认证完成
    if (authLoading) {
      return;
    }

    // 检查登录状态
    if (requireAuth && !authService.isLoggedIn()) {
      setError('请先登录');
      setIsAuthorized(false);
      const timer = setTimeout(() => {
        router.push(redirectTo);
      }, redirectDelay);
      
      return () => clearTimeout(timer);
    }

    // 检查权限
    if (user) {
      let hasPermission = true;
      let errorMessage = '';

      // 检查单个权限
      if (requiredPermission && !user.permissions?.includes(requiredPermission)) {
        hasPermission = false;
        errorMessage = `缺少权限: ${requiredPermission}`;
      }

      // 检查多个权限（需要全部拥有）
      if (hasPermission && requiredPermissions && requiredPermissions.length > 0) {
        const missingPermissions = requiredPermissions.filter(
          permission => !user.permissions?.includes(permission)
        );
        if (missingPermissions.length > 0) {
          hasPermission = false;
          errorMessage = `缺少权限: ${missingPermissions.join(', ')}`;
        }
      }

      // 检查单个角色
      if (hasPermission && requiredRole && !user.roles?.includes(requiredRole)) {
        hasPermission = false;
        errorMessage = `缺少角色: ${requiredRole}`;
      }

      // 检查多个角色（需要拥有任意一个）
      if (hasPermission && requiredRoles && requiredRoles.length > 0) {
        const hasAnyRole = requiredRoles.some(role => user.roles?.includes(role));
        if (!hasAnyRole) {
          hasPermission = false;
          errorMessage = `缺少角色: ${requiredRoles.join(' 或 ')}`;
        }
      }

      if (!hasPermission) {
        setError(errorMessage);
        setIsAuthorized(false);
        const timer = setTimeout(() => {
          router.push('/unauthorized');
        }, redirectDelay);
        
        return () => clearTimeout(timer);
      }
    }

    // 通过所有检查
    setError(null);
    setIsAuthorized(true);
  }, [
    authLoading, 
    user, 
    requiredPermission, 
    requiredPermissions, 
    requiredRole, 
    requiredRoles, 
    requireAuth, 
    redirectTo, 
    redirectDelay, 
    router
  ]);

  return {
    isAuthorized,
    error,
    loading: authLoading || isAuthorized === null
  };
}

// 便捷的权限检查Hook
export function useHasPermission(permission: string): boolean {
  const { user } = useAuthContext();
  return user?.permissions?.includes(permission) || false;
}

// 便捷的角色检查Hook
export function useHasRole(role: string): boolean {
  const { user } = useAuthContext();
  return user?.roles?.includes(role) || false;
}

// 便捷的管理员检查Hook
export function useIsAdmin(): boolean {
  const { user } = useAuthContext();
  return user?.isAdmin || false;
}

// 便捷的任意权限检查Hook
export function useHasAnyPermission(permissions: string[]): boolean {
  const { user } = useAuthContext();
  if (!user?.permissions || permissions.length === 0) {
    return false;
  }
  return permissions.some(permission => user.permissions.includes(permission));
}

// 便捷的任意角色检查Hook
export function useHasAnyRole(roles: string[]): boolean {
  const { user } = useAuthContext();
  if (!user?.roles || roles.length === 0) {
    return false;
  }
  return roles.some(role => user.roles.includes(role));
}
