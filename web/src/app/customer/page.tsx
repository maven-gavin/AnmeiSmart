'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { customerService } from '@/service/customerService';
import { authService } from '@/service/authService';
import { CustomerAppointment, Treatment, TreatmentPlan } from '@/types/customer';
import { Message } from '@/types/chat';

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

// 近期预约组件
function UpcomingAppointments({ appointments }: { appointments: CustomerAppointment[] }) {
  // 获取未来的预约
  const futureAppointments = appointments.filter(
    (appointment) => appointment.status !== 'canceled' && appointment.status !== 'completed'
  );
  
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-medium text-gray-800">近期预约</h3>
      <div className="divide-y divide-gray-100">
        {futureAppointments.length > 0 ? (
          futureAppointments.map((appointment) => (
            <div key={appointment.id} className="py-3">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium text-gray-800">{appointment.title}</p>
                  <p className="text-sm text-gray-600">
                    {appointment.date} {appointment.time}
                  </p>
                  <p className="text-xs text-gray-500">
                    {appointment.type === 'consultation' 
                      ? `咨询：${appointment.consultant}` 
                      : `${appointment.type === 'treatment' ? '治疗' : '复诊'}：${appointment.doctor}`}
                  </p>
                </div>
                <span className={`rounded-full px-2 py-1 text-xs ${
                  appointment.status === 'confirmed' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {appointment.status === 'confirmed' ? '已确认' : '待确认'}
                </span>
              </div>
            </div>
          ))
        ) : (
          <p className="py-3 text-sm text-gray-500">暂无预约</p>
        )}
      </div>
      {futureAppointments.length > 0 && (
        <Link href="/customer/appointments" className="mt-4 block text-center text-sm font-medium text-orange-600 hover:text-orange-500">
          查看全部预约
        </Link>
      )}
    </div>
  );
}

export default function CustomerDashboard() {
  const [loading, setLoading] = useState(true);
  const [treatments, setTreatments] = useState<Treatment[]>([]);
  const [plans, setPlans] = useState<TreatmentPlan[]>([]);
  const [appointments, setAppointments] = useState<CustomerAppointment[]>([]);
  const [notifications, setNotifications] = useState<Message[]>([]);
  const [user, setUser] = useState(authService.getCurrentUser());
  
  useEffect(() => {
    const loadData = async () => {
      try {
        const treatmentsData = await customerService.getTreatments();
        const plansData = await customerService.getTreatmentPlans();
        const appointmentsData = await customerService.getAppointments();
        const messagesData = await customerService.getSystemMessages();
        
        setTreatments(treatmentsData);
        setPlans(plansData);
        setAppointments(appointmentsData);
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
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">
          你好，{user?.name}
        </h1>
        <p className="text-gray-600">
          欢迎回到安美智享，查看您的个人医美治疗信息
        </p>
      </div>
      
      <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <DashboardCard 
          title="治疗记录" 
          count={treatments.length} 
          link="/customer/treatments"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          }
        />
        
        <DashboardCard 
          title="治疗方案" 
          count={plans.length} 
          link="/customer/plans"
          color="blue"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        
        <DashboardCard 
          title="我的预约" 
          count={appointments.length} 
          link="/customer/appointments"
          color="green"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          }
        />
        
        <DashboardCard 
          title="在线咨询" 
          count={notifications.length} 
          link="/customer/chat"
          color="purple"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          }
        />
      </div>
      
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <UpcomingAppointments appointments={appointments} />
        <RecentNotifications messages={notifications} />
      </div>
    </div>
  );
} 