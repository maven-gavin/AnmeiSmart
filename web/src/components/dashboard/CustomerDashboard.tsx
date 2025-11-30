'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { customerService } from '@/service/customerService';
import { Message } from '@/types/chat';
import AppLayout from '../layout/AppLayout';
import { useAuthContext } from '@/contexts/AuthContext';

// 首页卡片组件
function DashboardCard({ 
  title, 
  count, 
  icon, 
  link, 
  color = 'orange' 
}: { 
  title: string; 
  count: number; 
  icon: React.ReactNode; 
  link: string; 
  color?: 'orange' | 'blue' | 'green' | 'purple'; 
}) {
  const colorClasses = {
    orange: 'bg-orange-50 text-orange-700',
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    purple: 'bg-purple-50 text-purple-700',
  };
  
  return (
    <Link href={link} className="block">
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md">
        <div className="flex items-center">
          <div className={`rounded-full p-3 ${colorClasses[color]}`}>
            {icon}
          </div>
          <div className="ml-4">
            <h3 className="text-lg font-medium text-gray-800">{title}</h3>
            <p className="text-3xl font-bold">{count}</p>
          </div>
        </div>
      </div>
    </Link>
  );
}

// 最近通知组件
function RecentNotifications({ messages }: { messages: Message[] }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-medium text-gray-800">最近通知</h3>
      <div className="divide-y divide-gray-100">
        {messages.length > 0 ? (
          messages.map((message) => (
            <div key={message.id} className="py-3">
              <p className="text-sm text-gray-800">{message.content}</p>
              <p className="text-xs text-gray-500">
                {new Date(message.timestamp).toLocaleString('zh-CN', {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </div>
          ))
        ) : (
          <p className="py-3 text-sm text-gray-500">暂无通知</p>
        )}
      </div>
    </div>
  );
}

export default function CustomerDashboard() {
  const { user } = useAuthContext();
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState<Message[]>([]);
  
  useEffect(() => {
    const loadData = async () => {
      try {
        const messagesData = await customerService.getSystemMessages();
        
        setNotifications(messagesData);
      } catch (error) {
        console.error('加载数据失败', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, []);
  
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }
  
  return (
    <AppLayout requiredRole={user?.currentRole}>
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">
          你好，{user?.name}
        </h1>
        <p className="text-gray-600">
          欢迎回到安美智享
        </p>
      </div>
      
      <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        <DashboardCard 
          title="我的消息" 
          count={notifications.length} 
          link="/chat"
          color="purple"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          }
        />
      </div>
      
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <RecentNotifications messages={notifications} />
      </div>
    </div>
    </AppLayout>
  );
} 