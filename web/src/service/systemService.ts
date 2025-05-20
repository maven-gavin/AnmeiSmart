import { apiClient } from '@/service/apiClient';

interface AIModelConfig {
  modelName: string;
  apiKey: string;
  baseUrl: string;
  maxTokens: number;
  temperature: number;
  enabled: boolean;
  provider?: string;  // 添加提供商字段：openai, dify等
  appId?: string;     // Dify应用ID
}

interface SystemSettings {
  siteName: string;
  logoUrl: string;
  aiModels: AIModelConfig[];
  defaultModelId: string;
  maintenanceMode: boolean;
  userRegistrationEnabled: boolean;
}

const systemService = {
  /**
   * 获取系统设置
   */
  async getSystemSettings(): Promise<SystemSettings> {
    try {
      const response = await apiClient.get('/system/settings');
      if (!response.ok) {
        throw new Error(`获取系统设置失败: ${response.status}`);
      }
      return response.data?.data;
    } catch (error) {
      console.error('获取系统设置失败:', error);
      throw error;
    }
  },

  /**
   * 更新系统设置
   */
  async updateSystemSettings(settings: Partial<SystemSettings>): Promise<SystemSettings> {
    try {
      const response = await apiClient.put('/system/settings', settings);
      if (!response.ok) {
        throw new Error(`更新系统设置失败: ${response.status}`);
      }
      return response.data?.data;
    } catch (error) {
      console.error('更新系统设置失败:', error);
      throw error;
    }
  },

  /**
   * 获取所有AI模型配置
   */
  async getAIModels(): Promise<AIModelConfig[]> {
    try {
      const response = await apiClient.get('/system/ai-models');
      if (!response.ok) {
        throw new Error(`获取AI模型配置失败: ${response.status}`);
      }
      return response.data?.data;
    } catch (error) {
      console.error('获取AI模型配置失败:', error);
      throw error;
    }
  },

  /**
   * 创建AI模型配置
   */
  async createAIModel(modelConfig: AIModelConfig): Promise<AIModelConfig> {
    try {
      const response = await apiClient.post('/system/ai-models', modelConfig);
      if (!response.ok) {
        throw new Error(`创建AI模型配置失败: ${response.status}`);
      }
      return response.data?.data;
    } catch (error) {
      console.error('创建AI模型配置失败:', error);
      throw error;
    }
  },

  /**
   * 更新AI模型配置
   */
  async updateAIModel(modelName: string, modelConfig: Partial<AIModelConfig>): Promise<AIModelConfig> {
    try {
      const response = await apiClient.put(`/system/ai-models/${modelName}`, modelConfig);
      if (!response.ok) {
        throw new Error(`更新AI模型配置失败: ${response.status}`);
      }
      return response.data?.data;
    } catch (error) {
      console.error('更新AI模型配置失败:', error);
      throw error;
    }
  },

  /**
   * 删除AI模型配置
   */
  async deleteAIModel(modelName: string): Promise<void> {
    try {
      const response = await apiClient.delete(`/system/ai-models/${modelName}`);
      if (!response.ok) {
        throw new Error(`删除AI模型配置失败: ${response.status}`);
      }
    } catch (error) {
      console.error('删除AI模型配置失败:', error);
      throw error;
    }
  },

  /**
   * 切换AI模型状态
   */
  async toggleAIModelStatus(modelName: string): Promise<AIModelConfig> {
    try {
      const response = await apiClient.post(`/system/ai-models/${modelName}/toggle`);
      if (!response.ok) {
        throw new Error(`切换AI模型状态失败: ${response.status}`);
      }
      return response.data?.data;
    } catch (error) {
      console.error('切换AI模型状态失败:', error);
      throw error;
    }
  },
};

export default systemService;
export type { SystemSettings, AIModelConfig }; 