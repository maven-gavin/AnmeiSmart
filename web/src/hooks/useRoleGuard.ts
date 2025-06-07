'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { authService } from '@/service/authService';

export interface RoleGuardOptions {
  requiredRole?: string;
  requireAuth?: boolean;
  redirectTo?: string;
  redirectDelay?: number;
}

export function useRoleGuard(options: RoleGuardOptions = {}) {
  const {
    requiredRole,
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

    // 检查用户角色
    if (requiredRole && user && user.currentRole !== requiredRole) {
      setError(`无权访问，需要${requiredRole}角色`);
      setIsAuthorized(false);
      const timer = setTimeout(() => {
        router.push('/');
      }, redirectDelay);
      
      return () => clearTimeout(timer);
    }

    // 通过所有检查
    setError(null);
    setIsAuthorized(true);
  }, [authLoading, user, requiredRole, requireAuth, redirectTo, redirectDelay, router]);

  return {
    isAuthorized,
    error,
    loading: authLoading || isAuthorized === null
  };
} 