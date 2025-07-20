'use client';

import { useState, useEffect } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import AppLayout from '@/components/layout/AppLayout';

export default function AppointmentsPage() {
  const { user } = useAuthContext();
  
  const getPageTitle = () => {
    switch (user?.currentRole) {
      case 'doctor':
        return '预约管理';
      case 'customer':
        return '我的预约';
      default:
        return '预约管理';
    }
  };
  
  const getPageDescription = () => {
    switch (user?.currentRole) {
      case 'doctor':
        return '管理患者预约';
      case 'customer':
        return '查看和管理我的预约';
      default:
        return '预约管理';
    }
  };

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800">{getPageTitle()}</h1>
          <p className="text-gray-600">{getPageDescription()}</p>
        </div>
        
        {/* 根据角色显示不同内容 */}
        {user?.currentRole === 'customer' ? (
          // 这里放客户预约列表内容
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500">我的预约功能正在开发中...</p>
          </div>
        ) : (
          // 这里放医生端预约管理内容
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500">预约管理功能正在开发中...</p>
          </div>
        )}
      </div>
    </AppLayout>
  );
} 