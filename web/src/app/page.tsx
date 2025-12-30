'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/service/authService';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // 检查登录状态
    const isLoggedIn = authService.isLoggedIn();
    const currentUser = authService.getCurrentUser();

    if (isLoggedIn && currentUser) {
      // 已登录，根据当前角色重定向
      // const currentRole = currentUser.currentRole;
      // const path = currentRole === 'consultant' ? '/consultant' :
      //             currentRole === 'doctor' ? '/doctor' : '/operator';
      router.push('/tasks');
    } else {
      // 未登录，重定向到登录页
      router.push('/login');
    }
  }, [router]);

  // 显示加载动画
  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-orange-100 via-orange-200 to-yellow-100">
      <div className="h-12 w-12 animate-spin rounded-full border-4 border-orange-500 border-t-transparent" />
    </main>
  );
}
