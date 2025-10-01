/**
 * Agent配置管理服务
 * 与后端API交互，管理Agent应用配置
 */

import { apiClient } from './apiClient';

// 更新后的Agent配置接口，匹配新的数据库结构
export interface AgentConfig {
  id: string;
  environment: string;
  appId: string;
  appName: string;
  agentType?: string;
  baseUrl: string;
  timeoutSeconds: number;
  maxRetries: number;
  enabled: boolean;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AgentConfigCreate {
  environment: string;
  appId: string;
  appName: string;
  agentType?: string;
  apiKey: string;
  baseUrl: string;
  timeoutSeconds: number;
  maxRetries: number;
  enabled: boolean;
  description?: string;
}

export interface AgentConfigUpdate {
  environment?: string;
  appId?: string;
  appName?: string;
  agentType?: string;
  apiKey?: string;
  baseUrl?: string;
  timeoutSeconds?: number;
  maxRetries?: number;
  enabled?: boolean;
  description?: string;
}

export interface TestConnectionResult {
  success: boolean;
  message: string;
  details?: any;
}

export interface AgentConfigResponse {
  success: boolean;
  data: AgentConfig;
  message: string;
}

export interface AgentConfigListResponse {
  success: boolean;
  data: AgentConfig[];
  message: string;
}

/**
 * 获取所有Agent配置
 * @returns Promise<AgentConfig[]>
 */
export const getAgentConfigs = async (): Promise<AgentConfig[]> => {
  try {
    const response = await apiClient.get<AgentConfigListResponse>('/agent/configs');
    return response.data.data;
  } catch (error) {
    console.error('获取Agent配置列表失败:', error);
    throw error;
  }
};

/**
 * 根据ID获取Agent配置
 * @param configId 配置ID
 * @returns Promise<AgentConfig>
 */
export const getAgentConfig = async (configId: string): Promise<AgentConfig> => {
  try {
    const response = await apiClient.get<AgentConfigResponse>(`/agent/configs/${configId}`);
    return response.data.data;
  } catch (error) {
    console.error('获取Agent配置详情失败:', error);
    throw error;
  }
};

/**
 * 创建Agent配置
 * @param config 配置数据
 * @returns Promise<AgentConfig>
 */
export const createAgentConfig = async (config: AgentConfigCreate): Promise<AgentConfig> => {
  try {
    const response = await apiClient.post<AgentConfigResponse>(
      '/agent/configs',
      { body: config }
    );
    return response.data.data;
  } catch (error) {
    console.error('创建Agent配置失败:', error);
    throw error;
  }
};

/**
 * 更新Agent配置
 * @param configId 配置ID
 * @param config 更新数据
 * @returns Promise<AgentConfig>
 */
export const updateAgentConfig = async (
  configId: string,
  config: AgentConfigUpdate
): Promise<AgentConfig> => {
  try {
    const response = await apiClient.put<AgentConfigResponse>(
      `/agent/configs/${configId}`, 
      { body: config }
    );
    return response.data.data;
  } catch (error) {
    console.error('更新Agent配置失败:', error);
    throw error;
  }
};

/**
 * 删除Agent配置
 * @param configId 配置ID
 * @returns Promise<void>
 */
export const deleteAgentConfig = async (configId: string): Promise<void> => {
  try {
    await apiClient.delete(`/agent/configs/${configId}`);
  } catch (error) {
    console.error('删除Agent配置失败:', error);
    throw error;
  }
};

/**
 * 测试Agent连接
 * @param config 配置数据
 * @returns Promise<TestConnectionResult>
 */
export const testAgentConnection = async (config: AgentConfig): Promise<TestConnectionResult> => {
  try {
    const response = await apiClient.post<TestConnectionResult>(
      '/agent/test-connection',
      { body: config }
    );
    return response.data;
  } catch (error) {
    console.error('测试Agent连接失败:', error);
    throw error;
  }
};

/**
 * 重载AI Gateway配置
 * @returns Promise<void>
 */
export const reloadAIGateway = async (): Promise<void> => {
  try {
    await apiClient.post('/agent/reload-gateway');
  } catch (error) {
    console.error('重载AI Gateway失败:', error);
    throw error;
  }
};

// 导出默认对象
const agentConfigService = {
  getAgentConfigs,
  getAgentConfig,
  createAgentConfig,
  updateAgentConfig,
  deleteAgentConfig,
  testAgentConnection,
  reloadAIGateway,
};

export default agentConfigService; 