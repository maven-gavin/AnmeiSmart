'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import systemService, { SystemSettings, AIModelConfig } from '@/service/systemService';
import difyConfigService, { 
  DifyConfigInfo, 
  DifyConfigCreate, 
  DifyConfigUpdate,
  DifyTestConnectionRequest 
} from '@/service/difyConfigService';


export default function SystemSettingsPage() {
  const [activeTab, setActiveTab] = useState('general');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  // 系统设置状态
  const [settings, setSettings] = useState<SystemSettings>({
    siteName: '',
    logoUrl: '',
    aiModels: [],
    defaultModelId: '',
    maintenanceMode: false,
    userRegistrationEnabled: true
  });

  // 新AI模型状态
  const [newModel, setNewModel] = useState<AIModelConfig>({
    modelName: '',
    apiKey: '',
    baseUrl: '',
    maxTokens: 2000,
    temperature: 0.7,
    enabled: true,
    provider: 'openai', // 默认提供商
    appId: '' // Dify应用ID
  });

  // Dify配置状态
  const [difyConfigs, setDifyConfigs] = useState<DifyConfigInfo[]>([]);
  const [selectedDifyConfig, setSelectedDifyConfig] = useState<DifyConfigInfo | null>(null);
  const [showDifyConfigDialog, setShowDifyConfigDialog] = useState(false);
  const [isEditingDifyConfig, setIsEditingDifyConfig] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  
  // 新Dify配置状态
  const [newDifyConfig, setNewDifyConfig] = useState<DifyConfigCreate>({
    configName: '',
    baseUrl: 'http://localhost/v1',
    description: '',
    chatAppId: '',
    chatApiKey: '',
    beautyAppId: '',
    beautyApiKey: '',
    summaryAppId: '',
    summaryApiKey: '',
    timeoutSeconds: 30,
    maxRetries: 3,
    enabled: true
  });

  const { register, handleSubmit, formState: { errors }, reset } = useForm<SystemSettings>();

  // 加载系统设置和Dify配置
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setIsLoading(true);
        const [settingsData, difyConfigsData] = await Promise.all([
          systemService.getSystemSettings(),
          difyConfigService.getDifyConfigs()
        ]);
        setSettings(settingsData);
        setDifyConfigs(difyConfigsData);
        reset(settingsData); // 重置表单为获取到的数据
        setIsLoading(false);
      } catch (error) {
        console.error('加载设置失败:', error);
        toast.error('加载设置失败');
        setIsLoading(false);
      }
    };

    fetchSettings();
  }, [reset]);

  // 表单提交处理
  const onSubmit = async (data: SystemSettings) => {
    setIsSubmitting(true);
    try {
      // 更新系统设置
      const updatedSettings = await systemService.updateSystemSettings(data);
      setSettings(updatedSettings);
      toast.success('设置已成功保存');
    } catch (error) {
      console.error('保存设置时出错:', error);
      toast.error('保存设置时出错');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 添加新AI模型
  const handleAddModel = async () => {
    // 基本验证
    if (!newModel.modelName || !newModel.apiKey || !newModel.baseUrl) {
      toast.error('请填写所有必填字段');
      return;
    }
    
    // 特定提供商验证
    if (newModel.provider === 'dify' && !newModel.appId) {
      toast.error('使用Dify时必须填写应用ID');
      return;
    }
    
    try {
      // 创建新AI模型
      await systemService.createAIModel(newModel);
      
      // 刷新系统设置
      const updatedSettings = await systemService.getSystemSettings();
      setSettings(updatedSettings);
      reset(updatedSettings);
      
      // 重置新模型表单
      setNewModel({
        modelName: '',
        apiKey: '',
        baseUrl: '',
        maxTokens: 2000,
        temperature: 0.7,
        enabled: true,
        provider: 'openai',
        appId: ''
      });
      
      toast.success('AI模型已添加');
    } catch (error) {
      console.error('添加AI模型失败:', error);
      toast.error('添加AI模型失败');
    }
  };

  // Dify配置处理函数
  const handleCreateDifyConfig = async () => {
    try {
      const createdConfig = await difyConfigService.createDifyConfig(newDifyConfig);
      setDifyConfigs([...difyConfigs, createdConfig]);
      setShowDifyConfigDialog(false);
      resetDifyConfigForm();
      toast.success('Dify配置创建成功');
    } catch (error) {
      console.error('创建Dify配置失败:', error);
      toast.error('创建Dify配置失败');
    }
  };

  const handleUpdateDifyConfig = async () => {
    if (!selectedDifyConfig) return;
    
    try {
      const updateData: DifyConfigUpdate = {
        configName: newDifyConfig.configName,
        baseUrl: newDifyConfig.baseUrl,
        description: newDifyConfig.description,
        chatAppId: newDifyConfig.chatAppId,
        chatApiKey: newDifyConfig.chatApiKey,
        beautyAppId: newDifyConfig.beautyAppId,
        beautyApiKey: newDifyConfig.beautyApiKey,
        summaryAppId: newDifyConfig.summaryAppId,
        summaryApiKey: newDifyConfig.summaryApiKey,
        timeoutSeconds: newDifyConfig.timeoutSeconds,
        maxRetries: newDifyConfig.maxRetries,
        enabled: newDifyConfig.enabled
      };
      
      const updatedConfig = await difyConfigService.updateDifyConfig(selectedDifyConfig.id, updateData);
      setDifyConfigs(difyConfigs.map(config => 
        config.id === selectedDifyConfig.id ? updatedConfig : config
      ));
      setShowDifyConfigDialog(false);
      resetDifyConfigForm();
      toast.success('Dify配置更新成功');
    } catch (error) {
      console.error('更新Dify配置失败:', error);
      toast.error('更新Dify配置失败');
    }
  };

  const handleDeleteDifyConfig = async (configId: string) => {
    if (!confirm('确定要删除这个Dify配置吗？')) return;
    
    try {
      await difyConfigService.deleteDifyConfig(configId);
      setDifyConfigs(difyConfigs.filter(config => config.id !== configId));
      toast.success('Dify配置删除成功');
    } catch (error) {
      console.error('删除Dify配置失败:', error);
      toast.error('删除Dify配置失败');
    }
  };

  const handleTestConnection = async (appType: 'chat' | 'agent' | 'workflow', apiKey: string) => {
    if (!apiKey || !newDifyConfig.baseUrl) {
      toast.error('请填写基础URL和API密钥');
      return;
    }
    
    try {
      setIsTestingConnection(true);
      const testData: DifyTestConnectionRequest = {
        baseUrl: newDifyConfig.baseUrl,
        apiKey,
        appType
      };
      
      const result = await difyConfigService.testDifyConnection(testData);
      if (result.success) {
        toast.success(`${appType}应用连接测试成功`);
      } else {
        toast.error(`${appType}应用连接测试失败: ${result.message}`);
      }
    } catch (error) {
      console.error('连接测试失败:', error);
      toast.error('连接测试失败');
    } finally {
      setIsTestingConnection(false);
    }
  };

  const openCreateDifyConfigDialog = () => {
    resetDifyConfigForm();
    setIsEditingDifyConfig(false);
    setSelectedDifyConfig(null);
    setShowDifyConfigDialog(true);
  };

  const openEditDifyConfigDialog = (config: DifyConfigInfo) => {
    setNewDifyConfig({
      configName: config.configName,
      baseUrl: config.baseUrl,
      description: config.description || '',
      chatAppId: config.chatAppId || '',
      chatApiKey: '', // 安全考虑，不显示现有密钥
      beautyAppId: config.beautyAppId || '',
      beautyApiKey: '', // 安全考虑，不显示现有密钥
      summaryAppId: config.summaryAppId || '',
      summaryApiKey: '', // 安全考虑，不显示现有密钥
      timeoutSeconds: config.timeoutSeconds,
      maxRetries: config.maxRetries,
      enabled: config.enabled
    });
    setIsEditingDifyConfig(true);
    setSelectedDifyConfig(config);
    setShowDifyConfigDialog(true);
  };

  const resetDifyConfigForm = () => {
    setNewDifyConfig({
      configName: '',
      baseUrl: 'http://localhost/v1',
      description: '',
      chatAppId: '',
      chatApiKey: '',
      beautyAppId: '',
      beautyApiKey: '',
      summaryAppId: '',
      summaryApiKey: '',
      timeoutSeconds: 30,
      maxRetries: 3,
      enabled: true
    });
  };

  // 移除AI模型
  const handleRemoveModel = async (modelName: string) => {
    try {
      // 删除AI模型
      await systemService.deleteAIModel(modelName);
      
      // 刷新系统设置
      const updatedSettings = await systemService.getSystemSettings();
      setSettings(updatedSettings);
      reset(updatedSettings);
      
      toast.success('AI模型已移除');
    } catch (error) {
      console.error('移除AI模型失败:', error);
      toast.error('移除AI模型失败');
    }
  };

  // 切换AI模型状态
  const handleToggleModelStatus = async (modelName: string) => {
    try {
      // 切换AI模型状态
      await systemService.toggleAIModelStatus(modelName);
      
      // 刷新系统设置
      const updatedSettings = await systemService.getSystemSettings();
      setSettings(updatedSettings);
      reset(updatedSettings);
    } catch (error) {
      console.error('切换AI模型状态失败:', error);
      toast.error('切换AI模型状态失败');
    }
  };

  // 显示加载状态
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-orange-500"></div>
          <p className="text-gray-600">加载系统设置...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-800">系统设置</h1>
      
      <div className="mb-6 flex border-b">
        <button
          className={`mr-4 py-2 px-4 font-medium ${activeTab === 'general' ? 'border-b-2 border-orange-500 text-orange-500' : 'text-gray-500'}`}
          onClick={() => setActiveTab('general')}
        >
          基本设置
        </button>
        <button
          className={`mr-4 py-2 px-4 font-medium ${activeTab === 'ai' ? 'border-b-2 border-orange-500 text-orange-500' : 'text-gray-500'}`}
          onClick={() => setActiveTab('ai')}
        >
          AI模型配置
        </button>
        <button
          className={`mr-4 py-2 px-4 font-medium ${activeTab === 'security' ? 'border-b-2 border-orange-500 text-orange-500' : 'text-gray-500'}`}
          onClick={() => setActiveTab('security')}
        >
          安全与访问控制
        </button>
        <button
          className={`mr-4 py-2 px-4 font-medium ${activeTab === 'dify' ? 'border-b-2 border-orange-500 text-orange-500' : 'text-gray-500'}`}
          onClick={() => setActiveTab('dify')}
        >
          Dify配置
        </button>

      </div>
      
      <form onSubmit={handleSubmit(onSubmit)} className="mb-8">
        {/* 基本设置 */}
        <div className={activeTab === 'general' ? 'block' : 'hidden'}>
          <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6 shadow">
            <h2 className="mb-4 text-xl font-semibold text-gray-800">基本系统设置</h2>
            
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                系统名称
              </label>
              <input
                type="text"
                {...register('siteName', { required: '系统名称不能为空' })}
                className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
              />
              {errors.siteName && (
                <p className="mt-1 text-sm text-red-600">{errors.siteName.message}</p>
              )}
            </div>
            
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Logo URL
              </label>
              <input
                type="text"
                {...register('logoUrl')}
                className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
              />
            </div>
            
            <div className="mb-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  {...register('maintenanceMode')}
                  className="h-4 w-4 rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                />
                <span className="ml-2 text-sm text-gray-700">启用维护模式</span>
              </label>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                className="mr-4 rounded-md border border-gray-300 bg-white px-4 py-2 text-gray-700 hover:bg-gray-50 focus:outline-none"
                onClick={() => reset(settings)} // 重置为当前状态
              >
                重置
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="rounded-md bg-orange-500 px-4 py-2 text-white hover:bg-orange-600 focus:outline-none disabled:opacity-70"
              >
                {isSubmitting ? '保存中...' : '保存设置'}
              </button>
            </div>
          </div>
        </div>
        
        {/* AI模型配置 */}
        <div className={activeTab === 'ai' ? 'block' : 'hidden'}>
          <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6 shadow">
            <h2 className="mb-4 text-xl font-semibold text-gray-800">AI模型配置</h2>
            
            <div className="mb-6 max-h-96 overflow-y-auto pr-2">
              <h3 className="mb-3 text-lg font-medium text-gray-700">已配置模型</h3>
              
              {settings.aiModels.length === 0 ? (
                <p className="text-gray-500">尚未配置任何AI模型</p>
              ) : (
                <div className="space-y-4">
                  {settings.aiModels.map((model, index) => (
                    <div key={index} className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <span className={`mr-2 h-3 w-3 rounded-full ${model.enabled ? 'bg-green-500' : 'bg-red-500'}`}></span>
                          <h4 className="font-medium">{model.modelName}</h4>
                          {model.provider && (
                            <span className="ml-2 rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-800">
                              {model.provider.toUpperCase()}
                            </span>
                          )}
                        </div>
                        <div className="flex space-x-2">
                          <button
                            type="button"
                            onClick={() => handleToggleModelStatus(model.modelName)}
                            className="rounded bg-blue-500 px-3 py-1 text-sm text-white hover:bg-blue-600"
                          >
                            {model.enabled ? '停用' : '启用'}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleRemoveModel(model.modelName)}
                            className="rounded bg-red-500 px-3 py-1 text-sm text-white hover:bg-red-600"
                          >
                            删除
                          </button>
                        </div>
                      </div>
                      
                      <div className="mt-3 grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm font-medium text-gray-500">API基础URL:</span>
                          <p className="text-sm">{model.baseUrl}</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-500">API密钥:</span>
                          <p className="text-sm">••••••••••••••••••••</p>
                        </div>
                        {model.provider === 'dify' && model.appId && (
                          <div>
                            <span className="text-sm font-medium text-gray-500">应用ID:</span>
                            <p className="text-sm">{model.appId}</p>
                          </div>
                        )}
                        <div>
                          <span className="text-sm font-medium text-gray-500">最大Token数:</span>
                          <p className="text-sm">{model.maxTokens}</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-500">温度系数:</span>
                          <p className="text-sm">{model.temperature}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            
            
              <h3 className="mb-3 mt-6 text-lg font-medium text-gray-700">添加新模型</h3>
              <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    AI提供商 *
                  </label>
                  <select
                    value={newModel.provider}
                    onChange={(e) => setNewModel({...newModel, provider: e.target.value})}
                    className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
                  >
                    <option value="openai">OpenAI</option>
                    <option value="dify">Dify</option>
                  </select>
                </div>
                
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      模型名称 *
                    </label>
                    <input
                      type="text"
                      value={newModel.modelName}
                      onChange={(e) => setNewModel({...newModel, modelName: e.target.value})}
                      className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
                      placeholder={newModel.provider === 'openai' ? "例如: GPT-4, GPT-3.5-turbo" : "例如: Dify-Claude"}
                    />
                  </div>
                  
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      API密钥 *
                    </label>
                    <input
                      type="password"
                      value={newModel.apiKey}
                      onChange={(e) => setNewModel({...newModel, apiKey: e.target.value})}
                      className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
                      placeholder={newModel.provider === 'openai' ? "sk-..." : "Bearer token"}
                    />
                  </div>
                  
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      API基础URL *
                    </label>
                    <input
                      type="text"
                      value={newModel.baseUrl}
                      onChange={(e) => setNewModel({...newModel, baseUrl: e.target.value})}
                      className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
                                                  placeholder={newModel.provider === 'openai' ? "https://api.openai-proxy.com/v1" : "http://localhost/v1"}
                    />
                  </div>
                  
                  {newModel.provider === 'dify' && (
                    <div>
                      <label className="mb-1 block text-sm font-medium text-gray-700">
                        应用ID *
                      </label>
                      <input
                        type="text"
                        value={newModel.appId}
                        onChange={(e) => setNewModel({...newModel, appId: e.target.value})}
                        className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
                        placeholder="例如: e15daecf-548c-47da-986c-ed37036d33ea"
                      />
                    </div>
                  )}
                  
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      最大Token数
                    </label>
                    <input
                      type="number"
                      value={newModel.maxTokens}
                      onChange={(e) => setNewModel({...newModel, maxTokens: parseInt(e.target.value)})}
                      className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
                    />
                  </div>
                  
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      温度系数
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      value={newModel.temperature}
                      onChange={(e) => setNewModel({...newModel, temperature: parseFloat(e.target.value)})}
                      className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
                    />
                  </div>
                  
                  <div className="flex items-center">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={newModel.enabled}
                        onChange={(e) => setNewModel({...newModel, enabled: e.target.checked})}
                        className="h-4 w-4 rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">启用此模型</span>
                    </label>
                  </div>
                </div>
                
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={handleAddModel}
                    className="rounded-md bg-orange-500 px-4 py-2 text-white hover:bg-orange-600 focus:outline-none"
                  >
                    添加模型
                  </button>
                </div>
              </div>
            </div>
            
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                默认AI模型
              </label>
              <select
                {...register('defaultModelId')}
                className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
              >
                {settings.aiModels.length > 0 ? (
                  settings.aiModels.map((model, index) => (
                    <option key={index} value={model.modelName}>
                      {model.modelName} {!model.enabled && '(已停用)'} 
                      {model.provider && ` - ${model.provider.toUpperCase()}`}
                    </option>
                  ))
                ) : (
                  <option value="">请先添加模型</option>
                )}
              </select>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                className="mr-4 rounded-md border border-gray-300 bg-white px-4 py-2 text-gray-700 hover:bg-gray-50 focus:outline-none"
                onClick={() => reset(settings)} // 重置为当前状态
              >
                重置
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="rounded-md bg-orange-500 px-4 py-2 text-white hover:bg-orange-600 focus:outline-none disabled:opacity-70"
              >
                {isSubmitting ? '保存中...' : '保存设置'}
              </button>
            </div>
          </div>
        </div>
        
        {/* 安全与访问控制 */}
        <div className={activeTab === 'security' ? 'block' : 'hidden'}>
          <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6 shadow">
            <h2 className="mb-4 text-xl font-semibold text-gray-800">安全与访问控制设置</h2>
            
            <div className="mb-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  {...register('userRegistrationEnabled')}
                  className="h-4 w-4 rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                />
                <span className="ml-2 text-sm text-gray-700">允许新用户注册</span>
              </label>
            </div>
            
            {/* 这里可以添加更多安全相关的设置 */}

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                className="mr-4 rounded-md border border-gray-300 bg-white px-4 py-2 text-gray-700 hover:bg-gray-50 focus:outline-none"
                onClick={() => reset(settings)} // 重置为当前状态
              >
                重置
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="rounded-md bg-orange-500 px-4 py-2 text-white hover:bg-orange-600 focus:outline-none disabled:opacity-70"
              >
                {isSubmitting ? '保存中...' : '保存设置'}
              </button>
            </div>
          </div>
        </div>
        
        {/* Dify配置 */}
        <div className={activeTab === 'dify' ? 'block' : 'hidden'}>
          <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6 shadow">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-800">Dify配置管理</h2>
              <button
                type="button"
                onClick={openCreateDifyConfigDialog}
                className="rounded-md bg-orange-500 px-4 py-2 text-white hover:bg-orange-600 focus:outline-none"
              >
                添加配置
              </button>
            </div>
            
            {/* Dify配置列表 */}
            <div className="space-y-4">
              {difyConfigs.length === 0 ? (
                <div className="rounded-lg border border-gray-200 p-8 text-center">
                  <p className="text-gray-500">暂无Dify配置，点击上方"添加配置"按钮开始配置</p>
                </div>
              ) : (
                difyConfigs.map((config) => (
                  <div key={config.id} className="rounded-lg border border-gray-200 p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h3 className="text-lg font-medium text-gray-900">{config.configName}</h3>
                          <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                            config.enabled 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {config.enabled ? '启用' : '禁用'}
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-gray-600">{config.description || '无描述'}</p>
                        <div className="mt-2 space-y-1 text-sm text-gray-500">
                          <div>基础URL: {config.baseUrl}</div>
                          <div className="flex space-x-4">
                            <span>聊天应用: {config.chatAppId ? '已配置' : '未配置'}</span>
                            <span>方案应用: {config.beautyAppId ? '已配置' : '未配置'}</span>
                            <span>总结应用: {config.summaryAppId ? '已配置' : '未配置'}</span>
                          </div>
                          <div>超时时间: {config.timeoutSeconds}秒 | 重试次数: {config.maxRetries}</div>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          type="button"
                          onClick={() => openEditDifyConfigDialog(config)}
                          className="rounded-md bg-blue-500 px-3 py-1 text-sm text-white hover:bg-blue-600 focus:outline-none"
                        >
                          编辑
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteDifyConfig(config.id)}
                          className="rounded-md bg-red-500 px-3 py-1 text-sm text-white hover:bg-red-600 focus:outline-none"
                        >
                          删除
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Dify配置弹窗 */}
        {showDifyConfigDialog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 shadow-lg">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {isEditingDifyConfig ? '编辑Dify配置' : '创建Dify配置'}
                </h3>
                <button
                  type="button"
                  onClick={() => setShowDifyConfigDialog(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                {/* 基本信息 */}
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">配置名称 *</label>
                    <input
                      type="text"
                      value={newDifyConfig.configName}
                      onChange={(e) => setNewDifyConfig({...newDifyConfig, configName: e.target.value})}
                      className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                      placeholder="例如: 生产环境配置"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">基础URL *</label>
                    <input
                      type="text"
                      value={newDifyConfig.baseUrl}
                      onChange={(e) => setNewDifyConfig({...newDifyConfig, baseUrl: e.target.value})}
                      className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                      placeholder="例如: http://localhost/v1"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">描述</label>
                  <textarea
                    value={newDifyConfig.description}
                    onChange={(e) => setNewDifyConfig({...newDifyConfig, description: e.target.value})}
                    className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                    rows={2}
                    placeholder="配置描述信息"
                  />
                </div>

                {/* Chat应用配置 */}
                <div className="rounded-lg border border-gray-200 p-4">
                  <h4 className="mb-3 font-medium text-gray-900">聊天应用配置</h4>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">应用ID</label>
                      <input
                        type="text"
                        value={newDifyConfig.chatAppId}
                        onChange={(e) => setNewDifyConfig({...newDifyConfig, chatAppId: e.target.value})}
                        className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                        placeholder="例如: app-xxxxxxxxxxxx"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">API密钥</label>
                      <div className="flex space-x-2">
                        <input
                          type="password"
                          value={newDifyConfig.chatApiKey}
                          onChange={(e) => setNewDifyConfig({...newDifyConfig, chatApiKey: e.target.value})}
                          className="mt-1 flex-1 rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                          placeholder="API密钥"
                        />
                        <button
                          type="button"
                          onClick={() => handleTestConnection('chat', newDifyConfig.chatApiKey || '')}
                          disabled={isTestingConnection || !newDifyConfig.chatApiKey}
                          className="mt-1 rounded-md bg-blue-500 px-3 py-2 text-sm text-white hover:bg-blue-600 focus:outline-none disabled:opacity-50"
                        >
                          测试
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Beauty Agent配置 */}
                <div className="rounded-lg border border-gray-200 p-4">
                  <h4 className="mb-3 font-medium text-gray-900">医美方案专家配置</h4>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">应用ID</label>
                      <input
                        type="text"
                        value={newDifyConfig.beautyAppId}
                        onChange={(e) => setNewDifyConfig({...newDifyConfig, beautyAppId: e.target.value})}
                        className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                        placeholder="例如: app-xxxxxxxxxxxx"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">API密钥</label>
                      <div className="flex space-x-2">
                        <input
                          type="password"
                          value={newDifyConfig.beautyApiKey}
                          onChange={(e) => setNewDifyConfig({...newDifyConfig, beautyApiKey: e.target.value})}
                          className="mt-1 flex-1 rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                          placeholder="API密钥"
                        />
                        <button
                          type="button"
                          onClick={() => handleTestConnection('agent', newDifyConfig.beautyApiKey || '')}
                          disabled={isTestingConnection || !newDifyConfig.beautyApiKey}
                          className="mt-1 rounded-md bg-blue-500 px-3 py-2 text-sm text-white hover:bg-blue-600 focus:outline-none disabled:opacity-50"
                        >
                          测试
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Summary Workflow配置 */}
                <div className="rounded-lg border border-gray-200 p-4">
                  <h4 className="mb-3 font-medium text-gray-900">咨询总结工作流配置</h4>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">应用ID</label>
                      <input
                        type="text"
                        value={newDifyConfig.summaryAppId}
                        onChange={(e) => setNewDifyConfig({...newDifyConfig, summaryAppId: e.target.value})}
                        className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                        placeholder="例如: app-xxxxxxxxxxxx"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">API密钥</label>
                      <div className="flex space-x-2">
                        <input
                          type="password"
                          value={newDifyConfig.summaryApiKey}
                          onChange={(e) => setNewDifyConfig({...newDifyConfig, summaryApiKey: e.target.value})}
                          className="mt-1 flex-1 rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                          placeholder="API密钥"
                        />
                        <button
                          type="button"
                          onClick={() => handleTestConnection('workflow', newDifyConfig.summaryApiKey || '')}
                          disabled={isTestingConnection || !newDifyConfig.summaryApiKey}
                          className="mt-1 rounded-md bg-blue-500 px-3 py-2 text-sm text-white hover:bg-blue-600 focus:outline-none disabled:opacity-50"
                        >
                          测试
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 高级设置 */}
                <div className="rounded-lg border border-gray-200 p-4">
                  <h4 className="mb-3 font-medium text-gray-900">高级设置</h4>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">超时时间（秒）</label>
                      <input
                        type="number"
                        value={newDifyConfig.timeoutSeconds}
                        onChange={(e) => setNewDifyConfig({...newDifyConfig, timeoutSeconds: parseInt(e.target.value) || 30})}
                        className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                        min="1"
                        max="300"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">最大重试次数</label>
                      <input
                        type="number"
                        value={newDifyConfig.maxRetries}
                        onChange={(e) => setNewDifyConfig({...newDifyConfig, maxRetries: parseInt(e.target.value) || 3})}
                        className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 focus:border-orange-500 focus:outline-none"
                        min="1"
                        max="10"
                      />
                    </div>
                    <div className="flex items-center">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={newDifyConfig.enabled}
                          onChange={(e) => setNewDifyConfig({...newDifyConfig, enabled: e.target.checked})}
                          className="h-4 w-4 rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">启用配置</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowDifyConfigDialog(false)}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-gray-700 hover:bg-gray-50 focus:outline-none"
                >
                  取消
                </button>
                <button
                  type="button"
                  onClick={isEditingDifyConfig ? handleUpdateDifyConfig : handleCreateDifyConfig}
                  className="rounded-md bg-orange-500 px-4 py-2 text-white hover:bg-orange-600 focus:outline-none"
                >
                  {isEditingDifyConfig ? '更新配置' : '创建配置'}
                </button>
              </div>
            </div>
          </div>
        )}

      </form>
    </div>
  );
} 