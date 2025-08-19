'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { AgentConfig } from '@/service/agentConfigService';

interface AgentConfigPanelProps {
  configs: AgentConfig[];
  onCreateConfig: (config: Omit<AgentConfig, 'id' | 'createdAt' | 'updatedAt'> & { apiKey: string }) => Promise<void>;
  onUpdateConfig: (id: string, config: Partial<AgentConfig> & { apiKey?: string }) => Promise<void>;
  onDeleteConfig: (id: string) => Promise<void>;
  onTestConnection: (config: AgentConfig) => Promise<void>;
}

export default function AgentConfigPanel({
  configs,
  onCreateConfig,
  onUpdateConfig,
  onDeleteConfig,
  onTestConnection
}: AgentConfigPanelProps) {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<AgentConfig | null>(null);
  const [newConfig, setNewConfig] = useState<Omit<AgentConfig, 'id' | 'createdAt' | 'updatedAt'> & { apiKey: string }>({
    environment: 'dev',
    appId: '',
    appName: '',
    apiKey: '',
    baseUrl: 'http://localhost/v1',
    timeoutSeconds: 30,
    maxRetries: 3,
    enabled: true,
    description: ''
  });

  const [searchTerm, setSearchTerm] = useState('');
  const [environmentFilter, setEnvironmentFilter] = useState<string>('all');
  const [filteredConfigs, setFilteredConfigs] = useState<AgentConfig[]>([]);
  const [allConfigs, setAllConfigs] = useState<AgentConfig[]>([]);

  // 更新配置列表
  useEffect(() => {
    setAllConfigs(configs);
  }, [configs]);

  // 过滤配置
  useEffect(() => {
    let filtered = allConfigs;

    // 按搜索词过滤
    if (searchTerm) {
      filtered = filtered.filter(config =>
        config.appName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        config.appId.toLowerCase().includes(searchTerm.toLowerCase()) ||
        config.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // 按环境过滤
    if (environmentFilter !== 'all') {
      filtered = filtered.filter(config => config.environment === environmentFilter);
    }

    setFilteredConfigs(filtered);
  }, [allConfigs, searchTerm, environmentFilter]);

  const handleCreateConfig = async () => {
    try {
      await onCreateConfig(newConfig);
      setIsCreateDialogOpen(false);
      resetNewConfig();
    } catch (error) {
      console.error('创建配置失败:', error);
    }
  };

  const handleUpdateConfig = async () => {
    if (!editingConfig) return;
    
    try {
      const updateData: Partial<AgentConfig> & { apiKey?: string } = {
        environment: editingConfig.environment,
        appId: editingConfig.appId,
        appName: editingConfig.appName,
        baseUrl: editingConfig.baseUrl,
        timeoutSeconds: editingConfig.timeoutSeconds,
        maxRetries: editingConfig.maxRetries,
        enabled: editingConfig.enabled,
        description: editingConfig.description
      };
      
      await onUpdateConfig(editingConfig.id, updateData);
      setIsEditDialogOpen(false);
      setEditingConfig(null);
    } catch (error) {
      console.error('更新配置失败:', error);
    }
  };

  const handleToggleEnabled = async (config: AgentConfig) => {
    try {
      await onUpdateConfig(config.id, { enabled: !config.enabled });
    } catch (error) {
      console.error('切换启用状态失败:', error);
    }
  };

  const openEditDialog = (config: AgentConfig) => {
    setEditingConfig({ ...config });
    setIsEditDialogOpen(true);
  };

  const resetNewConfig = () => {
    setNewConfig({
      environment: 'dev',
      appId: '',
      appName: '',
      apiKey: '',
      baseUrl: 'http://localhost/v1',
      timeoutSeconds: 30,
      maxRetries: 3,
      enabled: true,
      description: ''
    });
  };

  const handleDeleteConfig = async (config: AgentConfig) => {
    if (confirm('确定要删除这个Agent配置吗？')) {
      try {
        await onDeleteConfig(config.id);
      } catch (error) {
        console.error('删除配置失败:', error);
      }
    }
  };

  const getEnvironmentColor = (environment: string) => {
    switch (environment) {
      case 'dev': return 'bg-blue-100 text-blue-800';
      case 'test': return 'bg-yellow-100 text-yellow-800';
      case 'prod': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* 头部操作区 */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Agent配置管理</h2>
          <p className="text-gray-600">管理Agent应用的配置信息</p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => resetNewConfig()}>
              添加配置
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>创建Agent配置</DialogTitle>
              <DialogDescription>
                添加新的Agent应用配置
              </DialogDescription>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="environment">环境</Label>
                <Select value={newConfig.environment} onValueChange={(value) => setNewConfig(prev => ({ ...prev, environment: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dev">开发环境</SelectItem>
                    <SelectItem value="test">测试环境</SelectItem>
                    <SelectItem value="prod">生产环境</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="appId">应用ID</Label>
                <Input
                  id="appId"
                  value={newConfig.appId}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, appId: e.target.value }))}
                  placeholder="例如: agent-chat-app"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="appName">应用名称</Label>
                <Input
                  id="appName"
                  value={newConfig.appName}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, appName: e.target.value }))}
                  placeholder="例如: 聊天助手"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="apiKey">API密钥</Label>
                <Input
                  id="apiKey"
                  type="password"
                  value={newConfig.apiKey}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, apiKey: e.target.value }))}
                  placeholder="输入API密钥"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="baseUrl">基础URL</Label>
                <Input
                  id="baseUrl"
                  value={newConfig.baseUrl}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, baseUrl: e.target.value }))}
                  placeholder="http://localhost/v1"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="timeoutSeconds">超时时间（秒）</Label>
                <Input
                  id="timeoutSeconds"
                  type="number"
                  value={newConfig.timeoutSeconds}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, timeoutSeconds: parseInt(e.target.value) || 30 }))}
                  min="1"
                  max="300"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxRetries">最大重试次数</Label>
                <Input
                  id="maxRetries"
                  type="number"
                  value={newConfig.maxRetries}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, maxRetries: parseInt(e.target.value) || 3 }))}
                  min="1"
                  max="10"
                />
              </div>
              <div className="col-span-2 space-y-2">
                <Label htmlFor="description">描述</Label>
                <Textarea
                  id="description"
                  value={newConfig.description}
                  onChange={(e) => setNewConfig(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="配置描述"
                  rows={3}
                />
              </div>
              <div className="col-span-2 flex items-center space-x-2">
                <Switch
                  id="enabled"
                  checked={newConfig.enabled}
                  onCheckedChange={(checked) => setNewConfig(prev => ({ ...prev, enabled: checked }))}
                />
                <Label htmlFor="enabled">启用配置</Label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                取消
              </Button>
              <Button onClick={handleCreateConfig}>
                创建
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* 搜索和过滤 */}
      <div className="flex gap-4">
        <div className="flex-1">
          <Input
            placeholder="搜索配置..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Select value={environmentFilter} onValueChange={setEnvironmentFilter}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">所有环境</SelectItem>
            <SelectItem value="dev">开发环境</SelectItem>
            <SelectItem value="test">测试环境</SelectItem>
            <SelectItem value="prod">生产环境</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* 配置列表 */}
      <div className="grid gap-4">
        {filteredConfigs.map((config) => (
          <Card key={config.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {config.appName}
                    <Badge className={getEnvironmentColor(config.environment)}>
                      {config.environment}
                    </Badge>
                    {config.enabled ? (
                      <Badge className="bg-green-100 text-green-800">启用</Badge>
                    ) : (
                      <Badge className="bg-gray-100 text-gray-800">禁用</Badge>
                    )}
                  </CardTitle>
                  <CardDescription>
                    ID: {config.appId} | URL: {config.baseUrl}
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onTestConnection(config)}
                  >
                    测试连接
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openEditDialog(config)}
                  >
                    编辑
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleToggleEnabled(config)}
                  >
                    {config.enabled ? '禁用' : '启用'}
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDeleteConfig(config)}
                    disabled={config.enabled}
                  >
                    删除
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">超时时间:</span> {config.timeoutSeconds}秒
                </div>
                <div>
                  <span className="font-medium">最大重试:</span> {config.maxRetries}次
                </div>
                {config.description && (
                  <div className="col-span-2">
                    <span className="font-medium">描述:</span> {config.description}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 编辑对话框 */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>编辑Agent配置</DialogTitle>
            <DialogDescription>
              修改Agent应用配置信息
            </DialogDescription>
          </DialogHeader>
          {editingConfig && (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-environment">环境</Label>
                <Select value={editingConfig.environment} onValueChange={(value) => setEditingConfig(prev => prev ? { ...prev, environment: value } : null)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dev">开发环境</SelectItem>
                    <SelectItem value="test">测试环境</SelectItem>
                    <SelectItem value="prod">生产环境</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-appId">应用ID</Label>
                <Input
                  id="edit-appId"
                  value={editingConfig.appId}
                  onChange={(e) => setEditingConfig(prev => prev ? { ...prev, appId: e.target.value } : null)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-appName">应用名称</Label>
                <Input
                  id="edit-appName"
                  value={editingConfig.appName}
                  onChange={(e) => setEditingConfig(prev => prev ? { ...prev, appName: e.target.value } : null)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-baseUrl">基础URL</Label>
                <Input
                  id="edit-baseUrl"
                  value={editingConfig.baseUrl}
                  onChange={(e) => setEditingConfig(prev => prev ? { ...prev, baseUrl: e.target.value } : null)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-timeoutSeconds">超时时间（秒）</Label>
                <Input
                  id="edit-timeoutSeconds"
                  type="number"
                  value={editingConfig.timeoutSeconds}
                  onChange={(e) => setEditingConfig(prev => prev ? { ...prev, timeoutSeconds: parseInt(e.target.value) || 30 } : null)}
                  min="1"
                  max="300"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-maxRetries">最大重试次数</Label>
                <Input
                  id="edit-maxRetries"
                  type="number"
                  value={editingConfig.maxRetries}
                  onChange={(e) => setEditingConfig(prev => prev ? { ...prev, maxRetries: parseInt(e.target.value) || 3 } : null)}
                  min="1"
                  max="10"
                />
              </div>
              <div className="col-span-2 space-y-2">
                <Label htmlFor="edit-description">描述</Label>
                <Textarea
                  id="edit-description"
                  value={editingConfig.description || ''}
                  onChange={(e) => setEditingConfig(prev => prev ? { ...prev, description: e.target.value } : null)}
                  rows={3}
                />
              </div>
              <div className="col-span-2 flex items-center space-x-2">
                <Switch
                  id="edit-enabled"
                  checked={editingConfig.enabled}
                  onCheckedChange={(checked) => setEditingConfig(prev => prev ? { ...prev, enabled: checked } : null)}
                />
                <Label htmlFor="edit-enabled">启用配置</Label>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleUpdateConfig}>
              更新
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
} 