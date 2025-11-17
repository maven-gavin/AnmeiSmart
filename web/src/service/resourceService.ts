/**
 * 资源管理服务
 */

import { apiClient } from './apiClient';

export interface Resource {
  id: string;
  name: string;
  displayName?: string;
  description?: string;
  resourceType: 'api' | 'menu';
  resourcePath: string;
  httpMethod?: string;
  parentId?: string;
  isActive: boolean;
  isSystem: boolean;
  priority: number;
  tenantId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ResourceListResponse {
  resources: Resource[];
  total: number;
  skip: number;
  limit: number;
}

export interface CreateResourceRequest {
  name: string;
  displayName?: string;
  description?: string;
  resourceType: 'api' | 'menu';
  resourcePath: string;
  httpMethod?: string;
  parentId?: string;
  tenantId?: string;
  priority?: number;
}

export interface UpdateResourceRequest {
  displayName?: string;
  description?: string;
  resourcePath?: string;
  httpMethod?: string;
  priority?: number;
}

export interface SyncMenusResponse {
  synced_count: number;
  created_count: number;
  updated_count: number;
}

class ResourceService {
  /**
   * 获取资源列表
   */
  async getResources(params?: {
    tenantId?: string;
    resourceType?: 'api' | 'menu';
    skip?: number;
    limit?: number;
  }): Promise<ResourceListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.tenantId) queryParams.append('tenant_id', params.tenantId);
    if (params?.resourceType) queryParams.append('resource_type', params.resourceType);
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());

    const response = await apiClient.get<ResourceListResponse>(
      `/resources?${queryParams.toString()}`
    );
    return response.data;
  }

  /**
   * 获取资源详情
   */
  async getResource(resourceId: string): Promise<Resource> {
    const response = await apiClient.get<Resource>(
      `/resources/${resourceId}`
    );
    return response.data;
  }

  /**
   * 创建资源
   */
  async createResource(data: CreateResourceRequest): Promise<Resource> {
    // 将驼峰命名转换为下划线命名以匹配后端API
    // 将空字符串转换为 null，避免外键约束错误
    const requestData = {
      name: data.name,
      display_name: data.displayName,
      description: data.description,
      resource_type: data.resourceType,
      resource_path: data.resourcePath,
      http_method: data.httpMethod,
      parent_id: data.parentId && data.parentId.trim() ? data.parentId : null,
      tenant_id: data.tenantId && data.tenantId.trim() ? data.tenantId : null,
      priority: data.priority ?? 0,
    };
    const response = await apiClient.post<Resource>(
      '/resources',
      requestData
    );
    return response.data;
  }

  /**
   * 更新资源
   */
  async updateResource(resourceId: string, data: UpdateResourceRequest): Promise<Resource> {
    // 将驼峰命名转换为下划线命名以匹配后端API
    const requestData: any = {};
    if (data.displayName !== undefined) requestData.display_name = data.displayName;
    if (data.description !== undefined) requestData.description = data.description;
    if (data.resourcePath !== undefined) requestData.resource_path = data.resourcePath;
    if (data.httpMethod !== undefined) requestData.http_method = data.httpMethod;
    if (data.priority !== undefined) requestData.priority = data.priority;
    
    const response = await apiClient.put<Resource>(
      `/resources/${resourceId}`,
      requestData
    );
    return response.data;
  }

  /**
   * 删除资源
   */
  async deleteResource(resourceId: string): Promise<void> {
    await apiClient.delete<void>(`/resources/${resourceId}`);
  }

  /**
   * 同步菜单资源
   */
  async syncMenuResources(menus: any[]): Promise<SyncMenusResponse> {
    const response = await apiClient.post<SyncMenusResponse>(
      '/resources/sync-menus',
      { menus, version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0' }
    );
    return response.data;
  }
}

export const resourceService = new ResourceService();

