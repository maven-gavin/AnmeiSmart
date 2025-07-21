import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import systemService, { SystemSettings, AIModelConfig } from '@/service/systemService';

export function useSystemSettings() {
  const [settings, setSettings] = useState<SystemSettings>({
    siteName: '',
    logoUrl: '',
    aiModels: [],
    defaultModelId: '',
    maintenanceMode: false,
    userRegistrationEnabled: true
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 加载系统设置
  const loadSettings = async () => {
    try {
      setIsLoading(true);
      const settingsData = await systemService.getSystemSettings();
      setSettings(settingsData);
    } catch (error) {
      console.error('加载设置失败:', error);
      toast.error('加载设置失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 更新基本设置
  const updateGeneralSettings = async (data: {
    siteName: string;
    logoUrl: string;
    maintenanceMode: boolean;
  }) => {
    setIsSubmitting(true);
    try {
      const updatedSettings = await systemService.updateSystemSettings({
        ...settings,
        ...data
      });
      setSettings(updatedSettings);
      toast.success('基本设置已保存');
    } catch (error) {
      console.error('保存基本设置失败:', error);
      toast.error('保存基本设置失败');
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  // 更新安全设置
  const updateSecuritySettings = async (data: {
    userRegistrationEnabled: boolean;
  }) => {
    setIsSubmitting(true);
    try {
      const updatedSettings = await systemService.updateSystemSettings({
        ...settings,
        ...data
      });
      setSettings(updatedSettings);
      toast.success('安全设置已保存');
    } catch (error) {
      console.error('保存安全设置失败:', error);
      toast.error('保存安全设置失败');
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  // 添加AI模型
  const addAIModel = async (model: AIModelConfig) => {
    try {
      await systemService.createAIModel(model);
      await loadSettings(); // 重新加载设置
      toast.success('AI模型已添加');
    } catch (error) {
      console.error('添加AI模型失败:', error);
      toast.error('添加AI模型失败');
      throw error;
    }
  };

  // 删除AI模型
  const removeAIModel = async (modelName: string) => {
    try {
      await systemService.deleteAIModel(modelName);
      await loadSettings(); // 重新加载设置
      toast.success('AI模型已删除');
    } catch (error) {
      console.error('删除AI模型失败:', error);
      toast.error('删除AI模型失败');
      throw error;
    }
  };

  // 切换AI模型状态
  const toggleAIModelStatus = async (modelName: string) => {
    try {
      await systemService.toggleAIModelStatus(modelName);
      await loadSettings(); // 重新加载设置
    } catch (error) {
      console.error('切换AI模型状态失败:', error);
      toast.error('切换AI模型状态失败');
      throw error;
    }
  };

  // 更新默认模型
  const updateDefaultModel = async (modelId: string) => {
    setIsSubmitting(true);
    try {
      const updatedSettings = await systemService.updateSystemSettings({
        ...settings,
        defaultModelId: modelId
      });
      setSettings(updatedSettings);
      toast.success('默认模型已更新');
    } catch (error) {
      console.error('更新默认模型失败:', error);
      toast.error('更新默认模型失败');
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  return {
    settings,
    isLoading,
    isSubmitting,
    updateGeneralSettings,
    updateSecuritySettings,
    addAIModel,
    removeAIModel,
    toggleAIModelStatus,
    updateDefaultModel,
    loadSettings
  };
} 