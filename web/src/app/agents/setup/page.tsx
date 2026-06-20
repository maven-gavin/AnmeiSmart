'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import AppLayout from '@/components/layout/AppLayout';
import { useAgentConfigs } from '@/hooks/useAgentConfigs';
import { AgentConfig, AgentConfigCreate, AgentConfigUpdate } from '@/service/agentConfigService';
import { SMARTBRAIN_API_BASE_URL, SMARTBRAIN_DEFAULT_TIMEOUT, SMARTBRAIN_DEFAULT_MAX_RETRIES } from '@/config';
import { EnhancedPagination } from '@/components/ui/pagination';
import { AgentConfigForm } from '@/components/agents/AgentConfigForm';
import {
  capabilitiesFromRecord,
  capabilitiesToRecord,
  DEFAULT_CAPABILITIES,
  getProviderPreset,
  type AgentCapabilitiesForm,
  type LlmProviderId,
} from '@/lib/llmProviderPresets';

export default function AgentsPage() {
  const { user } = useAuthContext();
  const router = useRouter();
  const {
    configs: agentConfigs,
    isLoading,
    createConfig,
    updateConfig,
    deleteConfig,
    testConnection
  } = useAgentConfigs();

  const [configs, setConfigs] = useState<AgentConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  
  // 编辑状态
  const [editingConfig, setEditingConfig] = useState<AgentConfig | null>(null);
  const [showEditDialog, setShowEditDialog] = useState(false);
  
  // 删除确认状态
  const [deletingConfig, setDeletingConfig] = useState<AgentConfig | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  
  // 查看详情状态
  const [viewingConfig, setViewingConfig] = useState<AgentConfig | null>(null);
  const [showViewDialog, setShowViewDialog] = useState(false);
  
  // 表单字段
  const [environment, setEnvironment] = useState('dev');
  const [appId, setAppId] = useState('');
  const [appName, setAppName] = useState('');
  const [agentType, setAgentType] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState(SMARTBRAIN_API_BASE_URL);
  const [description, setDescription] = useState('');
  const [timeoutSeconds, setTimeoutSeconds] = useState(SMARTBRAIN_DEFAULT_TIMEOUT);
  const [maxRetries, setMaxRetries] = useState(SMARTBRAIN_DEFAULT_MAX_RETRIES);
  const [enabled, setEnabled] = useState(true);
  const [llmProvider, setLlmProvider] = useState<LlmProviderId>('openai');
  const [capabilities, setCapabilities] = useState<AgentCapabilitiesForm>({ ...DEFAULT_CAPABILITIES });

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);
  
  // 搜索筛选状态
  const [searchEnvironment, setSearchEnvironment] = useState('all');
  const [searchAppName, setSearchAppName] = useState('');
  const [searchStatus, setSearchStatus] = useState('all');
  const [allConfigs, setAllConfigs] = useState<AgentConfig[]>([]);

  // 检查用户是否有管理员权限
  useEffect(() => {
    if (user && !user.roles.includes('admin')) {
      router.push('/unauthorized');
    }
  }, [user, router]);

  // 同步数据
  useEffect(() => {
    setConfigs(agentConfigs);
    setAllConfigs(agentConfigs);
    setLoading(isLoading);
  }, [agentConfigs, isLoading]);

  // 筛选配置
  const filterConfigs = () => {
    setCurrentPage(1);
    let filteredConfigs = [...allConfigs];
    
    if (searchEnvironment && searchEnvironment !== 'all') {
      filteredConfigs = filteredConfigs.filter(config => 
        config.environment.toLowerCase().includes(searchEnvironment.toLowerCase())
      );
    }
    
    if (searchAppName) {
      filteredConfigs = filteredConfigs.filter(config => 
        config.appName.toLowerCase().includes(searchAppName.toLowerCase())
      );
    }
    
    if (searchStatus && searchStatus !== 'all') {
      const isEnabled = searchStatus === 'enabled';
      filteredConfigs = filteredConfigs.filter(config => 
        config.enabled === isEnabled
      );
    }
    
    setConfigs(filteredConfigs);
  };

  // 重置筛选条件
  const resetFilters = () => {
    setSearchEnvironment('all');
    setSearchAppName('');
    setSearchStatus('all');
    setConfigs(allConfigs);
    setCurrentPage(1);
  };

  const detectProviderFromBaseUrl = (url: string): LlmProviderId => {
    const normalized = url.trim().toLowerCase();
    if (normalized.includes('deepseek')) return 'deepseek';
    if (normalized.includes('openai')) return 'openai';
    return 'custom';
  };

  const applyProviderPreset = (providerId: LlmProviderId) => {
    setLlmProvider(providerId);
    const preset = getProviderPreset(providerId);
    if (providerId !== 'custom' && preset.baseUrl) {
      setBaseUrl(preset.baseUrl);
    }
    if (providerId !== 'custom' && preset.defaultModel) {
      setCapabilities((prev) => ({ ...prev, model: preset.defaultModel }));
    }
  };

  // 重置表单
  const resetForm = () => {
    setEnvironment('dev');
    setAppId('');
    setAppName('');
    setAgentType('');
    setApiKey('');
    setBaseUrl(SMARTBRAIN_API_BASE_URL);
    setDescription('');
    setTimeoutSeconds(SMARTBRAIN_DEFAULT_TIMEOUT);
    setMaxRetries(SMARTBRAIN_DEFAULT_MAX_RETRIES);
    setEnabled(true);
    setLlmProvider('openai');
    setCapabilities({ ...DEFAULT_CAPABILITIES });
    setFormError(null);
  };

  // 打开创建对话框
  const handleCreateClick = () => {
    resetForm();
    setShowCreateDialog(true);
  };

  // 创建配置
  const handleCreateConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!appId.trim() || !appName.trim() || !apiKey.trim()) {
      setFormError('应用ID、应用名称和API密钥不能为空');
      return;
    }
    
    setFormLoading(true);
    setFormError(null);
    
    try {
      const configData: AgentConfigCreate = {
        environment,
        appId: appId.trim(),
        appName: appName.trim(),
        agentType: agentType.trim() || undefined,
        apiKey: apiKey.trim(),
        baseUrl,
        description: description.trim() || undefined,
        timeoutSeconds,
        maxRetries,
        enabled,
        capabilities: capabilitiesToRecord(capabilities),
      };

      await createConfig(configData);
      
      // 重置表单
      resetForm();
      setShowCreateDialog(false);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : '创建配置失败');
      console.error('创建配置错误', err);
    } finally {
      setFormLoading(false);
    }
  };

  // 打开编辑对话框
  const handleEditClick = (config: AgentConfig) => {
    setEditingConfig(config);
    setEnvironment(config.environment);
    setAppId(config.appId);
    setAppName(config.appName);
    setAgentType(config.agentType || '');
    setApiKey(''); // 不显示现有API密钥
    setBaseUrl(config.baseUrl);
    setDescription(config.description || '');
    setTimeoutSeconds(config.timeoutSeconds);
    setMaxRetries(config.maxRetries);
    setEnabled(config.enabled);
    const caps = capabilitiesFromRecord(config.capabilities);
    setCapabilities(caps);
    setLlmProvider(detectProviderFromBaseUrl(config.baseUrl));
    setShowEditDialog(true);
  };

  // 编辑配置
  const handleEditConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!editingConfig) return;
    
    if (!appId.trim() || !appName.trim()) {
      setFormError('应用ID和应用名称不能为空');
      return;
    }
    
    setFormLoading(true);
    setFormError(null);
    
    try {
      const updateData: AgentConfigUpdate = {
        environment,
        appId: appId.trim(),
        appName: appName.trim(),
        agentType: agentType.trim() || undefined,
        baseUrl,
        description: description.trim() || undefined,
        timeoutSeconds,
        maxRetries,
        enabled,
        capabilities: capabilitiesToRecord(capabilities, editingConfig.capabilities),
      };
      if (apiKey.trim()) {
        updateData.apiKey = apiKey.trim();
      }

      await updateConfig(editingConfig.id, updateData);
      
      // 重置表单和状态
      resetForm();
      setEditingConfig(null);
      setShowEditDialog(false);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : '更新配置失败');
      console.error('更新配置错误', err);
    } finally {
      setFormLoading(false);
    }
  };

  // 打开查看详情对话框
  const handleViewClick = (config: AgentConfig) => {
    setViewingConfig(config);
    setShowViewDialog(true);
  };

  // 打开删除确认对话框
  const handleDeleteClick = (config: AgentConfig) => {
    if (config.enabled) {
      setFormError('启用的配置不能删除，请先禁用配置');
      return;
    }
    setDeletingConfig(config);
    setShowDeleteDialog(true);
  };

  // 确认删除
  const handleConfirmDelete = async () => {
    if (!deletingConfig) return;
    
    try {
      await deleteConfig(deletingConfig.id);
      setShowDeleteDialog(false);
      setDeletingConfig(null);
    } catch (err) {
      console.error('删除配置错误', err);
    }
  };

  // 切换启用/禁用状态
  const handleToggleEnabled = async (config: AgentConfig) => {
    try {
      await updateConfig(config.id, {
        enabled: !config.enabled
      });
    } catch (err) {
      console.error('切换状态错误', err);
    }
  };

  if (loading && configs.length === 0) {
    return (
      <AppLayout requiredRole={user?.currentRole}>
        <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
        </div>
      </AppLayout>
    );
  }

  // 状态样式映射
  const getStatusStyle = (enabled: boolean) => {
    return enabled 
      ? 'bg-green-100 text-green-800' 
      : 'bg-gray-100 text-gray-800';
  };

  // 环境样式映射
  const getEnvironmentStyle = (env: string) => {
    const styles: Record<string, string> = {
      dev: 'bg-blue-100 text-blue-800',
      test: 'bg-yellow-100 text-yellow-800',
      prod: 'bg-red-100 text-red-800'
    };
    return styles[env] || 'bg-gray-100 text-gray-800';
  };
  
  // 分页逻辑
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentConfigs = configs.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(configs.length / itemsPerPage);

  const formValues = {
    environment,
    appId,
    appName,
    agentType,
    apiKey,
    baseUrl,
    description,
    timeoutSeconds,
    maxRetries,
    enabled,
    llmProvider,
    capabilities,
  };

  const agentConfigDialogClass =
    'flex max-h-[90vh] w-full max-w-4xl flex-col gap-0 overflow-hidden p-0 sm:max-w-4xl';

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Agent配置管理</h1>
          </div>
          <Button 
            onClick={handleCreateClick}
            className="bg-orange-500 hover:bg-orange-600"
          >
            添加配置
          </Button>
        </div>

        {/* 组合查询区域 */}
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
          <h2 className="mb-4 text-lg font-medium text-gray-800">组合查询</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <Label htmlFor="searchEnvironment" className="mb-2 block text-sm font-medium">环境</Label>
              <Select value={searchEnvironment} onValueChange={setSearchEnvironment}>
                <SelectTrigger id="searchEnvironment" className="w-full">
                  <SelectValue placeholder="所有环境" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有环境</SelectItem>
                  <SelectItem value="dev">开发环境</SelectItem>
                  <SelectItem value="test">测试环境</SelectItem>
                  <SelectItem value="prod">生产环境</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="searchAppName" className="mb-2 block text-sm font-medium">应用名称</Label>
              <Input
                id="searchAppName"
                value={searchAppName}
                onChange={(e) => setSearchAppName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    filterConfigs();
                  }
                }}
                placeholder="搜索应用名称"
                className="w-full"
              />
            </div>
            <div>
              <Label htmlFor="searchStatus" className="mb-2 block text-sm font-medium">状态</Label>
              <Select value={searchStatus} onValueChange={setSearchStatus}>
                <SelectTrigger id="searchStatus" className="w-full">
                  <SelectValue placeholder="所有状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有状态</SelectItem>
                  <SelectItem value="enabled">启用</SelectItem>
                  <SelectItem value="disabled">禁用</SelectItem>
                </SelectContent>
              </Select>
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




        <div className="overflow-x-auto rounded-lg border border-gray-200 shadow">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  环境
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  应用名称
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  应用ID
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  应用类型
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  模型
                </th>
                <th scope="col" className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                  状态
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {currentConfigs.map((config) => (
                <tr key={config.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                    <span className={`rounded-full ${getEnvironmentStyle(config.environment)} px-3 py-1 text-sm font-medium`}>
                      {config.environment}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                    {config.appName}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {config.appId}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {config.agentType || '-'}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 am-mono">
                    {(config.capabilities?.model as string) || 'gpt-4o-mini'}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="flex items-center justify-center space-x-2">
                      <Switch
                        checked={config.enabled}
                        onCheckedChange={() => handleToggleEnabled(config)}
                      />
                      <span className={`text-sm font-medium ${config.enabled ? 'text-green-600' : 'text-gray-500'}`}>
                        {config.enabled ? '启用' : '禁用'}
                      </span>
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium">
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleViewClick(config)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        查看
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => testConnection(config)}
                        className="text-green-600 hover:text-green-800"
                      >
                        测试
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleEditClick(config)}
                        className="text-gray-600 hover:text-gray-800"
                      >
                        编辑
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDeleteClick(config)}
                        className="text-red-600 hover:text-red-800"
                        disabled={config.enabled}
                      >
                        删除
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              
              {configs.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-sm text-gray-500">
                    暂无配置数据
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* 分页组件 */}
        {configs.length > 0 && (
          <div className="mt-6">
            <EnhancedPagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={configs.length}
              itemsPerPage={itemsPerPage}
              itemsPerPageOptions={[5, 10, 20, 50, 100]}
              onPageChange={(page) => {
                setCurrentPage(page);
              }}
              onItemsPerPageChange={(newItemsPerPage) => {
                setItemsPerPage(newItemsPerPage);
                setCurrentPage(1);
              }}
              showPageInput={true}
            />
          </div>
        )}

        {/* 创建对话框 */}
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogContent className={agentConfigDialogClass}>
            <DialogHeader className="shrink-0 border-b border-gray-200 px-6 py-5">
              <DialogTitle>创建 Agent 配置</DialogTitle>
              <DialogDescription>
                填写基本信息与 LLM 连接参数，创建新的 Agent
              </DialogDescription>
            </DialogHeader>

            <div className="flex min-h-0 flex-1 flex-col px-6 pb-6 pt-4">
              <AgentConfigForm
                mode="create"
                idPrefix="create"
                formLoading={formLoading}
                formError={formError}
                values={formValues}
                onEnvironmentChange={setEnvironment}
                onAppIdChange={setAppId}
                onAppNameChange={setAppName}
                onAgentTypeChange={setAgentType}
                onApiKeyChange={setApiKey}
                onBaseUrlChange={setBaseUrl}
                onDescriptionChange={setDescription}
                onTimeoutSecondsChange={setTimeoutSeconds}
                onMaxRetriesChange={setMaxRetries}
                onEnabledChange={setEnabled}
                onProviderChange={applyProviderPreset}
                onCapabilitiesChange={setCapabilities}
                onSubmit={handleCreateConfig}
                onCancel={() => {
                  setShowCreateDialog(false);
                  resetForm();
                }}
              />
            </div>
          </DialogContent>
        </Dialog>

        {/* 编辑对话框 */}
        <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
          <DialogContent className={agentConfigDialogClass}>
            <DialogHeader className="shrink-0 border-b border-gray-200 px-6 py-5">
              <DialogTitle>编辑 Agent 配置</DialogTitle>
              <DialogDescription>
                {editingConfig ? `正在编辑「${editingConfig.appName}」` : '修改 Agent 配置的参数和设置'}
              </DialogDescription>
            </DialogHeader>

            <div className="flex min-h-0 flex-1 flex-col px-6 pb-6 pt-4">
              <AgentConfigForm
                mode="edit"
                idPrefix="edit"
                formLoading={formLoading}
                formError={formError}
                values={formValues}
                onEnvironmentChange={setEnvironment}
                onAppIdChange={setAppId}
                onAppNameChange={setAppName}
                onAgentTypeChange={setAgentType}
                onApiKeyChange={setApiKey}
                onBaseUrlChange={setBaseUrl}
                onDescriptionChange={setDescription}
                onTimeoutSecondsChange={setTimeoutSeconds}
                onMaxRetriesChange={setMaxRetries}
                onEnabledChange={setEnabled}
                onProviderChange={applyProviderPreset}
                onCapabilitiesChange={setCapabilities}
                onSubmit={handleEditConfig}
                onCancel={() => {
                  setShowEditDialog(false);
                  setEditingConfig(null);
                  resetForm();
                }}
              />
            </div>
          </DialogContent>
        </Dialog>

        {/* 查看详情对话框 */}
        <Dialog open={showViewDialog} onOpenChange={setShowViewDialog}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>配置详情</DialogTitle>
              <DialogDescription>
                查看Agent配置的详细信息
              </DialogDescription>
            </DialogHeader>
            
            {viewingConfig && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-700">环境</Label>
                    <div className="mt-1 text-sm text-gray-900">
                      <span className={`rounded-full ${viewingConfig.environment === 'dev' ? 'bg-blue-100 text-blue-800' : viewingConfig.environment === 'test' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'} px-3 py-1 text-sm font-medium`}>
                        {viewingConfig.environment === 'dev' ? '开发环境' : viewingConfig.environment === 'test' ? '测试环境' : '生产环境'}
                      </span>
                    </div>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium text-gray-700">状态</Label>
                    <div className="mt-1 text-sm text-gray-900">
                      <span className={`rounded-full ${viewingConfig.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'} px-3 py-1 text-sm font-medium`}>
                        {viewingConfig.enabled ? '启用' : '禁用'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-700">应用ID</Label>
                    <div className="mt-1 text-sm text-gray-900">{viewingConfig.appId}</div>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium text-gray-700">应用名称</Label>
                    <div className="mt-1 text-sm text-gray-900">{viewingConfig.appName}</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-700">应用类型</Label>
                    <div className="mt-1 text-sm text-gray-900">
                      {viewingConfig.agentType === 'chat' ? '对话型' : viewingConfig.agentType === 'agent' ? '智能体' : viewingConfig.agentType === 'workflow' ? '工作流' : '-'}
                    </div>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium text-gray-700">基础URL</Label>
                    <div className="mt-1 text-sm text-gray-900">{viewingConfig.baseUrl}</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-700">模型</Label>
                    <div className="mt-1 text-sm text-gray-900 am-mono">
                      {(viewingConfig.capabilities?.model as string) || 'gpt-4o-mini'}
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-700">RAG</Label>
                    <div className="mt-1 text-sm text-gray-900">
                      {viewingConfig.capabilities?.enable_rag ? '已启用' : '未启用'}
                    </div>
                  </div>
                </div>

                {(viewingConfig.capabilities?.system_prompt as string) && (
                  <div>
                    <Label className="text-sm font-medium text-gray-700">系统提示词</Label>
                    <div className="mt-1 whitespace-pre-wrap rounded border border-gray-200 bg-gray-50 p-3 text-sm text-gray-900">
                      {viewingConfig.capabilities?.system_prompt as string}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-700">超时时间</Label>
                    <div className="mt-1 text-sm text-gray-900">{viewingConfig.timeoutSeconds} 秒</div>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium text-gray-700">最大重试次数</Label>
                    <div className="mt-1 text-sm text-gray-900">{viewingConfig.maxRetries} 次</div>
                  </div>
                </div>

                {viewingConfig.description && (
                  <div>
                    <Label className="text-sm font-medium text-gray-700">描述</Label>
                    <div className="mt-1 text-sm text-gray-900">{viewingConfig.description}</div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-700">创建时间</Label>
                    <div className="mt-1 text-sm text-gray-900">
                      {new Date(viewingConfig.createdAt).toLocaleString('zh-CN')}
                    </div>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium text-gray-700">更新时间</Label>
                    <div className="mt-1 text-sm text-gray-900">
                      {new Date(viewingConfig.updatedAt).toLocaleString('zh-CN')}
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowViewDialog(false)}
              >
                关闭
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* 删除确认对话框 */}
        <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>确认删除</AlertDialogTitle>
              <AlertDialogDescription>
                您确定要删除 &quot;{deletingConfig?.appName}&quot; 配置吗？此操作无法撤销。
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => {
                setShowDeleteDialog(false);
                setDeletingConfig(null);
              }}>
                取消
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={handleConfirmDelete}
                className="bg-red-600 hover:bg-red-700"
              >
                确认删除
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </AppLayout>
  );
}
