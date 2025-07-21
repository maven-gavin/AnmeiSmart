import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import difyConfigService, { 
  DifyConfig, 
  DifyConfigCreate, 
  DifyConfigUpdate 
} from '@/service/difyConfigService';

export function useDifyConfigs() {
  const [configs, setConfigs] = useState<DifyConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isTestingConnection, setIsTestingConnection] = useState(false);

  // 加载配置列表
  const loadConfigs = async () => {
    try {
      setIsLoading(true);
      const configsData = await difyConfigService.getDifyConfigs();
      setConfigs(configsData);
    } catch (error) {
      console.error('加载Dify配置失败:', error);
      toast.error('加载Dify配置失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 创建配置
  const createConfig = async (configData: DifyConfigCreate): Promise<void> => {
    try {
      const newConfig = await difyConfigService.createDifyConfig(configData);
      setConfigs(prev => [newConfig, ...prev]);
      toast.success('创建Dify配置成功');
    } catch (error) {
      console.error('创建Dify配置失败:', error);
      toast.error('创建Dify配置失败');
      throw error;
    }
  };

  // 更新配置
  const updateConfig = async (configId: string, configData: DifyConfigUpdate): Promise<void> => {
    try {
      const updatedConfig = await difyConfigService.updateDifyConfig(configId, configData);
      setConfigs(prev => prev.map(config => 
        config.id === configId ? updatedConfig : config
      ));
      toast.success('更新Dify配置成功');
    } catch (error) {
      console.error('更新Dify配置失败:', error);
      toast.error('更新Dify配置失败');
      throw error;
    }
  };

  // 删除配置
  const deleteConfig = async (configId: string): Promise<void> => {
    try {
      const config = configs.find(c => c.id === configId);
      if (config?.enabled) {
        throw new Error('启用配置不可删除，请先禁用配置');
      }
      
      await difyConfigService.deleteDifyConfig(configId);
      setConfigs(prev => prev.filter(config => config.id !== configId));
      toast.success('删除Dify配置成功');
    } catch (error) {
      console.error('删除Dify配置失败:', error);
      toast.error(error instanceof Error ? error.message : '删除Dify配置失败');
      throw error;
    }
  };

  // 测试连接
  const testConnection = async (config: DifyConfig): Promise<void> => {
    try {
      setIsTestingConnection(true);
      const result = await difyConfigService.testDifyConnection(config);
      
      if (result.success) {
        toast.success(`${config.appName} 连接测试成功`);
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      console.error('测试Dify连接失败:', error);
      toast.error(error instanceof Error ? error.message : '连接测试失败');
      throw error;
    } finally {
      setIsTestingConnection(false);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  return {
    configs,
    isLoading,
    isTestingConnection,
    createConfig,
    updateConfig,
    deleteConfig,
    testConnection,
    refreshConfigs: loadConfigs
  };
} 