'use client';

import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
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
import { cn } from '@/service/utils';

type TabType = 'basic' | 'security' | 'preferences' | 'digital-humans';

export default function ProfilePage() {
  const { user } = useAuthContext();
  const [activeTab, setActiveTab] = useState<TabType>('basic');
  // 移动端侧边栏显示/隐藏状态（默认隐藏，显示主内容区）
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  
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

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    // 移动端：选择标签后隐藏侧边栏，显示主内容区
    setIsSidebarOpen(false);
  };

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="flex h-full bg-gray-50 relative">
        {/* 侧边栏导航 - 移动端通过绝对定位控制显示/隐藏 */}
        <div className={cn(
          "absolute inset-y-0 left-0 z-50 transition-transform duration-300 ease-in-out",
          "md:relative md:z-auto",
          isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}>
          <div className="w-64 bg-white border-r border-gray-200 h-full shadow-lg md:shadow-none">
            <div className="p-6">
              {/* 标题行：个人中心 + 关闭按钮 */}
              <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold text-gray-800">个人中心</h1>
                {/* 移动端：关闭侧边栏按钮（淡黄色） */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsSidebarOpen(false)}
                  className="md:hidden text-yellow-400 hover:text-yellow-500 hover:bg-yellow-50/50 p-2"
                >
                  <ChevronRight className="h-5 w-5" />
                </Button>
              </div>
              <PersonalCenterTabs activeTab={activeTab} onTabChange={handleTabChange} />
            </div>
          </div>
        </div>
        
        {/* 移动端侧边栏打开时的遮罩层 */}
        {isSidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/50 z-40 md:hidden"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}

        {/* 主内容区域 */}
        <div className="flex-1 flex flex-col w-full md:w-auto">
          {/* 移动端工具栏 */}
          <div className="bg-white border-b border-gray-200 p-4 md:hidden">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsSidebarOpen(true)}
              className="text-yellow-400 hover:text-yellow-500 hover:bg-yellow-50/50 p-2"
            >
              <ChevronLeft className="h-5 w-5" />
            </Button>
          </div>
          
          <div className="flex-1 overflow-auto">
            <div className="p-8">
              {activeTab === 'basic' && <BasicInfoPanel />}
              {activeTab === 'security' && <SecurityPanel />}
              {activeTab === 'preferences' && <PreferencesPanel />}
              {activeTab === 'digital-humans' && <DigitalHumanManagementPanel />}
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
} 