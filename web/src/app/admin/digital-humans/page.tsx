'use client';

import { useState } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import AppLayout from '@/components/layout/AppLayout';
import AdminDigitalHumanList from '@/components/admin/AdminDigitalHumanList';
import AdminDigitalHumanDetail from '@/components/admin/AdminDigitalHumanDetail';
import { useAdminDigitalHumans } from '@/hooks/useAdminDigitalHumans';
import { Button } from '@/components/ui/button';

import { 
  Shield, 
  Users, 
  Bot, 
  Activity, 
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function AdminDigitalHumansPage() {
  const [selectedDigitalHumanId, setSelectedDigitalHumanId] = useState<string | null>(null);

  const { user } = useAuthContext();
  
  const {
    digitalHumans,
    isLoading,
    stats,
    toggleDigitalHumanStatus,
    refreshDigitalHumans
  } = useAdminDigitalHumans();

  const handleDigitalHumanSelect = (digitalHumanId: string) => {
    setSelectedDigitalHumanId(digitalHumanId);
  };

  const handleStatusToggle = async (digitalHumanId: string, newStatus: string) => {
    try {
      await toggleDigitalHumanStatus(digitalHumanId, newStatus);
    } catch (error) {
      console.error('切换数字人状态失败:', error);
    }
  };

  const handleBackToList = () => {
    setSelectedDigitalHumanId(null);
  };

  if (isLoading) {
    return (
      <AppLayout requiredRole={user?.currentRole}>
        <div className="flex h-screen items-center justify-center">
          <div className="text-center">
            <div className="mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-orange-500"></div>
            <p className="text-gray-600">加载数字人数据...</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="container mx-auto px-4 py-6">
        {/* 页面头部 */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Shield className="h-8 w-8 text-orange-500" />
              <div>
                <h1 className="text-2xl font-bold text-gray-800">
                  {selectedDigitalHumanId ? '数字人详情' : '数字人管理'}
                </h1>
                <p className="text-gray-600 mt-1">
                  {selectedDigitalHumanId ? '查看和管理数字人详细信息' : '管理系统中所有数字人，进行状态控制和监督'}
                </p>
              </div>
            </div>

            {!selectedDigitalHumanId && (
              <div className="flex items-center space-x-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={refreshDigitalHumans}
                  className="flex items-center space-x-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span>刷新</span>
                </Button>
              </div>
            )}
          </div>
        </div>

        {!selectedDigitalHumanId ? (
          <div className="space-y-6">
            {/* 统计卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">总数字人</CardTitle>
                  <Bot className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.total}</div>
                  <p className="text-xs text-muted-foreground">
                    系统 {stats.system} 个，用户 {stats.user} 个
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">活跃数字人</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.active}</div>
                  <p className="text-xs text-muted-foreground">
                    正在运行中
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">用户数字人</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.user}</div>
                  <p className="text-xs text-muted-foreground">
                    用户创建
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">异常数字人</CardTitle>
                  <AlertCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.inactive + stats.maintenance}</div>
                  <p className="text-xs text-muted-foreground">
                    停用 {stats.inactive} 个，维护 {stats.maintenance} 个
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* 数字人列表 */}
            <div className="bg-white rounded-lg shadow-sm">
              <AdminDigitalHumanList
                digitalHumans={digitalHumans}
                onSelect={handleDigitalHumanSelect}
                onStatusToggle={handleStatusToggle}
                currentUserId={user?.id}
              />
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm">
            <AdminDigitalHumanDetail
              digitalHumanId={selectedDigitalHumanId}
              onBack={handleBackToList}
              onStatusToggle={handleStatusToggle}
              currentUserId={user?.id}
            />
          </div>
        )}
      </div>
    </AppLayout>
  );
}
