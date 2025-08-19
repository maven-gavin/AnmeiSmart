'use client';

import { useState } from 'react';
import DigitalHumanList from './DigitalHumanList';
import DigitalHumanForm from './DigitalHumanForm';
import AgentConfigPanel from './AgentConfigPanel';
import { useDigitalHumans, CreateDigitalHumanRequest, UpdateDigitalHumanRequest } from '@/hooks/useDigitalHumans';
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

  const handleBackToOverview = () => {
    setActiveView('overview');
    setSelectedDigitalHuman(null);
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-orange-500"></div>
          <p className="text-gray-600">加载数字人数据...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {activeView !== 'overview' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={activeView === 'list' ? handleBackToOverview : handleBackToList}
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>返回{activeView === 'list' ? '概览' : '列表'}</span>
            </Button>
          )}
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {activeView === 'overview' && '数字人管理'}
              {activeView === 'list' && '数字人列表'}
              {activeView === 'create' && '创建数字人'}
              {activeView === 'edit' && '编辑数字人'}
              {activeView === 'agents' && '智能体配置'}
            </h2>
            <p className="text-gray-600 mt-1">
              {activeView === 'overview' && '管理您的数字人助手和智能体配置'}
              {activeView === 'list' && '查看和管理您的数字人'}
              {activeView === 'create' && '创建新的数字人助手'}
              {activeView === 'edit' && '修改数字人信息'}
              {activeView === 'agents' && '配置数字人的智能体能力'}
            </p>
          </div>
        </div>

        {activeView === 'overview' && (
          <div className="flex space-x-3">
            <Button
              variant="outline"
              onClick={() => setActiveView('list')}
              className="flex items-center space-x-2"
            >
              <Users className="h-4 w-4" />
              <span>管理数字人</span>
            </Button>
            <Button
              onClick={() => setActiveView('create')}
              className="flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>创建数字人</span>
            </Button>
          </div>
        )}

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

      {/* 内容区域 */}
      <div className="bg-white rounded-lg shadow-sm">
        {activeView === 'overview' && (
          <div className="p-6 space-y-6">
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
                    个人创建 {stats.personal} 个
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
                  <CardTitle className="text-sm font-medium">系统数字人</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.system}</div>
                  <p className="text-xs text-muted-foreground">
                    系统自动创建
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">智能体配置</CardTitle>
                  <Zap className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {digitalHumans.reduce((sum, dh) => sum + (dh.agent_count || 0), 0)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    总配置数量
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* 最近的数字人 */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">最近的数字人</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setActiveView('list')}
                >
                  查看全部
                </Button>
              </div>
              
              {digitalHumans.length === 0 ? (
                <div className="text-center py-8">
                  <Bot className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">还没有数字人</h3>
                  <p className="text-gray-500 mb-6">创建您的第一个数字人助手，开始智能对话体验</p>
                  <Button onClick={() => setActiveView('create')}>
                    <Plus className="h-4 w-4 mr-2" />
                    创建数字人
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {digitalHumans.slice(0, 3).map((digitalHuman) => (
                    <Card key={digitalHuman.id} className="hover:shadow-md transition-shadow cursor-pointer">
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-3 mb-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white font-semibold">
                            {digitalHuman.avatar ? (
                              <img
                                src={digitalHuman.avatar}
                                alt={digitalHuman.name}
                                className="w-full h-full rounded-full object-cover"
                              />
                            ) : (
                              digitalHuman.name.charAt(0).toUpperCase()
                            )}
                          </div>
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-900">{digitalHuman.name}</h4>
                            <p className="text-sm text-gray-600 truncate">
                              {digitalHuman.description || '暂无描述'}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex justify-between text-sm text-gray-500">
                          <span>会话: {digitalHuman.conversation_count}</span>
                          <span>消息: {digitalHuman.message_count}</span>
                        </div>
                        
                        <div className="mt-3 flex space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEditDigitalHuman(digitalHuman.id)}
                            className="flex-1"
                          >
                            编辑
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleConfigureAgents(digitalHuman.id)}
                            className="flex-1"
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
