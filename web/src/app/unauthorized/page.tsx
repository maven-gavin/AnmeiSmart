'use client';

import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';

export default function UnauthorizedPage() {
  const router = useRouter();
  const { user, logout } = useAuthContext();

  const handleBackHome = () => {
    // 智能重定向到用户对应角色的首页
    if (user) {
      const role = user.currentRole || (user.roles.length > 0 ? user.roles[0] : null);
      if (role) {
        const path = role === 'consultant' ? '/consultant' : 
                    role === 'doctor' ? '/doctor' : 
                    role === 'customer' ? '/customer' : 
                    role === 'admin' ? '/admin' : '/';
        router.push(path);
      } else {
        router.push('/');
      }
    } else {
      router.push('/');
    }
  };

  const handleSwitchAccount = () => {
    logout();
    router.push('/login');
  };

  const handleSwitchRole = () => {
    router.push('/login?switch=true');
  };

  return (
    <div className="flex h-screen flex-col items-center justify-center bg-gray-50 px-4">
      <div className="text-center">
        <div className="mb-6 flex justify-center">
          <div className="rounded-full bg-red-100 p-6">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="h-16 w-16 text-red-600" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="2" 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
              />
            </svg>
          </div>
        </div>
        <h1 className="mb-4 text-3xl font-bold text-gray-900">
          访问权限不足
        </h1>
        <p className="mb-8 max-w-md text-lg text-gray-600 mx-auto">
          {user 
            ? '很抱歉，您没有访问此页面的权限。请联系管理员或切换到具有相应权限的角色。' 
            : '请先登录以访问此页面。'
          }
        </p>
        <div className="flex flex-col space-y-3 sm:flex-row sm:space-x-4 sm:space-y-0 sm:justify-center">
          <Button
            className="bg-orange-500 hover:bg-orange-600"
            onClick={handleBackHome}
          >
            返回首页
          </Button>
          {!user ? (
            <Button
              variant="outline"
              onClick={() => router.push('/login')}
            >
              前往登录
            </Button>
          ) : (
            <>
              <Button
                variant="outline"
                onClick={handleSwitchRole}
              >
                切换角色
              </Button>
              <Button
                variant="outline"
                onClick={handleSwitchAccount}
              >
                切换账号
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
} 