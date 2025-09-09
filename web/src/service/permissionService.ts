import { apiClient } from './apiClient';
import { Permission, Role, Tenant, UserPermissionSummary } from '@/types/auth';

class PermissionService {
  private baseUrl = '/api/v1/permissions';

  // ==================== 权限管理 ====================

  /**
   * 获取所有权限列表
   */
  async getPermissions(tenantId?: string): Promise<Permission[]> {
    const params = tenantId ? { tenant_id: tenantId } : {};
    const response = await apiClient.get(`${this.baseUrl}`, { params });
    return response.data;
  }

  /**
   * 获取权限详情
   */
  async getPermission(permissionId: string): Promise<Permission> {
    const response = await apiClient.get(`${this.baseUrl}/${permissionId}`);
    return response.data;
  }

  /**
   * 创建权限
   */
  async createPermission(permission: Partial<Permission>): Promise<Permission> {
    const response = await apiClient.post(`${this.baseUrl}`, permission);
    return response.data;
  }

  /**
   * 更新权限
   */
  async updatePermission(permissionId: string, permission: Partial<Permission>): Promise<Permission> {
    const response = await apiClient.put(`${this.baseUrl}/${permissionId}`, permission);
    return response.data;
  }

  /**
   * 删除权限
   */
  async deletePermission(permissionId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${permissionId}`);
  }

  // ==================== 角色管理 ====================

  /**
   * 获取所有角色列表
   */
  async getRoles(tenantId?: string): Promise<Role[]> {
    const params = tenantId ? { tenant_id: tenantId } : {};
    const response = await apiClient.get('/api/v1/roles', { params });
    return response.data;
  }

  /**
   * 获取角色详情
   */
  async getRole(roleId: string): Promise<Role> {
    const response = await apiClient.get(`/api/v1/roles/${roleId}`);
    return response.data;
  }

  /**
   * 创建角色
   */
  async createRole(role: Partial<Role>): Promise<Role> {
    const response = await apiClient.post('/api/v1/roles', role);
    return response.data;
  }

  /**
   * 更新角色
   */
  async updateRole(roleId: string, role: Partial<Role>): Promise<Role> {
    const response = await apiClient.put(`/api/v1/roles/${roleId}`, role);
    return response.data;
  }

  /**
   * 删除角色
   */
  async deleteRole(roleId: string): Promise<void> {
    await apiClient.delete(`/api/v1/roles/${roleId}`);
  }

  // ==================== 角色权限关联 ====================

  /**
   * 为角色分配权限
   */
  async assignPermissionToRole(roleId: string, permissionId: string): Promise<void> {
    await apiClient.post(`/api/v1/roles/${roleId}/permissions`, { permission_id: permissionId });
  }

  /**
   * 从角色移除权限
   */
  async removePermissionFromRole(roleId: string, permissionId: string): Promise<void> {
    await apiClient.delete(`/api/v1/roles/${roleId}/permissions/${permissionId}`);
  }

  /**
   * 获取角色的权限列表
   */
  async getRolePermissions(roleId: string): Promise<Permission[]> {
    const response = await apiClient.get(`/api/v1/roles/${roleId}/permissions`);
    return response.data;
  }

  /**
   * 获取拥有指定权限的角色列表
   */
  async getPermissionRoles(permissionId: string): Promise<Role[]> {
    const response = await apiClient.get(`${this.baseUrl}/${permissionId}/roles`);
    return response.data;
  }

  // ==================== 租户管理 ====================

  /**
   * 获取所有租户列表
   */
  async getTenants(status?: string): Promise<Tenant[]> {
    const params = status ? { status } : {};
    const response = await apiClient.get('/api/v1/tenants', { params });
    return response.data;
  }

  /**
   * 获取租户详情
   */
  async getTenant(tenantId: string): Promise<Tenant> {
    const response = await apiClient.get(`/api/v1/tenants/${tenantId}`);
    return response.data;
  }

  /**
   * 创建租户
   */
  async createTenant(tenant: Partial<Tenant>): Promise<Tenant> {
    const response = await apiClient.post('/api/v1/tenants', tenant);
    return response.data;
  }

  /**
   * 更新租户
   */
  async updateTenant(tenantId: string, tenant: Partial<Tenant>): Promise<Tenant> {
    const response = await apiClient.put(`/api/v1/tenants/${tenantId}`, tenant);
    return response.data;
  }

  /**
   * 删除租户
   */
  async deleteTenant(tenantId: string): Promise<void> {
    await apiClient.delete(`/api/v1/tenants/${tenantId}`);
  }

  /**
   * 激活租户
   */
  async activateTenant(tenantId: string): Promise<void> {
    await apiClient.post(`/api/v1/tenants/${tenantId}/activate`);
  }

  /**
   * 停用租户
   */
  async deactivateTenant(tenantId: string): Promise<void> {
    await apiClient.post(`/api/v1/tenants/${tenantId}/deactivate`);
  }

  /**
   * 获取租户统计信息
   */
  async getTenantStatistics(tenantId: string): Promise<any> {
    const response = await apiClient.get(`/api/v1/tenants/${tenantId}/statistics`);
    return response.data;
  }

  // ==================== 用户权限检查 ====================

  /**
   * 检查用户权限
   */
  async checkUserPermission(userId: string, permission: string): Promise<boolean> {
    const response = await apiClient.get(`/api/v1/users/${userId}/permissions/check`, {
      params: { permission }
    });
    return response.data.has_permission;
  }

  /**
   * 检查用户角色
   */
  async checkUserRole(userId: string, role: string): Promise<boolean> {
    const response = await apiClient.get(`/api/v1/users/${userId}/roles/check`, {
      params: { role }
    });
    return response.data.has_role;
  }

  /**
   * 获取用户权限列表
   */
  async getUserPermissions(userId: string): Promise<string[]> {
    const response = await apiClient.get(`/api/v1/users/${userId}/permissions`);
    return response.data.permissions;
  }

  /**
   * 获取用户角色列表
   */
  async getUserRoles(userId: string): Promise<string[]> {
    const response = await apiClient.get(`/api/v1/users/${userId}/roles`);
    return response.data.roles;
  }

  /**
   * 检查用户是否为管理员
   */
  async isUserAdmin(userId: string): Promise<boolean> {
    const response = await apiClient.get(`/api/v1/users/${userId}/admin/check`);
    return response.data.is_admin;
  }

  /**
   * 获取用户权限摘要
   */
  async getUserPermissionSummary(userId: string): Promise<UserPermissionSummary> {
    const response = await apiClient.get(`/api/v1/users/${userId}/permissions/summary`);
    return response.data;
  }
}

export const permissionService = new PermissionService();
