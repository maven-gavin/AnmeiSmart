'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { useAuthContext } from '@/contexts/AuthContext';

export default function AccessDeniedPage() {
  const router = useRouter();
  const { user, logout } = useAuthContext();

  const handleBackHome = () => {
    router.push('/');
  };
  
  const handleGoToLogin = () => {
    logout();
  };

  return (
    <div className="flex h-screen flex-col items-center justify-center p-4">
      <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-red-100">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-12 w-12 text-red-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      
      <h1 className="mb-2 text-center text-3xl font-bold text-gray-800">访问被拒绝</h1>
      
      <p className="mb-8 max-w-md text-center text-gray-600">
        {user ? '您没有权限访问此页面。请联系管理员或切换到具有相应权限的角色。' : '请先登录以访问此页面。'}
      </p>
      
      <div className="flex space-x-4">
        <Button onClick={handleBackHome} variant="outline">
          返回首页
        </Button>
        
        {!user ? (
          <Button onClick={handleGoToLogin}>
            前往登录
          </Button>
        ) : (
          <Button onClick={() => router.push('/login?switch=true')}>
            切换角色
          </Button>
        )}
      </div>
    </div>
  );
} 