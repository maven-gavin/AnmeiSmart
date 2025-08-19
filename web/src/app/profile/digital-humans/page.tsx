'use client';

import { useState } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import AppLayout from '@/components/layout/AppLayout';
import DigitalHumanList from '@/components/profile/DigitalHumanList';
import DigitalHumanForm from '@/components/profile/DigitalHumanForm';
import AgentConfigPanel from '@/components/profile/AgentConfigPanel';
import { useDigitalHumans, CreateDigitalHumanRequest, UpdateDigitalHumanRequest } from '@/hooks/useDigitalHumans';
import { Button } from '@/components/ui/button';
import { Plus, ArrowLeft } from 'lucide-react';

export default function DigitalHumanManagementPage() {
  const [activeView, setActiveView] = useState<'list' | 'create' | 'edit' | 'agents'>('list');
  const [selectedDigitalHuman, setSelectedDigitalHuman] = useState<string | null>(null);
  const { user } = useAuthContext();
  
  const {
    digitalHumans,
    isLoading,
    createDigitalHuman,
    updateDigitalHuman,
    deleteDigitalHuman,
    refreshDigitalHumans
  } = useDigitalHumans();

  const handleCreateDigitalHuman = async (data: CreateDigitalHumanRequest) => {
    try {
      await createDigitalHuman(data);
      setActiveView('list');
    } catch (error) {
      console.error('创建数字人失败:', error);
    }
  };

  const handleUpdateDigitalHuman = async (data: UpdateDigitalHumanRequest) => {
    if (!selectedDigitalHuman) return;
    
    try {
      await updateDigitalHuman(selectedDigitalHuman, data);
      setActiveView('list');
      setSelectedDigitalHuman(null);
    } catch (error) {
      console.error('更新数字人失败:', error);
    }
  };

  const handleDeleteDigitalHuman = async (id: string) => {
    try {
      await deleteDigitalHuman(id);
    } catch (error) {
      console.error('删除数字人失败:', error);
    }
  };

  const handleEditDigitalHuman = (id: string) => {
    setSelectedDigitalHuman(id);
    setActiveView('edit');
  };

  const handleConfigureAgents = (id: string) => {
    setSelectedDigitalHuman(id);
    setActiveView('agents');
  };

  const handleBackToList = () => {
    setActiveView('list');
    setSelectedDigitalHuman(null);
  };

  if (isLoading) {
    return (
      <AppLayout requiredRole={user?.currentRole}>
        <div className="flex h-screen items-center justify-center">
          <div className="text-center">
            <div className="mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-orange-500"></div>
            <p className="text-gray-600">加载数字人列表...</p>
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
              {activeView !== 'list' && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleBackToList}
                  className="flex items-center space-x-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  <span>返回列表</span>
                </Button>
              )}
              <div>
                <h1 className="text-2xl font-bold text-gray-800">
                  {activeView === 'list' && '数字人管理'}
                  {activeView === 'create' && '创建数字人'}
                  {activeView === 'edit' && '编辑数字人'}
                  {activeView === 'agents' && '智能体配置'}
                </h1>
                <p className="text-gray-600 mt-1">
                  {activeView === 'list' && '管理您的数字人助手'}
                  {activeView === 'create' && '创建新的数字人助手'}
                  {activeView === 'edit' && '修改数字人信息'}
                  {activeView === 'agents' && '配置数字人的智能体能力'}
                </p>
              </div>
            </div>

            {activeView === 'list' && (
              <Button
                onClick={() => setActiveView('create')}
                className="flex items-center space-x-2"
              >
                <Plus className="h-4 w-4" />
                <span>创建数字人</span>
              </Button>
            )}
          </div>
        </div>

        {/* 内容区域 */}
        <div className="bg-white rounded-lg shadow-sm">
          {activeView === 'list' && (
            <DigitalHumanList
              digitalHumans={digitalHumans}
              onEdit={handleEditDigitalHuman}
              onDelete={handleDeleteDigitalHuman}
              onConfigureAgents={handleConfigureAgents}
            />
          )}

          {activeView === 'create' && (
            <DigitalHumanForm
              onSubmit={handleCreateDigitalHuman}
              onCancel={handleBackToList}
            />
          )}

          {activeView === 'edit' && selectedDigitalHuman && (
            <DigitalHumanForm
              digitalHuman={digitalHumans.find(dh => dh.id === selectedDigitalHuman)}
              onSubmit={handleUpdateDigitalHuman}
              onCancel={handleBackToList}
            />
          )}

          {activeView === 'agents' && selectedDigitalHuman && (
            <AgentConfigPanel
              digitalHumanId={selectedDigitalHuman}
              onBack={handleBackToList}
            />
          )}
        </div>
      </div>
    </AppLayout>
  );
}
