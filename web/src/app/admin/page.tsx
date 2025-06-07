'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import Link from 'next/link';
import { ChatWebSocketStatus } from '@/components/chat/ChatWebSocketStatus';

interface AdminCard {
  title: string;
  description: string;
  icon: React.ReactNode;
  link: string;
}

export default function AdminDashboard() {
  const { user } = useAuthContext();
  const router = useRouter();

  // 检查用户是否有管理员权限
  useEffect(() => {
    if (user && !user.roles.includes('admin')) {
      router.push('/unauthorized');
    }
  }, [user, router]);

  const adminCards: AdminCard[] = [
    {
      title: '用户管理',
      description: '创建、编辑和管理系统用户',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      ),
      link: '/admin/users'
    },
    {
      title: '角色管理',
      description: '管理系统角色与权限',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      link: '/admin/roles'
    },
    {
      title: '系统设置',
      description: '配置系统参数与AI模型',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      link: '/admin/settings'
    },
    {
      title: '数据统计',
      description: '查看系统使用数据与统计',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      link: '/admin/statistics'
    }
  ];

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">管理员控制面板</h1>
        <ChatWebSocketStatus />
      </div>
      
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        {adminCards.map((card, index) => (
          <Link 
            key={index} 
            href={card.link}
            className="flex flex-col rounded-lg border border-gray-200 bg-white p-6 shadow transition-all hover:shadow-md"
          >
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-orange-50">
              {card.icon}
            </div>
            <h2 className="mb-2 text-xl font-semibold text-gray-800">{card.title}</h2>
            <p className="mb-4 text-gray-600">{card.description}</p>
            <div className="mt-auto flex items-center text-orange-500">
              <span>查看详情</span>
              <svg xmlns="http://www.w3.org/2000/svg" className="ml-1 h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
            </div>
          </Link>
        ))}
      </div>
      
      <div className="mt-8 rounded-lg border border-gray-200 bg-white p-6 shadow">
        <h2 className="mb-4 text-xl font-semibold text-gray-800">系统概览</h2>
        <div className="flex flex-wrap gap-4">
          <div className="flex min-w-[200px] flex-1 flex-col rounded-lg bg-blue-50 p-4">
            <p className="text-sm text-gray-600">总用户数</p>
            <p className="text-2xl font-bold text-blue-600">128</p>
          </div>
          <div className="flex min-w-[200px] flex-1 flex-col rounded-lg bg-green-50 p-4">
            <p className="text-sm text-gray-600">今日活跃用户</p>
            <p className="text-2xl font-bold text-green-600">24</p>
          </div>
          <div className="flex min-w-[200px] flex-1 flex-col rounded-lg bg-purple-50 p-4">
            <p className="text-sm text-gray-600">总预约数</p>
            <p className="text-2xl font-bold text-purple-600">86</p>
          </div>
          <div className="flex min-w-[200px] flex-1 flex-col rounded-lg bg-orange-50 p-4">
            <p className="text-sm text-gray-600">系统版本</p>
            <p className="text-2xl font-bold text-orange-600">v1.0.0</p>
          </div>
        </div>
      </div>
    </div>
  );
} 