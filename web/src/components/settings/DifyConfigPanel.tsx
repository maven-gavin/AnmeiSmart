'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import type { DifyConfig } from '@/service/difyConfigService';

interface DifyConfigPanelProps {
  configs: DifyConfig[];
  onCreateConfig: (config: Omit<DifyConfig, 'id' | 'createdAt' | 'updatedAt'> & { apiKey: string }) => Promise<void>;
  onUpdateConfig: (id: string, config: Partial<DifyConfig> & { apiKey?: string }) => Promise<void>;
  onDeleteConfig: (id: string) => Promise<void>;
  onTestConnection: (config: DifyConfig) => Promise<void>;
  isTestingConnection: boolean;
}

export default function DifyConfigPanel({
  configs,
  onCreateConfig,
  onUpdateConfig,
  onDeleteConfig,
  onTestConnection,
  isTestingConnection
}: DifyConfigPanelProps) {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingConfig, setEditingConfig] = useState<DifyConfig | null>(null);
  const [newConfig, setNewConfig] = useState<Omit<DifyConfig, 'id' | 'createdAt' | 'updatedAt'> & { apiKey: string }>({
    environment: '',
    appId: '',
    appName: '',
    apiKey: '',
    baseUrl: 'http://localhost/v1',
    timeoutSeconds: 30,
    maxRetries: 3,
    enabled: true,
    description: ''
  });

  const handleCreateConfig = async () => {
    if (!newConfig.environment || !newConfig.appId || !newConfig.appName || !newConfig.apiKey) {
      alert('请填写所有必填字段');
      return;
    }
    
    await onCreateConfig(newConfig);
    setShowCreateDialog(false);
    resetForm();
  };

  const handleUpdateConfig = async () => {
    if (!editingConfig) return;
    
    await onUpdateConfig(editingConfig.id, {
      environment: newConfig.environment,
      appId: newConfig.appId,
      appName: newConfig.appName,
      apiKey: newConfig.apiKey,
      baseUrl: newConfig.baseUrl,
      timeoutSeconds: newConfig.timeoutSeconds,
      maxRetries: newConfig.maxRetries,
      enabled: newConfig.enabled,
      description: newConfig.description
    });
    
    setEditingConfig(null);
    setShowCreateDialog(false);
    resetForm();
  };

  const handleToggleEnabled = async (config: DifyConfig) => {
    await onUpdateConfig(config.id, { enabled: !config.enabled });
  };

  const openCreateDialog = () => {
    resetForm();
    setEditingConfig(null);
    setShowCreateDialog(true);
  };

  const openEditDialog = (config: DifyConfig) => {
    setNewConfig({
      environment: config.environment,
      appId: config.appId,
      appName: config.appName,
      apiKey: '', // 安全考虑，不显示现有密钥
      baseUrl: config.baseUrl,
      timeoutSeconds: config.timeoutSeconds,
      maxRetries: config.maxRetries,
      enabled: config.enabled,
      description: config.description || ''
    });
    setEditingConfig(config);
    setShowCreateDialog(true);
  };

  const resetForm = () => {
    setNewConfig({
      environment: '',
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

  const handleDeleteConfig = async (config: DifyConfig) => {
    if (confirm('确定要删除这个Dify配置吗？')) {
      await onDeleteConfig(config.id);
    }
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
      {/* 标题和添加按钮 */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">机器人配置管理</h2>
        <Button
          onClick={openCreateDialog}
          className="bg-orange-500 hover:bg-orange-600"
        >
          添加配置
        </Button>
      </div>

      {/* 配置列表表格 */}
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead className="bg-gray-50">
            <tr>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">序号</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">环境名称</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">机器人ID</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">机器人名称</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">API密钥</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">基础URL</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">超时时间（秒）</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">最大重试次数</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">启用配置</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white">
            {configs.length === 0 ? (
              <tr>
                <td colSpan={10} className="border border-gray-200 px-4 py-8 text-center text-gray-500">
                  暂无机器人配置，点击上方"添加配置"按钮开始配置
                </td>
              </tr>
            ) : (
              configs.map((config, index) => (
                <tr key={config.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="border border-gray-200 px-4 py-3 text-sm">{index + 1}</td>
                  <td className="border border-gray-200 px-4 py-3 text-sm">{config.environment}</td>
                  <td className="border border-gray-200 px-4 py-3 text-sm font-mono text-xs">{config.appId}</td>
                  <td className="border border-gray-200 px-4 py-3 text-sm">{config.appName}</td>
                  <td className="border border-gray-200 px-4 py-3 text-sm">XXXXX</td>
                  <td className="border border-gray-200 px-4 py-3 text-sm">{config.baseUrl}</td>
                  <td className="border border-gray-200 px-4 py-3 text-sm text-center">{config.timeoutSeconds}</td>
                  <td className="border border-gray-200 px-4 py-3 text-sm text-center">{config.maxRetries}</td>
                  <td className="border border-gray-200 px-4 py-3 text-sm">
                    <Switch
                      checked={config.enabled}
                      onCheckedChange={() => handleToggleEnabled(config)}
                      className="data-[state=checked]:bg-orange-500"
                    />
                  </td>
                  <td className="border border-gray-200 px-4 py-3 text-sm">
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openEditDialog(config)}
                        className="text-xs"
                      >
                        编辑
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onTestConnection(config)}
                        disabled={isTestingConnection}
                        className="text-xs"
                      >
                        测试
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleDeleteConfig(config)}
                        className="text-xs"
                      >
                        删除
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 功能说明 */}
      <div className="mt-6 rounded-lg bg-yellow-50 p-4">
        <div className="flex">
          <div className="text-yellow-400">⚠️</div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">交互功能说明：</h3>
            <div className="mt-2 text-sm text-yellow-700">
              <ul className="list-disc pl-5 space-y-1">
                <li>用户点击"添加配置"按钮，系统弹出"新增"对话框并额外增加"客注"项，保存后列表显示新增内容的行</li>
                <li>用户点击"编辑"按钮，就弹出"编辑"对话框并显示该行的配置，并额外增加"客注"项，用户可以编辑相关信息</li>
                <li>用户点击"测试"按钮，就执行该配置的测试</li>
                <li>用户点击"删除"按钮，如果未启用配置，就可删除选中的行，如果启用记录被选择，就提示"启用配置不可删除，请先禁用配置。"</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* 创建/编辑配置弹窗 */}
      {showCreateDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 shadow-lg">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">
                {editingConfig ? '编辑机器人配置' : '新增机器人配置'}
              </h3>
              <button
                onClick={() => setShowCreateDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <Label className="block text-sm font-medium text-gray-700">环境名称 *</Label>
                  <Input
                    type="text"
                    value={newConfig.environment}
                    onChange={(e) => setNewConfig({...newConfig, environment: e.target.value})}
                    placeholder="例如: dev"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label className="block text-sm font-medium text-gray-700">机器人ID *</Label>
                  <Input
                    type="text"
                    value={newConfig.appId}
                    onChange={(e) => setNewConfig({...newConfig, appId: e.target.value})}
                    placeholder="例如: dify-chat-app"
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <Label className="block text-sm font-medium text-gray-700">机器人名称 *</Label>
                  <Input
                    type="text"
                    value={newConfig.appName}
                    onChange={(e) => setNewConfig({...newConfig, appName: e.target.value})}
                    placeholder="例如: 通用聊天"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label className="block text-sm font-medium text-gray-700">API密钥 *</Label>
                  <Input
                    type="password"
                    value={newConfig.apiKey}
                    onChange={(e) => setNewConfig({...newConfig, apiKey: e.target.value})}
                    placeholder="API密钥"
                    className="mt-1"
                  />
                </div>
              </div>

              <div>
                <Label className="block text-sm font-medium text-gray-700">基础URL *</Label>
                <Input
                  type="text"
                  value={newConfig.baseUrl}
                  onChange={(e) => setNewConfig({...newConfig, baseUrl: e.target.value})}
                  placeholder="例如: http://localhost/v1"
                  className="mt-1"
                />
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div>
                  <Label className="block text-sm font-medium text-gray-700">超时时间（秒）</Label>
                  <Input
                    type="number"
                    value={newConfig.timeoutSeconds}
                    onChange={(e) => setNewConfig({...newConfig, timeoutSeconds: parseInt(e.target.value) || 30})}
                    min="1"
                    max="300"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label className="block text-sm font-medium text-gray-700">最大重试次数</Label>
                  <Input
                    type="number"
                    value={newConfig.maxRetries}
                    onChange={(e) => setNewConfig({...newConfig, maxRetries: parseInt(e.target.value) || 3})}
                    min="1"
                    max="10"
                    className="mt-1"
                  />
                </div>
                <div className="flex items-center justify-center">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={newConfig.enabled}
                      onChange={(e) => setNewConfig({...newConfig, enabled: e.target.checked})}
                      className="h-4 w-4 rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">启用配置</span>
                  </label>
                </div>
              </div>

              <div>
                <Label className="block text-sm font-medium text-gray-700">客注</Label>
                <textarea
                  value={newConfig.description}
                  onChange={(e) => setNewConfig({...newConfig, description: e.target.value})}
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                  rows={3}
                  placeholder="配置描述信息"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
              >
                取消
              </Button>
              <Button
                onClick={editingConfig ? handleUpdateConfig : handleCreateConfig}
                className="bg-orange-500 hover:bg-orange-600"
              >
                {editingConfig ? '更新配置' : '创建配置'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 