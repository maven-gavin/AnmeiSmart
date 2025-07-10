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
      const response = await apiClient.get<{success: boolean, data: SystemSettings, message: string}>('/system/settings');
      const responseData = response.data as any;
      return responseData.data || responseData; // 兼容两种响应格式
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
      const response = await apiClient.put<{success: boolean, data: SystemSettings, message: string}>('/system/settings', settings);
      const responseData = response.data as any;
      return responseData.data || responseData; // 兼容两种响应格式
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
      const response = await apiClient.get<{success: boolean, data: AIModelConfig[], message: string}>('/system/ai-models');
      const responseData = response.data as any;
      return responseData.data || responseData; // 兼容两种响应格式
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
      const response = await apiClient.post<{success: boolean, data: AIModelConfig, message: string}>('/system/ai-models', modelConfig);
      const responseData = response.data as any;
      return responseData.data || responseData; // 兼容两种响应格式
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
      const response = await apiClient.put<{success: boolean, data: AIModelConfig, message: string}>(`/system/ai-models/${modelName}`, modelConfig);
      const responseData = response.data as any;
      return responseData.data || responseData; // 兼容两种响应格式
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
      await apiClient.delete(`/system/ai-models/${modelName}`);
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
      const response = await apiClient.post<{success: boolean, data: AIModelConfig, message: string}>(`/system/ai-models/${modelName}/toggle`);
      const responseData = response.data as any;
      return responseData.data || responseData; // 兼容两种响应格式
    } catch (error) {
      console.error('切换AI模型状态失败:', error);
      throw error;
    }
  },
};

export default systemService;
export type { SystemSettings, AIModelConfig }; 