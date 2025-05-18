import axios from 'axios';
import { API_BASE_URL } from '@/config';

interface AIModelConfig {
  modelName: string;
  apiKey: string;
  baseUrl: string;
  maxTokens: number;
  temperature: number;
  enabled: boolean;
}

interface SystemSettings {
  siteName: string;
  logoUrl: string;
  themeColor: string;
  aiModels: AIModelConfig[];
  defaultModelId: string;
  maintenanceMode: boolean;
  userRegistrationEnabled: boolean;
}

interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
}

const systemService = {
  /**
   * 获取系统设置
   */
  async getSystemSettings(): Promise<SystemSettings> {
    try {
      const response = await axios.get<ApiResponse<SystemSettings>>(
        `${API_BASE_URL}/system/settings`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
          withCredentials: true,
        }
      );
      return response.data.data;
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
      const response = await axios.put<ApiResponse<SystemSettings>>(
        `${API_BASE_URL}/system/settings`,
        settings,
        {
          headers: {
            'Content-Type': 'application/json',
          },
          withCredentials: true,
        }
      );
      return response.data.data;
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
      const response = await axios.get<ApiResponse<AIModelConfig[]>>(
        `${API_BASE_URL}/system/ai-models`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
          withCredentials: true,
        }
      );
      return response.data.data;
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
      const response = await axios.post<ApiResponse<AIModelConfig>>(
        `${API_BASE_URL}/system/ai-models`,
        modelConfig,
        {
          headers: {
            'Content-Type': 'application/json',
          },
          withCredentials: true,
        }
      );
      return response.data.data;
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
      const response = await axios.put<ApiResponse<AIModelConfig>>(
        `${API_BASE_URL}/system/ai-models/${modelName}`,
        modelConfig,
        {
          headers: {
            'Content-Type': 'application/json',
          },
          withCredentials: true,
        }
      );
      return response.data.data;
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
      await axios.delete(`${API_BASE_URL}/system/ai-models/${modelName}`, {
        headers: {
          'Content-Type': 'application/json',
        },
        withCredentials: true,
      });
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
      const response = await axios.post<ApiResponse<AIModelConfig>>(
        `${API_BASE_URL}/system/ai-models/${modelName}/toggle`,
        {},
        {
          headers: {
            'Content-Type': 'application/json',
          },
          withCredentials: true,
        }
      );
      return response.data.data;
    } catch (error) {
      console.error('切换AI模型状态失败:', error);
      throw error;
    }
  },
};

export default systemService;
export type { SystemSettings, AIModelConfig }; 