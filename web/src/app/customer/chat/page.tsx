'use client';

import { Suspense, useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import ChatWindow from '@/components/chat/ChatWindow';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { useAuth } from '@/contexts/AuthContext';

export default function CustomerChatPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  
  // 检查用户是否已登录
  useEffect(() => {
    if (!user) {
      console.log('用户未登录，重定向到登录页面');
      setError('请先登录');
      // 可以添加一个延迟，避免闪烁
      const timer = setTimeout(() => {
        router.push('/login?redirect=/customer/chat');
      }, 1500);
      
      return () => clearTimeout(timer);
    }
    
    // 如果用户角色不是customer，重定向到相应页面
    if (user && user.currentRole !== 'customer') {
      console.log(`用户角色不是customer(${user.currentRole})，重定向到首页`);
      setError('无权访问顾客聊天页面');
      const timer = setTimeout(() => {
        router.push('/');
      }, 1500);
      
      return () => clearTimeout(timer);
    }
  }, [user, router]);
  
  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center bg-gray-50">
        <div className="text-red-500 text-lg mb-4">{error}</div>
        <div className="text-gray-500 text-sm">正在重定向...</div>
      </div>
    );
  }

  return (
    <Suspense fallback={<LoadingSpinner fullScreen />}>
      <div className="flex h-full flex-col bg-gray-50">
        {/* 聊天头部 */}
        <div className="border-b border-gray-200 bg-white p-4 shadow-sm">
          <div className="flex items-center">
            <div className="mr-3 rounded-full bg-orange-100 p-2">
              <svg className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-medium text-gray-800">在线咨询</h2>
              <p className="text-sm text-gray-500">与专业顾问实时沟通</p>
            </div>
          </div>
        </div>
        
        {/* 使用统一的ChatWindow组件 */}
        <div className="flex-1 overflow-hidden">
          <ChatWindow />
        </div>
      </div>
    </Suspense>
  );
} 