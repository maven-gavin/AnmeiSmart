/**
 * Dify配置管理服务
 * 与后端API交互，管理Dify应用配置
 */

import { apiClient } from './apiClient';

// 更新后的Dify配置接口，匹配新的数据库结构
export interface DifyConfig {
  id: string;
  environment: string;
  appId: string;
  appName: string;
  baseUrl: string;
  timeoutSeconds: number;
  maxRetries: number;
  enabled: boolean;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface DifyConfigCreate {
  environment: string;
  appId: string;
  appName: string;
  apiKey: string;
  baseUrl: string;
  timeoutSeconds: number;
  maxRetries: number;
  enabled: boolean;
  description?: string;
}

export interface DifyConfigUpdate {
  environment?: string;
  appId?: string;
  appName?: string;
  apiKey?: string;
  baseUrl?: string;
  timeoutSeconds?: number;
  maxRetries?: number;
  enabled?: boolean;
  description?: string;
}

export interface DifyConfigResponse {
  success: boolean;
  data: DifyConfig;
  message: string;
}

export interface DifyConfigListResponse {
  success: boolean;
  data: DifyConfig[];
  message: string;
}

export interface TestConnectionResult {
  success: boolean;
  message: string;
  details?: any;
}

/**
 * 获取所有Dify配置
 */
export const getDifyConfigs = async (): Promise<DifyConfig[]> => {
  try {
    const response = await apiClient.get<DifyConfigListResponse>('/dify/configs');
    if (!response.data?.data) {
      throw new Error('获取配置列表失败');
    }
    return response.data.data;
  } catch (error) {
    console.error('获取Dify配置列表失败:', error);
    throw error;
  }
};

/**
 * 根据ID获取Dify配置
 */
export const getDifyConfig = async (configId: string): Promise<DifyConfig> => {
  try {
    const response = await apiClient.get<DifyConfigResponse>(`/dify/configs/${configId}`);
    if (!response.data?.data) {
      throw new Error('获取配置详情失败');
    }
    return response.data.data;
  } catch (error) {
    console.error('获取Dify配置详情失败:', error);
    throw error;
  }
};

/**
 * 创建Dify配置
 */
export const createDifyConfig = async (config: DifyConfigCreate): Promise<DifyConfig> => {
  try {
    const response = await apiClient.post<DifyConfigResponse>('/dify/configs', config);
    if (!response.data?.data) {
      throw new Error('创建配置失败');
    }
    return response.data.data;
  } catch (error) {
    console.error('创建Dify配置失败:', error);
    throw error;
  }
};

/**
 * 更新Dify配置
 */
export const updateDifyConfig = async (
  configId: string, 
  config: DifyConfigUpdate
): Promise<DifyConfig> => {
  try {
    const response = await apiClient.put<DifyConfigResponse>(`/dify/configs/${configId}`, config);
    if (!response.data?.data) {
      throw new Error('更新配置失败');
    }
    return response.data.data;
  } catch (error) {
    console.error('更新Dify配置失败:', error);
    throw error;
  }
};

/**
 * 删除Dify配置
 */
export const deleteDifyConfig = async (configId: string): Promise<void> => {
  try {
    await apiClient.delete(`/dify/configs/${configId}`);
  } catch (error) {
    console.error('删除Dify配置失败:', error);
    throw error;
  }
};

/**
 * 测试Dify连接
 */
export const testDifyConnection = async (config: DifyConfig): Promise<TestConnectionResult> => {
  try {
    const response = await apiClient.post<TestConnectionResult>('/dify/test-connection', config);
    if (!response.data) {
      throw new Error('测试连接失败');
    }
    return response.data;
  } catch (error) {
    console.error('测试Dify连接失败:', error);
    throw error;
  }
};

/**
 * 重载AI Gateway配置
 */
export const reloadAIGateway = async (): Promise<void> => {
  try {
    await apiClient.post('/dify/reload-gateway');
  } catch (error) {
    console.error('重载AI Gateway配置失败:', error);
    throw error;
  }
};

export default {
  getDifyConfigs,
  getDifyConfig,
  createDifyConfig,
  updateDifyConfig,
  deleteDifyConfig,
  testDifyConnection,
  reloadAIGateway,
}; 