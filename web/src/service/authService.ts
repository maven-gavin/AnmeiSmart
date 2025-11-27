/**
 * 身份验证服务
 * 专注于用户身份验证、角色管理和会话控制
 */

import type { AuthUser, LoginCredentials, UserRole, UserPermissionSummary, Role } from '@/types/auth';
import { tokenManager } from './tokenManager';
import { ApiClientError, ErrorType, apiClient } from './apiClient';
import { AUTH_CONFIG } from '@/config';
import { ContentType } from './fetch';

type PermissionSummaryResponse = UserPermissionSummary;
type PermissionCheckResponse = { has_permission: boolean };
type RoleCheckResponse = { has_role: boolean };
type AdminCheckResponse = { is_admin: boolean };
type UserPermissionsResponse = { permissions: string[] };
type UserRolesResponse = { roles: string[] };
type UserRoleDetailsResponse = Role[];
type UserProfileResponse = {
  id: string | number;
  username: string;
  email?: string;
  roles?: string[];
  activeRole?: string;
};

const isBrowser = typeof window !== 'undefined';

/**
 * 安全的用户存储工具
 */
const userStorage = {
  getUser(): AuthUser | null {
    if (!isBrowser) return null;
    
    try {
      const userStr = localStorage.getItem(AUTH_CONFIG.USER_STORAGE_KEY);
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('用户信息解析失败:', error);
      return null;
    }
  },

  setUser(user: AuthUser): boolean {
    if (!isBrowser) return false;
    
    try {
      localStorage.setItem(AUTH_CONFIG.USER_STORAGE_KEY, JSON.stringify(user));
      return true;
    } catch (error) {
      console.error('用户信息存储失败:', error);
      return false;
    }
  },

  removeUser(): boolean {
    if (!isBrowser) return false;
    
    try {
      localStorage.removeItem(AUTH_CONFIG.USER_STORAGE_KEY);
      return true;
    } catch {
      return false;
    }
  }
};

const normalizeRole = (role?: string): UserRole | undefined => {
  if (!role) {
    return undefined;
  }
  return (role === 'administrator' ? 'admin' : role) as UserRole;
};

const normalizeRoles = (roles?: string[]): UserRole[] => {
  if (!roles || roles.length === 0) {
    return [];
  }
  return roles
    .map((role) => normalizeRole(role))
    .filter((role): role is UserRole => Boolean(role));
};



/**
 * 身份验证服务类
 */
class AuthService {
  /**
   * 用户登录
   */
  async login(credentials: LoginCredentials): Promise<{ user: AuthUser; token: string }> {
    try {
      const formData = new URLSearchParams({
        username: credentials.username,
        password: credentials.password,
      });
      // Safari 浏览器需要显式转换为字符串，确保特殊字符（如 @）被正确编码
      const formDataString = formData.toString();

      const params: Record<string, string> = {};
      if (credentials.tenantId) {
        params.tenant_id = credentials.tenantId;
      }

      const response = await apiClient.post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
      }>(
        '/auth/login',
        {
          body: formDataString,
          headers: new Headers({ 'Content-Type': ContentType.form }),
          params,
        },
        {
          bodyStringify: false,
        }
      );

      const tokenData = response.data;
      if (!tokenData?.access_token || !tokenData?.refresh_token) {
        throw new ApiClientError('服务器未返回访问令牌', {
          status: 500,
          type: ErrorType.AUTHENTICATION,
        });
      }

      tokenManager.setTokens(tokenData.access_token, tokenData.refresh_token);

      const userResponse = await apiClient.get<UserProfileResponse>('/auth/me');

      const authUser: AuthUser = {
        id: userResponse.data.id.toString(),
        name: userResponse.data.username,
        email: userResponse.data.email,
        roles: normalizeRoles(userResponse.data.roles),
        currentRole: normalizeRole(userResponse.data.activeRole),
      };

      userStorage.setUser(authUser);

      // 异步获取用户权限（不阻塞登录流程）
      this.refreshUserPermissions().catch(err => {
        console.warn('获取用户权限失败（不影响登录）:', err);
      });

      return { user: authUser, token: tokenData.access_token };
    } catch (error) {
      if (error instanceof ApiClientError) {
        throw error;
      }

      throw new ApiClientError('登录失败，请稍后重试', {
        status: 500,
        type: ErrorType.AUTHENTICATION,
        responseData: error instanceof Error ? error.message : String(error),
      });
    }
  }

  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    // 清除存储的数据
    tokenManager.clearTokens();
    userStorage.removeUser();
  }

  /**
   * 用户注册
   */
  async register(registerData: {
    phone: string;
    username: string;
    email: string;
    password: string;
  }): Promise<{ user: AuthUser; token: string }> {
    try {
      // 调用注册接口
      const response = await apiClient.post<UserProfileResponse>('/auth/register', {
        body: {
          email: registerData.email,
          username: registerData.username,
          phone: registerData.phone,
          password: registerData.password,
          roles: ['customer'] // 默认注册为客户角色
        }
      });

      if (!response.data) {
        throw new ApiClientError('注册失败，服务器无响应', {
          status: 500,
          type: ErrorType.AUTHENTICATION,
        })
      }

      // 注册成功后自动登录
      const loginResult = await this.login({
        username: registerData.email, // 使用邮箱登录
        password: registerData.password
      });

      return loginResult;
    } catch (error) {
      if (error instanceof ApiClientError) {
        throw error;
      }
      
      throw new ApiClientError('注册失败，请稍后重试', {
        status: 500,
        type: ErrorType.AUTHENTICATION,
        responseData: error instanceof Error ? error.message : String(error),
      })
    }
  }

  /**
   * 获取当前登录用户
   */
  getCurrentUser(): AuthUser | null {
    return userStorage.getUser();
  }

  /**
   * 获取当前用户ID
   */
  getCurrentUserId(): string | null {
    const user = this.getCurrentUser();
    return user?.id || null;
  }

  /**
   * 获取当前用户角色
   */
  getCurrentUserRole(): UserRole | null {
    const user = this.getCurrentUser();
    return user?.currentRole || null;
  }

  /**
   * 切换用户角色
   */
  async switchRole(role: UserRole): Promise<AuthUser> {
    const currentUser = this.getCurrentUser();
    
    if (!currentUser) {
      throw new ApiClientError('用户未登录', {
        status: 401,
        type: ErrorType.AUTHENTICATION,
      })
    }
    
    if (!currentUser.roles.includes(role)) {
      throw new ApiClientError('用户没有该角色权限', {
        status: 403,
        type: ErrorType.AUTHORIZATION,
      })
    }
    
    try {
      // 调用后端API切换角色并获取新令牌对 - 使用统一的apiClient
      // 将前端的 'admin' 角色映射为后端的 'administrator'
      const backendRole = role === 'admin' ? 'administrator' : role;
      const response = await apiClient.post<{ access_token: string; refresh_token: string; token_type: string }>('/auth/switch-role', {
        body: { role: backendRole }
      });
      
      if (!response.data) {
        throw new ApiClientError('角色切换失败，服务器无响应', {
          status: 500,
          type: ErrorType.AUTHORIZATION,
        })
      }
      
      // 更新令牌对
      tokenManager.setTokens(response.data.access_token, response.data.refresh_token);
      
      // 更新用户信息
      const updatedUser: AuthUser = {
        ...currentUser,
        currentRole: role,
      };
      
      userStorage.setUser(updatedUser);
      return updatedUser;
    } catch (error) {
      // 改进错误处理，正确提取Response对象的错误信息
      let errorMessage = '角色切换失败，请稍后重试';
      
      if (error instanceof Response) {
        try {
          const errorData = await error.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          errorMessage = `HTTP ${error.status}: ${error.statusText}`;
        }
      } else if (error instanceof ApiClientError) {
        throw error;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }
      
      throw new ApiClientError(errorMessage, {
        status: 500,
        type: ErrorType.AUTHORIZATION,
        responseData: error instanceof Error ? error.message : String(error),
      })
    }
  }

  /**
   * 检查是否已登录
   */
  isLoggedIn(): boolean {
    const token = tokenManager.getToken();
    const user = this.getCurrentUser();
    
    return !!(token && user && !tokenManager.isTokenExpired());
  }

  /**
   * 获取有效令牌
   */
  async getValidToken(): Promise<string | null> {
    return tokenManager.getValidToken();
  }

  /**
   * 检查令牌是否过期
   */
  isTokenExpired(token?: string): boolean {
    return tokenManager.isTokenExpired(token);
  }

  /**
   * 刷新令牌
   */
  async refreshToken(): Promise<string> {
    return tokenManager.refreshToken();
  }

  /**
   * 处理未授权情况
   */
  handleUnauthorized(): void {
    this.logout();
    if (typeof window !== 'undefined') {
      const currentPath = window.location.pathname;
      const returnUrl = encodeURIComponent(currentPath);
      const errorMsg = encodeURIComponent('会话已过期，请重新登录');
      window.location.href = `/login?returnUrl=${returnUrl}&error=${errorMsg}`;
    }
  }

  /**
   * 检查当前登录用户是否具有特定角色（本地缓存）
   */
  hasRole(role: UserRole): boolean {
    const user = this.getCurrentUser();
    return user?.roles.includes(role) || false;
  }

  /**
   * 检查用户是否具有任一角色
   */
  hasAnyRole(roles: UserRole[]): boolean {
    return roles.some(role => this.hasRole(role));
  }

  /**
   * 获取当前用户所有角色
   */
  async getRoles(): Promise<string[]> {
    try {
      // 使用 /auth/roles/details 端点获取角色详情，然后提取角色名称列表
      const response = await apiClient.get<UserRoleDetailsResponse>("/auth/roles/details");
      const roles = response.data || [];
      return roles.map(role => role.name);
    } catch (error) {
      console.error('获取用户角色失败:', error);
      return [];
    }
  }

  // ==================== 权限相关方法 ====================

  /**
   * 获取用户权限摘要
   */
  async getUserPermissionSummary(userId?: string): Promise<UserPermissionSummary | null> {
    try {
      const targetUserId = userId || this.getCurrentUser()?.id;
      if (!targetUserId) {
        return null;
      }

      const response = await apiClient.get<PermissionSummaryResponse>(`/users/${targetUserId}/permissions/summary`);
      return response.data ?? null;
    } catch (error) {
      console.error('获取用户权限摘要失败:', error);
      return null;
    }
  }

  /**
   * 检查用户是否有指定权限
   */
  async hasPermission(permission: string, userId?: string): Promise<boolean> {
    try {
      const targetUserId = userId || this.getCurrentUser()?.id;
      if (!targetUserId) {
        return false;
      }

      const response = await apiClient.get<PermissionCheckResponse>(`/users/${targetUserId}/permissions/check`, {
        params: { permission }
      });
      return Boolean(response.data?.has_permission);
    } catch (error) {
      console.error('权限检查失败:', error);
      return false;
    }
  }

  /**
   * 远程检查用户是否具备指定角色
   */
  async checkUserRole(role: string, userId?: string): Promise<boolean> {
    try {
      const targetUserId = userId || this.getCurrentUser()?.id;
      if (!targetUserId) {
        return false;
      }

      const response = await apiClient.get<RoleCheckResponse>(`/users/${targetUserId}/roles/check`, {
        params: { role }
      });
      return Boolean(response.data?.has_role);
    } catch (error) {
      console.error('角色检查失败:', error);
      return false;
    }
  }

  /**
   * 检查用户是否为管理员
   */
  async isAdmin(userId?: string): Promise<boolean> {
    try {
      const targetUserId = userId || this.getCurrentUser()?.id;
      if (!targetUserId) {
        return false;
      }

      const response = await apiClient.get<AdminCheckResponse>(`/users/${targetUserId}/admin/check`);
      return Boolean(response.data?.is_admin);
    } catch (error) {
      console.error('管理员权限检查失败:', error);
      return false;
    }
  }

  /**
   * 获取用户权限列表
   */
  async getUserPermissions(userId?: string): Promise<string[]> {
    try {
      const targetUserId = userId || this.getCurrentUser()?.id;
      if (!targetUserId) {
        return [];
      }

      const response = await apiClient.get<UserPermissionsResponse>(`/users/${targetUserId}/permissions`);
      return response.data?.permissions ?? [];
    } catch (error) {
      console.error('获取用户权限列表失败:', error);
      return [];
    }
  }

  /**
   * 获取用户角色列表
   */
  async getUserRoles(userId?: string): Promise<string[]> {
    try {
      const targetUserId = userId || this.getCurrentUser()?.id;
      if (!targetUserId) {
        return [];
      }

      const response = await apiClient.get<UserRolesResponse>(`/users/${targetUserId}/roles`);
      return response.data?.roles ?? [];
    } catch (error) {
      console.error('获取用户角色列表失败:', error);
      return [];
    }
  }

  /**
   * 获取当前用户角色详情列表
   */
  async getRoleDetails(): Promise<Role[]> {
    try {
      const response = await apiClient.get<UserRoleDetailsResponse>("/auth/roles/details");
      return response.data || [];
    } catch (error) {
      console.error('获取用户角色详情失败:', error);
      return [];
    }
  }

  /**
   * 刷新用户权限信息
   */
  async refreshUserPermissions(): Promise<AuthUser | null> {
    try {
      const currentUser = this.getCurrentUser();
      if (!currentUser) {
        return null;
      }

      const permissionSummary = await this.getUserPermissionSummary();
      if (permissionSummary) {
        // 保留原始角色信息（可能包含administrator），同时normalize用于显示
        const originalRoles = permissionSummary.roles || [];
        const normalizedRoles = normalizeRoles(originalRoles);
        
        const updatedUser: AuthUser = {
          ...currentUser,
          roles: normalizedRoles, // 使用normalized后的角色用于显示
          permissions: permissionSummary.permissions,
          isAdmin: permissionSummary.isAdmin, // 优先使用API返回的isAdmin字段
          tenantId: permissionSummary.tenantId
        };

        userStorage.setUser(updatedUser);
        return updatedUser;
      }

      return currentUser;
    } catch (error) {
      console.error('刷新用户权限信息失败:', error);
      return this.getCurrentUser();
    }
  }
}

// 导出单例实例
export const authService = new AuthService();

/**
 * 角色配置选项
 */
export const roleOptions = [
  {
    id: 'consultant' as UserRole,
    name: '顾问端',
    path: '/consultant',
    icon: 'chat',
  },
  {
    id: 'doctor' as UserRole,
    name: '医生端',
    path: '/doctor',
    icon: 'hospital',
  },
  {
    id: 'operator' as UserRole,
    name: '运营端',
    path: '/operator',
    icon: 'chart',
  },
  {
    id: 'customer' as UserRole,
    name: '客户端',
    path: '/customer',
    icon: 'user',
  },
  {
    id: 'admin' as UserRole,
    name: '管理员端',
    path: '/admin',
    icon: 'user',
  },
] as const;