import { apiClient } from '@/service/apiClient';

// Dify配置相关的类型定义
export interface DifyConfigInfo {
  id: string;
  configName: string;
  baseUrl: string;
  description?: string;
  
  // 应用配置（不返回API密钥，只显示是否已配置）
  chatAppId?: string;
  chatApiKeyConfigured: boolean;
  
  beautyAppId?: string;
  beautyApiKeyConfigured: boolean;
  
  summaryAppId?: string;
  summaryApiKeyConfigured: boolean;
  
  timeoutSeconds: number;
  maxRetries: number;
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface DifyConfigCreate {
  configName: string;
  baseUrl: string;
  description?: string;
  
  // Chat应用配置
  chatAppId?: string;
  chatApiKey?: string;
  
  // Beauty Agent配置
  beautyAppId?: string;
  beautyApiKey?: string;
  
  // Summary Workflow配置
  summaryAppId?: string;
  summaryApiKey?: string;
  
  timeoutSeconds?: number;
  maxRetries?: number;
  enabled?: boolean;
}

export interface DifyConfigUpdate {
  configName?: string;
  baseUrl?: string;
  description?: string;
  
  // Chat应用配置
  chatAppId?: string;
  chatApiKey?: string;
  
  // Beauty Agent配置
  beautyAppId?: string;
  beautyApiKey?: string;
  
  // Summary Workflow配置
  summaryAppId?: string;
  summaryApiKey?: string;
  
  timeoutSeconds?: number;
  maxRetries?: number;
  enabled?: boolean;
}

export interface DifyTestConnectionRequest {
  baseUrl: string;
  apiKey: string;
  appType: 'chat' | 'agent' | 'workflow';
}

export interface DifyTestConnectionResponse {
  success: boolean;
  message: string;
  appInfo?: {
    name: string;
    mode: string;
    status: string;
  };
}

export interface DifyConfigResponse {
  success: boolean;
  data: DifyConfigInfo;
  message: string;
}

export interface DifyConfigListResponse {
  success: boolean;
  data: DifyConfigInfo[];
  message: string;
}

const difyConfigService = {
  /**
   * 获取Dify配置列表
   */
  async getDifyConfigs(): Promise<DifyConfigInfo[]> {
    try {
      const response = await apiClient.get<DifyConfigListResponse>('/dify/configs');
      return response.data?.data || [];
    } catch (error) {
      console.error('获取Dify配置列表失败:', error);
      throw error;
    }
  },

  /**
   * 获取单个Dify配置详情
   */
  async getDifyConfig(configId: string): Promise<DifyConfigInfo> {
    try {
      const response = await apiClient.get<DifyConfigResponse>(`/dify/configs/${configId}`);
      if (!response.data?.data) {
        throw new Error('配置不存在');
      }
      return response.data.data;
    } catch (error) {
      console.error('获取Dify配置详情失败:', error);
      throw error;
    }
  },

  /**
   * 创建Dify配置
   */
  async createDifyConfig(configData: DifyConfigCreate): Promise<DifyConfigInfo> {
    try {
      const response = await apiClient.post<DifyConfigResponse>('/dify/configs', configData);
      if (!response.data?.data) {
        throw new Error('创建配置失败');
      }
      return response.data.data;
    } catch (error) {
      console.error('创建Dify配置失败:', error);
      throw error;
    }
  },

  /**
   * 更新Dify配置
   */
  async updateDifyConfig(configId: string, configData: DifyConfigUpdate): Promise<DifyConfigInfo> {
    try {
      const response = await apiClient.put<DifyConfigResponse>(`/dify/configs/${configId}`, configData);
      if (!response.data?.data) {
        throw new Error('更新配置失败');
      }
      return response.data.data;
    } catch (error) {
      console.error('更新Dify配置失败:', error);
      throw error;
    }
  },

  /**
   * 删除Dify配置
   */
  async deleteDifyConfig(configId: string): Promise<void> {
    try {
      await apiClient.delete(`/dify/configs/${configId}`);
    } catch (error) {
      console.error('删除Dify配置失败:', error);
      throw error;
    }
  },

  /**
   * 测试Dify连接
   */
  async testDifyConnection(requestData: DifyTestConnectionRequest): Promise<DifyTestConnectionResponse> {
    try {
      const response = await apiClient.post<DifyTestConnectionResponse>('/dify/test-connection', requestData);
      return response.data || { success: false, message: '测试失败' };
    } catch (error) {
      console.error('测试Dify连接失败:', error);
      throw error;
    }
  }
};

export default difyConfigService; 