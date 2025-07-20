'use client';

import { useParams } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import DoctorDashboard from '@/components/dashboard/DoctorDashboard';
import ConsultantDashboard from '@/components/dashboard/ConsultantDashboard';
import CustomerDashboard from '@/components/dashboard/CustomerDashboard';
import AdminDashboard from '@/components/dashboard/AdminDashboard';

export default function DynamicHomePage() {
  const { user } = useAuthContext();

  // 验证用户权限
  if (!user || user.currentRole == undefined) {
    return <div>无权访问</div>;
  }

  // 根据角色渲染对应的欢迎页
  switch (user.currentRole) {
    case 'doctor':
      return <DoctorDashboard />;
    case 'consultant':
      return <ConsultantDashboard />;
    case 'customer':
      return <CustomerDashboard />;
    case 'admin':
      return <AdminDashboard />;
    default:
      return <div>未知角色</div>;
  }
} 