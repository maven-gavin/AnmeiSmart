'use client';

import { useState } from 'react';
import { useRoleGuard } from '@/hooks/useRoleGuard';
import RoleLayout from '@/components/layout/RoleLayout';
import { PersonalCenterTabs } from '@/components/profile/PersonalCenterTabs';
import { BasicInfoPanel } from '@/components/profile/BasicInfoPanel';
import { SecurityPanel } from '@/components/profile/SecurityPanel';
import { PreferencesPanel } from '@/components/profile/PreferencesPanel';
import DigitalHumanManagementPanel from '@/components/profile/DigitalHumanManagementPanel';

import LoadingSpinner from '@/components/ui/LoadingSpinner';
import AppLayout from '@/components/layout/AppLayout';
import { useAuthContext } from '@/contexts/AuthContext';

type TabType = 'basic' | 'security' | 'preferences' | 'digital-humans';

export default function ProfilePage() {
  const { user } = useAuthContext();
  const [activeTab, setActiveTab] = useState<TabType>('basic');
  
  // 个人中心需要用户登录但不限制特定角色
  const { isAuthorized, error, loading } = useRoleGuard({
    requireAuth: true,
    requiredRole: undefined // 所有角色都可以访问个人中心
  });

  if (loading || isAuthorized === null) {
    return (
      <RoleLayout>
        <div className="flex h-full items-center justify-center">
          <LoadingSpinner />
        </div>
      </RoleLayout>
    );
  }

  if (!isAuthorized) {
    return (
      <RoleLayout>
        <div className="flex h-full items-center justify-center">
          <div className="text-center">
            <p className="text-gray-600">{error || '无权访问'}</p>
          </div>
        </div>
      </RoleLayout>
    );
  }

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="flex h-full bg-gray-50">
        {/* 侧边栏导航 */}
        <div className="w-64 bg-white border-r border-gray-200">
          <div className="p-6">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">个人中心</h1>
            <PersonalCenterTabs activeTab={activeTab} onTabChange={setActiveTab} />
          </div>
        </div>

        {/* 主内容区域 */}
        <div className="flex-1 overflow-auto">
          <div className="p-8">
            {activeTab === 'basic' && <BasicInfoPanel />}
            {activeTab === 'security' && <SecurityPanel />}
            {activeTab === 'preferences' && <PreferencesPanel />}
            {activeTab === 'digital-humans' && <DigitalHumanManagementPanel />}
          </div>
        </div>
      </div>
    </AppLayout>
  );
} 