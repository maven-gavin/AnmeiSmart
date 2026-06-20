import { apiClient } from '@/service/apiClient';

interface SystemSettings {
  siteName: string;
  logoUrl: string;
  aiModels?: AIModel[];
  defaultModelId?: string;
  maintenanceMode?: boolean;
  userRegistrationEnabled: boolean;
}

export interface AIModel {
  modelName: string;
  apiKey?: string;
  baseUrl: string;
  maxTokens: number;
  temperature: number;
  enabled: boolean;
}

interface ApiEnvelope<T> {
  success?: boolean;
  data?: T;
  message?: string;
}

function unwrapApiData<T>(payload: ApiEnvelope<T> | T): T {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return (payload as ApiEnvelope<T>).data as T;
  }
  return payload as T;
}

const systemService = {
  /**
   * 获取系统设置
   */
  async getSystemSettings(): Promise<SystemSettings> {
    try {
      const response = await apiClient.get<{success: boolean, data: SystemSettings, message: string}>('/system/settings');
      return unwrapApiData<SystemSettings>(response.data);
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
      return unwrapApiData<SystemSettings>(response.data);
    } catch (error) {
      console.error('更新系统设置失败:', error);
      throw error;
    }
  },

  async getAIModels(): Promise<AIModel[]> {
    const response = await apiClient.get<ApiEnvelope<AIModel[]> | AIModel[]>('/system/ai-models');
    return unwrapApiData<AIModel[]>(response.data);
  },

  async createAIModel(model: AIModel): Promise<AIModel> {
    const response = await apiClient.post<ApiEnvelope<AIModel> | AIModel>('/system/ai-models', model);
    return unwrapApiData<AIModel>(response.data);
  },

  async updateAIModel(modelName: string, model: Partial<AIModel>): Promise<AIModel> {
    const response = await apiClient.put<ApiEnvelope<AIModel> | AIModel>(
      `/system/ai-models/${encodeURIComponent(modelName)}`,
      model,
    );
    return unwrapApiData<AIModel>(response.data);
  },

  async deleteAIModel(modelName: string): Promise<void> {
    await apiClient.delete(`/system/ai-models/${encodeURIComponent(modelName)}`);
  },

  async toggleAIModelStatus(modelName: string): Promise<AIModel> {
    const response = await apiClient.post<ApiEnvelope<AIModel> | AIModel>(
      `/system/ai-models/${encodeURIComponent(modelName)}/toggle`,
    );
    return unwrapApiData<AIModel>(response.data);
  },
};

export default systemService;
export type { SystemSettings}; 