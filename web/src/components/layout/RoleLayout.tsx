'use client';

import { ReactNode, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/service/authService';
import RoleHeader from './RoleHeader';
import { UserRole } from '@/types/auth';

interface RoleLayoutProps {
  children: ReactNode;
  requiredRole?: UserRole;
}

export default function RoleLayout({ children, requiredRole }: RoleLayoutProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  // 检查用户认证状态和角色权限
  useEffect(() => {
    const checkAuth = () => {
      const isLoggedIn = authService.isLoggedIn();
      const currentUser = authService.getCurrentUser();

      if (!isLoggedIn || !currentUser) {
        router.push('/login');
        return;
      }

      if (requiredRole && currentUser.currentRole !== requiredRole) {
        // 如果用户没有所需角色，但拥有该角色权限，则切换到该角色
        if (currentUser.roles.includes(requiredRole)) {
          authService.switchRole(requiredRole).then(() => {
            setLoading(false);
          });
        } else {
          // 如果用户没有所需角色权限，则跳转到默认页面
          router.push('/');
        }
      } else {
        setLoading(false);
      }
    };

    checkAuth();
  }, [router, requiredRole]);

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-orange-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-screen max-h-screen flex-col overflow-hidden bg-gray-50">
      <RoleHeader />
      <main className="flex flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  );
} 