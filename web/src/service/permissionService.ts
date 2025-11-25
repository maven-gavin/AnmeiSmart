import { apiClient } from './apiClient';
import { Permission, Role, Tenant, UserPermissionSummary } from '@/types/auth';
import { Resource } from './resourceService';

class PermissionService {
  private baseUrl = '/permissions';

  // ==================== 权限管理 ====================

  /**
   * 获取所有权限列表（全局，不区分租户）
   */
  async getPermissions(): Promise<Permission[]> {
    const response = await apiClient.get<{ permissions: Permission[] }>(`${this.baseUrl}`);
    // 后端返回的是 ApiResponse[PermissionListResponse]，需要提取 permissions 字段
    return response.data?.permissions || [];
  }

  /**
   * 获取权限详情
   */
  async getPermission(permissionId: string): Promise<Permission> {
    const response = await apiClient.get<Permission>(`${this.baseUrl}/${permissionId}`);
    return response.data;
  }

  /**
   * 创建权限
   */
  async createPermission(permission: Partial<Permission>): Promise<Permission> {
    const response = await apiClient.post<Permission>(`${this.baseUrl}`, permission);
    return response.data;
  }

  /**
   * 更新权限
   */
  async updatePermission(permissionId: string, permission: Partial<Permission>): Promise<Permission> {
    const response = await apiClient.put<Permission>(`${this.baseUrl}/${permissionId}`, permission);
    return response.data;
  }

  /**
   * 删除权限
   */
  async deletePermission(permissionId: string): Promise<void> {
    await apiClient.delete<void>(`${this.baseUrl}/${permissionId}`);
  }

  /**
   * 获取权限已分配的资源
   */
  async getPermissionResources(permissionId: string): Promise<Resource[]> {
    const response = await apiClient.get<Resource[]>(`${this.baseUrl}/${permissionId}/resources`);
    return response.data ?? [];
  }

  /**
   * 为权限分配资源
   */
  async assignResourcesToPermission(permissionId: string, resourceIds: string[]): Promise<void> {
    // 直接传递数组，normalizeBodyOptions 会将其包装在 body 中
    // 然后 base 函数会使用 json: body 将其序列化为 JSON
    await apiClient.post<void>(`${this.baseUrl}/${permissionId}/resources/assign`, resourceIds);
  }

  /**
   * 从权限移除资源
   */
  async unassignResourcesFromPermission(permissionId: string, resourceIds: string[]): Promise<void> {
    // 直接传递数组，normalizeBodyOptions 会将其包装在 body 中
    // 然后 base 函数会使用 json: body 将其序列化为 JSON
    await apiClient.post<void>(`${this.baseUrl}/${permissionId}/resources/unassign`, resourceIds);
  }

  // ==================== 角色管理 ====================

  /**
   * 获取所有角色列表
   * 
   * @param search - 搜索关键词（可选）
   * @param tenantId - 租户ID（可选，仅系统管理员可指定查看其他租户的角色）
   * 
   * 注意：普通用户不需要传递tenantId，后端会自动从当前登录用户获取租户信息
   */
  async getRoles(search?: string, tenantId?: string): Promise<Role[]> {
    const params: Record<string, string> = {};
    if (search) {
      params.search = search;
    }
    // tenantId 仅用于系统管理员查看其他租户的数据
    // 普通用户不传此参数，后端会自动从当前用户获取
    if (tenantId) {
      params.tenant_id = tenantId;
    }
    const response = await apiClient.get<Role[]>('/roles', { params });
    return response.data ?? [];
  }

  /**
   * 获取角色详情
   */
  async getRole(roleId: string): Promise<Role> {
    const response = await apiClient.get<Role>(`/roles/${roleId}`);
    return response.data as Role;
  }

  /**
   * 创建角色
   */
  async createRole(role: Partial<Role>): Promise<Role> {
    const response = await apiClient.post<Role>('/roles', role);
    return response.data as Role;
  }

  /**
   * 更新角色
   */
  async updateRole(roleId: string, role: Partial<Role>): Promise<Role> {
    const response = await apiClient.put<Role>(`/roles/${roleId}`, role);
    return response.data as Role;
  }

  /**
   * 删除角色
   */
  async deleteRole(roleId: string): Promise<boolean> {
    const response = await apiClient.delete<boolean>(`/roles/${roleId}`);
    return Boolean(response.data);
  }

  // ==================== 角色权限关联 ====================

  /**
   * 为角色分配权限
   */
  async assignPermissionToRole(roleId: string, permissionId: string): Promise<void> {
    await apiClient.post<void>(`/roles/${roleId}/permissions`, { permission_id: permissionId });
  }

  /**
   * 从角色移除权限
   */
  async removePermissionFromRole(roleId: string, permissionId: string): Promise<void> {
    await apiClient.delete<void>(`/roles/${roleId}/permissions/${permissionId}`);
  }

  /**
   * 获取角色的权限列表
   */
  async getRolePermissions(roleId: string): Promise<Permission[]> {
    const response = await apiClient.get<Permission[]>(`/roles/${roleId}/permissions`);
    return response.data;
  }

  /**
   * 获取拥有指定权限的角色列表
   */
  async getPermissionRoles(permissionId: string): Promise<Role[]> {
    const response = await apiClient.get<Role[]>(`${this.baseUrl}/${permissionId}/roles`);
    return response.data;
  }

  // ==================== 租户管理 ====================

  /**
   * 获取所有租户列表
   */
  async getTenants(status?: string): Promise<Tenant[]> {
    const params = status ? { status } : {};
    const response = await apiClient.get<{ tenants: Tenant[] }>('/tenants', { params });
    // 后端返回的是 TenantListResponse，需要提取 tenants 字段
    return response.data?.tenants || [];
  }

  /**
   * 获取租户详情
   */
  async getTenant(tenantId: string): Promise<Tenant> {
    const response = await apiClient.get<Tenant>(`/tenants/${tenantId}`);
    return response.data;
  }

  /**
   * 创建租户
   */
  async createTenant(tenant: Partial<Tenant>): Promise<Tenant> {
    const response = await apiClient.post<Tenant>('/tenants', tenant);
    return response.data;
  }

  /**
   * 更新租户
   */
  async updateTenant(tenantId: string, tenant: Partial<Tenant>): Promise<Tenant> {
    const response = await apiClient.put<Tenant>(`/tenants/${tenantId}`, tenant);
    return response.data;
  }

  /**
   * 删除租户
   */
  async deleteTenant(tenantId: string): Promise<void> {
    await apiClient.delete<void>(`/tenants/${tenantId}`);
  }

  /**
   * 激活租户
   */
  async activateTenant(tenantId: string): Promise<void> {
    await apiClient.post<void>(`/tenants/${tenantId}/activate`);
  }

  /**
   * 停用租户
   */
  async deactivateTenant(tenantId: string): Promise<void> {
    await apiClient.post<void>(`/tenants/${tenantId}/deactivate`);
  }

  /**
   * 获取租户统计信息
   */
  async getTenantStatistics(tenantId: string): Promise<any> {
    const response = await apiClient.get<any>(`/tenants/${tenantId}/statistics`);
    return response.data;
  }

  // ==================== 用户权限检查 ====================

  /**
   * 检查用户权限
   */
  async checkUserPermission(userId: string, permission: string): Promise<boolean> {
    const response = await apiClient.get<any>(`/users/${userId}/permissions/check`, {
      params: { permission }
    });
    return response.data.has_permission;
  }

  /**
   * 检查用户角色
   */
  async checkUserRole(userId: string, role: string): Promise<boolean> {
    const response = await apiClient.get<any>(`/users/${userId}/roles/check`, {
      params: { role }
    });
    return response.data.has_role;
  }

  /**
   * 获取用户权限列表
   */
  async getUserPermissions(userId: string): Promise<string[]> {
    const response = await apiClient.get<any>(`/users/${userId}/permissions`);
    return response.data.permissions;
  }

  /**
   * 获取用户角色列表
   */
  async getUserRoles(userId: string): Promise<string[]> {
    const response = await apiClient.get<any>(`/users/${userId}/roles`);
    return response.data.roles;
  }

  /**
   * 检查用户是否为管理员
   */
  async isUserAdmin(userId: string): Promise<boolean> {
    const response = await apiClient.get<any>(`/users/${userId}/admin/check`);
    return response.data.is_admin;
  }

  /**
   * 获取用户权限摘要
   */
  async getUserPermissionSummary(userId: string): Promise<UserPermissionSummary> {
    const response = await apiClient.get<UserPermissionSummary>(`/users/${userId}/permissions/summary`);
    return response.data;
  }
}

export const permissionService = new PermissionService();
