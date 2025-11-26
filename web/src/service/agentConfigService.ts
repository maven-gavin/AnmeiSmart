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
 * 将后端返回的下划线命名数据转换为前端使用的驼峰命名
 */
const mapAgentConfigFromApi = (apiData: any): AgentConfig => {
  return {
    id: apiData.id,
    environment: apiData.environment,
    appId: apiData.app_id || apiData.appId,
    appName: apiData.app_name || apiData.appName,
    agentType: apiData.agent_type || apiData.agentType,
    baseUrl: apiData.base_url || apiData.baseUrl,
    timeoutSeconds: apiData.timeout_seconds || apiData.timeoutSeconds,
    maxRetries: apiData.max_retries || apiData.maxRetries,
    enabled: apiData.enabled,
    description: apiData.description,
    createdAt: apiData.created_at || apiData.createdAt,
    updatedAt: apiData.updated_at || apiData.updatedAt
  };
};

/**
 * 获取所有Agent配置
 * @returns Promise<AgentConfig[]>
 */
export const getAgentConfigs = async (): Promise<AgentConfig[]> => {
  try {
    const response = await apiClient.get<any>('/agent/configs');
    const data = response.data.data || [];
    
    // 转换字段名从下划线到驼峰
    return Array.isArray(data) 
      ? data.map(mapAgentConfigFromApi)
      : [];
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
    const response = await apiClient.get<any>(`/agent/configs/${configId}`);
    const data = response.data.data;
    
    // 转换字段名从下划线到驼峰
    return mapAgentConfigFromApi(data);
  } catch (error) {
    console.error('获取Agent配置详情失败:', error);
    throw error;
  }
};

/**
 * 将前端使用的驼峰命名转换为后端需要的下划线命名
 */
const mapAgentConfigToApi = (config: AgentConfigCreate | AgentConfigUpdate): any => {
  const result: any = {};
  
  if ('environment' in config && config.environment !== undefined) result.environment = config.environment;
  if ('appId' in config && config.appId !== undefined) result.app_id = config.appId;
  if ('appName' in config && config.appName !== undefined) result.app_name = config.appName;
  if ('agentType' in config && config.agentType !== undefined) result.agent_type = config.agentType;
  if ('apiKey' in config && config.apiKey !== undefined) result.api_key = config.apiKey;
  if ('baseUrl' in config && config.baseUrl !== undefined) result.base_url = config.baseUrl;
  if ('timeoutSeconds' in config && config.timeoutSeconds !== undefined) result.timeout_seconds = config.timeoutSeconds;
  if ('maxRetries' in config && config.maxRetries !== undefined) result.max_retries = config.maxRetries;
  if ('enabled' in config && config.enabled !== undefined) result.enabled = config.enabled;
  if ('description' in config && config.description !== undefined) result.description = config.description;
  
  return result;
};

/**
 * 创建Agent配置
 * @param config 配置数据
 * @returns Promise<AgentConfig>
 */
export const createAgentConfig = async (config: AgentConfigCreate): Promise<AgentConfig> => {
  try {
    // 转换字段名从驼峰到下划线
    const apiData = mapAgentConfigToApi(config);
    
    const response = await apiClient.post<any>(
      '/agent/configs',
      { body: apiData }
    );
    
    const data = response.data.data;
    // 转换返回数据的字段名从下划线到驼峰
    return mapAgentConfigFromApi(data);
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
    // 转换字段名从驼峰到下划线
    const apiData = mapAgentConfigToApi(config);
    
    const response = await apiClient.put<any>(
      `/agent/configs/${configId}`, 
      { body: apiData }
    );
    
    const data = response.data.data;
    // 转换返回数据的字段名从下划线到驼峰
    return mapAgentConfigFromApi(data);
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
    // 确保配置有 id 和 appId（后端需要这些字段）
    if (!config.id) {
      throw new Error('配置ID缺失，无法测试连接');
    }
    if (!config.appId) {
      throw new Error('应用ID缺失，无法测试连接');
    }
    
    // 将前端格式转换为后端期望的格式
    const requestBody = {
      id: config.id,
      environment: config.environment,
      appId: config.appId, // 确保使用 appId（后端期望 appId）
      appName: config.appName,
      agentType: config.agentType,
      baseUrl: config.baseUrl,
      timeoutSeconds: config.timeoutSeconds,
      maxRetries: config.maxRetries,
      enabled: config.enabled,
      description: config.description
    };
    
    const response = await apiClient.post<TestConnectionResult>(
      '/agent/test-connection',
      { body: requestBody }
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