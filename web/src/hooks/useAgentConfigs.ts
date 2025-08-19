import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import agentConfigService, {
  AgentConfig,
  AgentConfigCreate,
  AgentConfigUpdate
} from '@/service/agentConfigService';

export function useAgentConfigs() {
  const [configs, setConfigs] = useState<AgentConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isTestingConnection, setIsTestingConnection] = useState(false);

  // 加载配置列表
  const loadConfigs = async () => {
    try {
      setIsLoading(true);
      const configsData = await agentConfigService.getAgentConfigs();
      setConfigs(configsData);
    } catch (error) {
      console.error('加载Agent配置失败:', error);
      toast.error('加载Agent配置失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 创建配置
  const createConfig = async (configData: AgentConfigCreate): Promise<void> => {
    try {
      const newConfig = await agentConfigService.createAgentConfig(configData);
      setConfigs(prev => [newConfig, ...prev]);
      toast.success('创建Agent配置成功');
    } catch (error) {
      console.error('创建Agent配置失败:', error);
      toast.error('创建Agent配置失败');
      throw error;
    }
  };

  // 更新配置
  const updateConfig = async (configId: string, configData: AgentConfigUpdate): Promise<void> => {
    try {
      const updatedConfig = await agentConfigService.updateAgentConfig(configId, configData);
      setConfigs(prev => prev.map(config => 
        config.id === configId ? updatedConfig : config
      ));
      toast.success('更新Agent配置成功');
    } catch (error) {
      console.error('更新Agent配置失败:', error);
      toast.error('更新Agent配置失败');
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
      
      await agentConfigService.deleteAgentConfig(configId);
      setConfigs(prev => prev.filter(config => config.id !== configId));
      toast.success('删除Agent配置成功');
    } catch (error) {
      console.error('删除Agent配置失败:', error);
      toast.error(error instanceof Error ? error.message : '删除Agent配置失败');
      throw error;
    }
  };

  // 测试连接
  const testConnection = async (config: AgentConfig): Promise<void> => {
    try {
      setIsTestingConnection(true);
      const result = await agentConfigService.testAgentConnection(config);
      
      if (result.success) {
        toast.success(`${config.appName} 连接测试成功`);
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      console.error('测试Agent连接失败:', error);
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