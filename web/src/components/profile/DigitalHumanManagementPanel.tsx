'use client';

import { useState } from 'react';
import DigitalHumanList from './DigitalHumanList';
import DigitalHumanForm from './DigitalHumanForm';
import AgentConfigPanel from './AgentConfigPanel';
import { useDigitalHumans } from '@/hooks/useDigitalHumans';
import type { CreateDigitalHumanRequest, UpdateDigitalHumanRequest } from '@/types/digital-human';
import { Button } from '@/components/ui/button';
import { Plus, ArrowLeft, Bot, Users, Zap, Activity } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function DigitalHumanManagementPanel() {
  const [activeView, setActiveView] = useState<'overview' | 'list' | 'create' | 'edit' | 'agents'>('overview');
  const [selectedDigitalHuman, setSelectedDigitalHuman] = useState<string | null>(null);
  
  const {
    digitalHumans,
    isLoading,
    stats,
    createDigitalHuman,
    updateDigitalHuman,
    deleteDigitalHuman
  } = useDigitalHumans();

  const handleCreateDigitalHuman = async (
    data: CreateDigitalHumanRequest | UpdateDigitalHumanRequest
  ) => {
    try {
      await createDigitalHuman(data as CreateDigitalHumanRequest);
      setActiveView('list');
    } catch (error) {
      console.error('创建数字人失败:', error);
    }
  };

  const handleUpdateDigitalHuman = async (
    data: CreateDigitalHumanRequest | UpdateDigitalHumanRequest
  ) => {
    if (!selectedDigitalHuman) return;
    
    try {
      await updateDigitalHuman(
        selectedDigitalHuman,
        data as UpdateDigitalHumanRequest
      );
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

  const handleBackToOverview = () => {
    setActiveView('overview');
    setSelectedDigitalHuman(null);
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
          <p className="text-sm text-gray-600">加载数字人数据...</p>
        </div>
      </div>
    );
  }

  const totalAgentConfigs = digitalHumans.reduce(
    (sum, dh) => sum + (dh.agent_count || 0),
    0
  );

  return (
    <div className="space-y-5">
      {/* 页面头部 */}
      <div className="flex items-center justify-between rounded-xl border bg-white/80 px-5 py-4 shadow-sm">
        <div className="flex items-center gap-4">
          {activeView !== 'overview' && (
            <Button
              variant="ghost"
              size="icon"
              onClick={activeView === 'list' ? handleBackToOverview : handleBackToList}
              className="mr-1 h-8 w-8 rounded-full text-gray-500 hover:bg-orange-50 hover:text-orange-600"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
          )}
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-semibold text-gray-900">
                {activeView === 'overview' && '数字人管理'}
                {activeView === 'list' && '数字人列表'}
                {activeView === 'create' && '创建数字人'}
                {activeView === 'edit' && '编辑数字人'}
                {activeView === 'agents' && '智能体配置'}
              </h2>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              {activeView === 'overview' && '统一管理数字人助手、统计指标与智能体配置'}
              {activeView === 'list' && '查看、编辑和管理您创建的数字人'}
              {activeView === 'create' && '为你的业务快速创建一个新的数字人助手'}
              {activeView === 'edit' && '调整数字人的基础信息和个性配置'}
              {activeView === 'agents' && '为数字人编排可复用的智能体能力'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {(activeView === 'overview' || activeView === 'list') && (
            <>
              <Button
                onClick={() => setActiveView('create')}
                className="flex items-center gap-2 bg-orange-500 hover:bg-orange-600"
              >
                <Plus className="h-4 w-4" />
                <span>创建数字人</span>
              </Button>
            </>
          )}
        </div>
      </div>

      {/* 内容区域 */}
      <div className="rounded-xl border bg-white/80 p-6 shadow-sm">
        {activeView === 'overview' && (
          <div className="space-y-8">
            {/* 统计卡片 */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
              <Card className="relative overflow-hidden border-none bg-gradient-to-br from-orange-50/90 to-white">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-xs font-medium text-gray-500">
                    总数字人
                  </CardTitle>
                  <div className="rounded-full bg-white/70 p-2 shadow-sm">
                    <Bot className="h-4 w-4 text-orange-500" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.total}
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    个人创建 {stats.user} 个
                  </p>
                </CardContent>
              </Card>

              <Card className="relative overflow-hidden border-none bg-gradient-to-br from-emerald-50/90 to-white">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-xs font-medium text-gray-500">
                    活跃数字人
                  </CardTitle>
                  <div className="rounded-full bg-white/70 p-2 shadow-sm">
                    <Activity className="h-4 w-4 text-emerald-500" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.active}
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    当前正在对话或运行中
                  </p>
                </CardContent>
              </Card>

              <Card className="relative overflow-hidden border-none bg-gradient-to-br from-sky-50/90 to-white">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-xs font-medium text-gray-500">
                    系统数字人
                  </CardTitle>
                  <div className="rounded-full bg-white/70 p-2 shadow-sm">
                    <Users className="h-4 w-4 text-sky-500" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.system}
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    系统为您预置的标准数字人
                  </p>
                </CardContent>
              </Card>

              <Card className="relative overflow-hidden border-none bg-gradient-to-br from-violet-50/90 to-white">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-xs font-medium text-gray-500">
                    智能体配置
                  </CardTitle>
                  <div className="rounded-full bg-white/70 p-2 shadow-sm">
                    <Zap className="h-4 w-4 text-violet-500" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-semibold text-gray-900">
                    {totalAgentConfigs}
                  </div>
                  <p className="mt-1 text-xs text-gray-500">总配置数量</p>
                </CardContent>
              </Card>
            </div>

            {/* 最近的数字人 */}
            <div>
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h3 className="text-base font-semibold text-gray-900">
                    最近的数字人
                  </h3>
                  <p className="mt-1 text-xs text-gray-500">
                    快速进入最近创建或修改的数字人进行配置
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setActiveView('list')}
                  className="border-gray-200 text-gray-700 hover:border-orange-200 hover:bg-orange-50 hover:text-orange-600"
                >
                  查看全部
                </Button>
              </div>

              {digitalHumans.length === 0 ? (
                <div className="rounded-lg border border-dashed bg-gray-50 py-10 text-center">
                  <Bot className="mx-auto mb-4 h-12 w-12 text-gray-300" />
                  <h3 className="mb-2 text-base font-medium text-gray-900">
                    还没有数字人
                  </h3>
                  <p className="mb-5 text-sm text-gray-500">
                    创建您的第一个数字人助手，开始智能对话体验
                  </p>
                  <Button
                    onClick={() => setActiveView('create')}
                    className="bg-orange-500 hover:bg-orange-600"
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    创建数字人
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {digitalHumans.slice(0, 3).map((digitalHuman) => (
                    <Card
                      key={digitalHuman.id}
                      className="group cursor-pointer border-gray-100 bg-gradient-to-br from-white to-orange-50/40 transition-all hover:border-orange-200 hover:shadow-md"
                    >
                      <CardContent className="flex h-40 flex-col justify-center">
                        <div className="mb-3 pt-6 flex items-center gap-3">
                          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-br from-orange-400 to-orange-600 text-sm font-semibold text-white shadow-sm">
                            {digitalHuman.avatar ? (
                              <img
                                src={digitalHuman.avatar}
                                alt={digitalHuman.name}
                                className="h-full w-full rounded-full object-cover"
                              />
                            ) : (
                              digitalHuman.name.charAt(0).toUpperCase()
                            )}
                          </div>
                          <div className="min-w-0 flex-1">
                            <h4 className="truncate text-sm font-semibold text-gray-900">
                              {digitalHuman.name}
                            </h4>
                            <p className="truncate text-xs text-gray-500">
                              {digitalHuman.description || '暂无描述'}
                            </p>
                          </div>
                        </div>

                        <div className="flex justify-between text-xs text-gray-500">
                          <span>会话 {digitalHuman.conversation_count}</span>
                          <span>消息 {digitalHuman.message_count}</span>
                          <span>智能体 {digitalHuman.agent_count || 0}</span>
                        </div>

                        <div className="mt-3 flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEditDigitalHuman(digitalHuman.id)}
                            className="flex-1 border-gray-200 text-gray-700 hover:border-orange-200 hover:bg-orange-50 hover:text-orange-600"
                          >
                            编辑
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleConfigureAgents(digitalHuman.id)}
                            className="flex-1 border-gray-200 text-gray-700 hover:border-orange-200 hover:bg-orange-50 hover:text-orange-600"
                          >
                            配置
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

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
  );
}
