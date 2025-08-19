'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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

  // 查询和分页状态
  const [searchEnvironment, setSearchEnvironment] = useState('');
  const [searchAppId, setSearchAppId] = useState('');
  const [searchAppName, setSearchAppName] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(5);
  const [filteredConfigs, setFilteredConfigs] = useState<DifyConfig[]>([]);
  const [allConfigs, setAllConfigs] = useState<DifyConfig[]>([]);

  // 更新数据状态
  useEffect(() => {
    setAllConfigs(configs);
    setFilteredConfigs(configs);
  }, [configs]);

  // 查询功能
  const filterConfigs = () => {
    setCurrentPage(1);
    let filtered = [...allConfigs];
    
    if (searchEnvironment) {
      filtered = filtered.filter(config => 
        config.environment.toLowerCase().includes(searchEnvironment.toLowerCase())
      );
    }
    
    if (searchAppId) {
      filtered = filtered.filter(config => 
        config.appId.toLowerCase().includes(searchAppId.toLowerCase())
      );
    }
    
    if (searchAppName) {
      filtered = filtered.filter(config => 
        config.appName.toLowerCase().includes(searchAppName.toLowerCase())
      );
    }
    
    setFilteredConfigs(filtered);
  };

  // 重置查询
  const resetFilters = () => {
    setSearchEnvironment('');
    setSearchAppId('');
    setSearchAppName('');
    setFilteredConfigs(allConfigs);
    setCurrentPage(1);
  };

  // 分页逻辑
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentConfigs = filteredConfigs.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredConfigs.length / itemsPerPage);

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
        <h2 className="text-xl font-semibold text-gray-800">智能体配置管理</h2>
        <Button
          onClick={openCreateDialog}
          className="bg-orange-500 hover:bg-orange-600"
        >
          添加配置
        </Button>
      </div>

      {/* 查询区域 */}
      {allConfigs.length > 0 && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-gray-50 p-4">
          <h3 className="mb-4 text-sm font-medium text-gray-800">组合查询</h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <Label htmlFor="searchEnvironment" className="mb-2 block text-sm font-medium">环境名称</Label>
              <Input
                id="searchEnvironment"
                value={searchEnvironment}
                onChange={(e) => setSearchEnvironment(e.target.value)}
                placeholder="搜索环境名称"
                className="w-full"
              />
            </div>
            <div>
              <Label htmlFor="searchAppId" className="mb-2 block text-sm font-medium">智能体ID</Label>
              <Input
                id="searchAppId"
                value={searchAppId}
                onChange={(e) => setSearchAppId(e.target.value)}
                placeholder="搜索智能体ID"
                className="w-full"
              />
            </div>
            <div>
              <Label htmlFor="searchAppName" className="mb-2 block text-sm font-medium">智能体名称</Label>
              <Input
                id="searchAppName"
                value={searchAppName}
                onChange={(e) => setSearchAppName(e.target.value)}
                placeholder="搜索智能体名称"
                className="w-full"
              />
            </div>
          </div>
          <div className="mt-4 flex justify-end space-x-2">
            <Button variant="outline" onClick={resetFilters}>
              重置
            </Button>
            <Button className="bg-orange-500 hover:bg-orange-600" onClick={filterConfigs}>
              查询
            </Button>
          </div>
        </div>
      )}

      {/* 配置列表表格 */}
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead className="bg-gray-50">
            <tr>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">序号</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">环境名称</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">智能体ID</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">智能体名称</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">API密钥</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">基础URL</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">超时时间（秒）</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">最大重试次数</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">启用配置</th>
              <th className="border border-gray-200 px-4 py-3 text-left text-sm font-medium text-gray-900">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white">
            {filteredConfigs.length === 0 && allConfigs.length === 0 ? (
              <tr>
                <td colSpan={10} className="border border-gray-200 px-4 py-8 text-center text-gray-500">
                  暂无智能体配置，点击上方"添加配置"按钮开始配置
                </td>
              </tr>
            ) : filteredConfigs.length === 0 ? (
              <tr>
                <td colSpan={10} className="border border-gray-200 px-4 py-8 text-center text-gray-500">
                  未找到匹配的智能体配置，请调整查询条件或重置查询
                </td>
              </tr>
            ) : (
              currentConfigs.map((config, index) => (
                <tr key={config.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="border border-gray-200 px-4 py-3 text-sm">{indexOfFirstItem + index + 1}</td>
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

      {/* 分页组件 */}
      {filteredConfigs.length > 0 && totalPages > 1 && (
        <div className="mt-6 flex justify-center">
          <div className="flex space-x-2">
            <Button
              onClick={() => setCurrentPage(currentPage - 1)}
              disabled={currentPage === 1}
              variant="outline"
              size="sm"
              className="px-3"
            >
              上一页
            </Button>
            
            {Array.from({ length: totalPages }, (_, i) => (
              <Button
                key={i}
                onClick={() => setCurrentPage(i + 1)}
                variant={currentPage === i + 1 ? "default" : "outline"}
                size="sm"
                className={`px-3 ${currentPage === i + 1 ? 'bg-orange-500 hover:bg-orange-600' : ''}`}
              >
                {i + 1}
              </Button>
            ))}
            
            <Button
              onClick={() => setCurrentPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              variant="outline"
              size="sm"
              className="px-3"
            >
              下一页
            </Button>
          </div>
        </div>
      )}

      {/* 功能说明 */}
      <div className="mt-6 rounded-lg bg-yellow-50 p-4">
        <div className="flex">
          <div className="text-yellow-400">⚠️</div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">交互功能说明：</h3>
            <div className="mt-2 text-sm text-yellow-700">
              <ul className="list-disc pl-5 space-y-1">
                <li>用户点击&quot;添加配置&quot;按钮，系统弹出&quot;新增&quot;对话框并额外增加&quot;客注&quot;项，保存后列表显示新增内容的行</li>
                <li>用户点击&quot;编辑&quot;按钮，就弹出&quot;编辑&quot;对话框并显示该行的配置，并额外增加&quot;客注&quot;项，用户可以编辑相关信息</li>
                <li>用户点击&quot;测试&quot;按钮，就执行该配置的测试</li>
                <li>用户点击&quot;删除&quot;按钮，如果未启用配置，就可删除选中的行，如果启用记录被选择，就提示&quot;启用配置不可删除，请先禁用配置。&quot;</li>
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
                {editingConfig ? '编辑智能体配置' : '新增智能体配置'}
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
                  <Label className="block text-sm font-medium text-gray-700">智能体ID *</Label>
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
                  <Label className="block text-sm font-medium text-gray-700">智能体名称 *</Label>
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