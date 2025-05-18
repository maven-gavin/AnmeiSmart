'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import systemService, { SystemSettings, AIModelConfig } from '@/services/systemService';

export default function SystemSettingsPage() {
  const [activeTab, setActiveTab] = useState('general');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  // 系统设置状态
  const [settings, setSettings] = useState<SystemSettings>({
    siteName: '',
    logoUrl: '',
    themeColor: '',
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
    enabled: true
  });

  const { register, handleSubmit, formState: { errors }, reset } = useForm<SystemSettings>();

  // 加载系统设置
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setIsLoading(true);
        const data = await systemService.getSystemSettings();
        setSettings(data);
        reset(data); // 重置表单为获取到的数据
        setIsLoading(false);
      } catch (error) {
        console.error('加载系统设置失败:', error);
        toast.error('加载系统设置失败');
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
    if (!newModel.modelName || !newModel.apiKey || !newModel.baseUrl) {
      toast.error('请填写所有必填字段');
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
        enabled: true
      });
      
      toast.success('AI模型已添加');
    } catch (error) {
      console.error('添加AI模型失败:', error);
      toast.error('添加AI模型失败');
    }
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
      </div>
      
      <form onSubmit={handleSubmit(onSubmit)}>
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
              <label className="mb-2 block text-sm font-medium text-gray-700">
                主题颜色
              </label>
              <div className="flex items-center">
                <input
                  type="color"
                  {...register('themeColor')}
                  className="h-10 w-20 rounded-md border border-gray-300"
                />
                <input
                  type="text"
                  {...register('themeColor')}
                  className="ml-2 w-40 rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
                />
              </div>
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
          </div>
        </div>
        
        {/* AI模型配置 */}
        <div className={activeTab === 'ai' ? 'block' : 'hidden'}>
          <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6 shadow">
            <h2 className="mb-4 text-xl font-semibold text-gray-800">AI模型配置</h2>
            
            <div className="mb-6">
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
            </div>
            
            <div className="mb-4">
              <h3 className="mb-3 text-lg font-medium text-gray-700">添加新模型</h3>
              <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-4">
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
                      placeholder="例如: GPT-4, Claude 3"
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
                      placeholder="sk-..."
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
                      placeholder="https://api.openai.com/v1"
                    />
                  </div>
                  
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
                {settings.aiModels.map((model, index) => (
                  <option key={index} value={model.modelName}>
                    {model.modelName} {!model.enabled && '(已停用)'}
                  </option>
                ))}
              </select>
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
          </div>
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
      </form>
    </div>
  );
} 