 'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { doctorService } from '@/service/doctorService';
import { authService, roleOptions } from '@/service/authService';
import AppLayout from '../layout/AppLayout';
import { useAuthContext } from '@/contexts/AuthContext';

// 概览卡片组件
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

// 需要关注的患者组件
function NeedAttentionPatients({ patients }: { patients: any[] }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-medium text-gray-800">需关注患者</h3>
      <div className="divide-y divide-gray-100">
        {patients.length > 0 ? (
          patients.map((patient) => (
            <div key={patient.id} className="py-3">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium text-gray-800">{patient.name}</p>
                  <p className="text-sm text-gray-600">{patient.treatment}</p>
                  <p className="text-xs text-gray-500">{patient.date}</p>
                </div>
                <span className={`rounded-full px-2 py-1 text-xs ${
                  patient.urgency === 'high' 
                    ? 'bg-red-100 text-red-800' 
                    : patient.urgency === 'medium'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  {patient.urgency === 'high' ? '紧急' : patient.urgency === 'medium' ? '关注' : '一般'}
                </span>
              </div>
            </div>
          ))
        ) : (
          <p className="py-3 text-sm text-gray-500">暂无需要关注的患者</p>
        )}
      </div>
      <Link href="/doctor/patients" className="mt-4 block text-center text-sm font-medium text-orange-600 hover:text-orange-500">
        查看全部患者
      </Link>
    </div>
  );
}

export default function DoctorDashboard() {
  const { user } = useAuthContext();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [patientsCount, setPatientsCount] = useState(0);
  const [urgentPatients, setUrgentPatients] = useState<any[]>([]);
  const [roleDisplayName, setRoleDisplayName] = useState('医生');
  
  useEffect(() => {
    // 获取角色显示名称
    const fetchRoleInfo = async () => {
      if (user?.currentRole) {
        try {
          const roles = await authService.getRoleDetails();
          const currentRole = roles.find(r => r.name === user.currentRole);
          if (currentRole?.displayName) {
            setRoleDisplayName(currentRole.displayName);
          } else {
             // Fallback
             const staticOption = roleOptions.find(r => r.id === user.currentRole);
             if (staticOption) {
               // 移除"端"字，使称呼更自然
               setRoleDisplayName(staticOption.name.replace('端', ''));
             }
          }
        } catch (e) {
          console.error('Failed to fetch role details', e);
        }
      }
    };
    fetchRoleInfo();

    // TODO: 实现真实API调用
    setLoading(false);
    setPatientsCount(0);
    setUrgentPatients([]);
  }, []);
  
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-orange-500 border-t-transparent"></div>
          <p className="mt-4 text-gray-600">加载中，请稍候...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <div className="text-center">
          <div className="mx-auto mb-4 rounded-full bg-red-100 p-3 text-red-600">
            <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-lg font-medium text-gray-800">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 rounded-md bg-orange-500 px-4 py-2 font-medium text-white hover:bg-orange-600"
          >
            刷新页面
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <AppLayout requiredRole={user?.currentRole}>
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">
          你好，{user?.name || roleDisplayName}
        </h1>
        <p className="text-gray-600">
          欢迎回到安美智享{roleDisplayName}工作台，今天是 {new Date().toLocaleDateString('zh-CN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>
      
      <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2">
        <DashboardCard 
          title="我的患者" 
          count={patientsCount} 
          link="/doctor/patients"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          }
        />
      </div>
      
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <NeedAttentionPatients patients={urgentPatients} />
      </div>
    </div>
    </AppLayout>
  );
} 