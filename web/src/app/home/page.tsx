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

  // 获取当前角色并标准化
  const role = user.currentRole;

  // 1. 优先匹配已知系统角色
  if (role === 'admin' || role === 'administrator') return <AdminDashboard />;
  if (role === 'doctor') return <DoctorDashboard />;
  if (role === 'consultant') return <ConsultantDashboard />;
  if (role === 'customer') return <CustomerDashboard />;
  if (role === 'operator') return <AdminDashboard />; // 运营人员暂时使用管理面板

  // 2. 根据角色特征模糊匹配
  if (role.includes('admin')) return <AdminDashboard />;
  if (role.includes('doctor')) return <DoctorDashboard />;
  if (role.includes('consultant')) return <ConsultantDashboard />;

  // 3. 根据用户权限标识判断
  if (user.isAdmin) return <AdminDashboard />;

  // 4. 默认回退到客户面板（最安全的默认值）
  return <CustomerDashboard />;
}
