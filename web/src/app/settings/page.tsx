'use client';

import { useState } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import AppLayout from '@/components/layout/AppLayout';
import GeneralSettingsPanel from '@/components/settings/GeneralSettingsPanel';
import SecuritySettingsPanel from '@/components/settings/SecuritySettingsPanel';


import { useSystemSettings } from '@/hooks/useSystemSettings';


export default function SystemSettingsPage() {
  const [activeTab, setActiveTab] = useState('general');
  const { user } = useAuthContext();
  
  // 使用自定义hooks管理状态
  const {
    settings,
    isLoading,
    isSubmitting,
    updateGeneralSettings,
    updateSecuritySettings
  } = useSystemSettings();





  // 显示加载状态
  if (isLoading) {
    return (
      <AppLayout requiredRole={user?.currentRole}>
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-orange-500"></div>
          <p className="text-gray-600">加载系统设置...</p>
        </div>
      </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout requiredRole={user?.currentRole}>
    <div className="container mx-auto px-4 py-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-800">系统设置</h1>
      
        {/* Tab导航 */}
      <div className="mb-6 flex border-b">
        <button
            className={`mr-4 py-2 px-4 font-medium ${
              activeTab === 'general' 
                ? 'border-b-2 border-orange-500 text-orange-500' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          onClick={() => setActiveTab('general')}
        >
          基本设置
        </button>
        <button
            className={`mr-4 py-2 px-4 font-medium ${
              activeTab === 'security' 
                ? 'border-b-2 border-orange-500 text-orange-500' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          onClick={() => setActiveTab('security')}
        >
          安全与访问控制
        </button>
        </div>
        
        {/* 内容区域 */}
        <div className="min-h-96">
          {/* 基本设置面板 */}
          {activeTab === 'general' && (
            <GeneralSettingsPanel
              settings={{
                siteName: settings.siteName,
                logoUrl: settings.logoUrl,
                maintenanceMode: (settings as any).maintenanceMode ?? false
              }}
              onSubmit={updateGeneralSettings}
              isSubmitting={isSubmitting}
            />
          )}

          {/* 安全设置面板 */}
          {activeTab === 'security' && (
            <SecuritySettingsPanel
              settings={{
                userRegistrationEnabled: settings.userRegistrationEnabled
              }}
              onSubmit={updateSecuritySettings}
              isSubmitting={isSubmitting}
            />
          )}
        </div>
    </div>
    </AppLayout>
  );
} 