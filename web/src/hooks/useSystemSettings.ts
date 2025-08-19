import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import systemService, { SystemSettings } from '@/service/systemService';

export function useSystemSettings() {
  const [settings, setSettings] = useState<SystemSettings>({
    siteName: '',
    logoUrl: '',
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

  useEffect(() => {
    loadSettings();
  }, []);

  return {
    settings,
    isLoading,
    isSubmitting,
    updateGeneralSettings,
    updateSecuritySettings,
    loadSettings
  };
} 