/**
 * 个人中心服务
 * 处理用户个人信息、偏好设置、默认角色、登录历史相关的API调用
 */

import { apiClient } from './apiClient';
import { ApiClientError, ErrorType } from './apiClient';

// 类型定义
export interface UserPreferences {
  user_id: string;
  notification_enabled: boolean;
  email_notification: boolean;
  push_notification: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface UserDefaultRole {
  user_id: string;
  default_role: string;
  created_at?: string;
  updated_at?: string;
}

export interface LoginHistory {
  id: string;
  user_id: string;
  ip_address?: string;
  user_agent?: string;
  login_time: string;
  login_role?: string;
  location?: string;
  created_at?: string;
  updated_at?: string;
}

export interface UserProfile {
  user_id: string;
  preferences?: UserPreferences;
  default_role_setting?: UserDefaultRole;
  recent_login_history: LoginHistory[];
}

// 更新类型
export interface UserPreferencesUpdate {
  notification_enabled?: boolean;
  email_notification?: boolean;
  push_notification?: boolean;
}

export interface UserDefaultRoleUpdate {
  default_role: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface BasicUserInfo {
  id: string;
  username: string;
  email: string;
  phone?: string;
  avatar?: string;
  is_active: boolean;
  created_at: string;
  roles: string[];
  active_role?: string;
}

/**
 * 个人中心服务类
 */
class ProfileService {
  private static readonly BASE_PATH = '/profile';

  /**
   * 获取当前用户的完整个人中心信息
   */
  async getMyProfile(): Promise<UserProfile> {
    try {
      // 使用 /users/me 端点（profile 路由已被注释）
      const response = await apiClient.get<UserProfile>("/users/me");
      
      if (!response.data) {
        throw new ApiClientError('获取个人信息失败', {
          status: 500,
          type: ErrorType.NETWORK,
        })
      }
      
      return response.data;
    } catch (error) {
      console.error('获取个人中心信息失败:', error);
      throw this.handleError(error, '获取个人信息失败');
    }
  }

  /**
   * 获取当前用户的偏好设置
   */
  async getMyPreferences(): Promise<UserPreferences> {
    try {
      // 使用 /users/me/preferences 端点（profile 路由已被注释）
      const response = await apiClient.get<UserPreferences>("/users/me/preferences");
      
      if (!response.data) {
        throw new ApiClientError('获取偏好设置失败', {
          status: 500,
          type: ErrorType.NETWORK,
        })
      }
      
      return response.data;
    } catch (error) {
      console.error('获取偏好设置失败:', error);
      throw this.handleError(error, '获取偏好设置失败');
    }
  }

  /**
   * 更新当前用户的偏好设置
   */
  async updateMyPreferences(preferences: UserPreferencesUpdate): Promise<UserPreferences> {
    try {
      // 使用 /users/me/preferences 端点（profile 路由已被注释）
      const response = await apiClient.put<UserPreferences>(
        "/users/me/preferences", 
        preferences
      );
      
      if (!response.data) {
        throw new ApiClientError('更新偏好设置失败', {
          status: 500,
          type: ErrorType.NETWORK,
        })
      }
      
      return response.data;
    } catch (error) {
      console.error('更新偏好设置失败:', error);
      throw this.handleError(error, '更新偏好设置失败');
    }
  }

  /**
   * 获取当前用户的默认角色设置
   */
  async getMyDefaultRole(): Promise<UserDefaultRole | null> {
    try {
      // 使用 /users/me/default-role 端点（profile 路由已被注释）
      const response = await apiClient.get<UserDefaultRole>("/users/me/default-role");
      return response.data || null;
    } catch (error) {
      if (error instanceof ApiClientError && error.status === 404) {
        return null; // 用户还没有设置默认角色
      }
      console.error('获取默认角色失败:', error);
      throw this.handleError(error, '获取默认角色失败');
    }
  }

  /**
   * 设置当前用户的默认角色
   */
  async setMyDefaultRole(defaultRole: UserDefaultRoleUpdate): Promise<UserDefaultRole> {
    try {
      // 使用 /users/me/default-role 端点（profile 路由已被注释）
      const response = await apiClient.put<UserDefaultRole>(
        "/users/me/default-role", 
        defaultRole
      );
      
      if (!response.data) {
        throw new ApiClientError('设置默认角色失败', {
          status: 500,
          type: ErrorType.NETWORK,
        })
      }
      
      return response.data;
    } catch (error) {
      console.error('设置默认角色失败:', error);
      throw this.handleError(error, '设置默认角色失败');
    }
  }

  /**
   * 获取当前用户的登录历史
   */
  async getMyLoginHistory(limit: number = 10): Promise<LoginHistory[]> {
    try {
      // 使用 /users/me/login-history 端点（profile 路由已被注释）
      const response = await apiClient.get<LoginHistory[]>(
        `/users/me/login-history?limit=${limit}`
      );
      
      return response.data || [];
    } catch (error) {
      console.error('获取登录历史失败:', error);
      throw this.handleError(error, '获取登录历史失败');
    }
  }

  /**
   * 创建登录历史记录
   */
  async createLoginRecord(loginRole?: string): Promise<LoginHistory> {
    try {
      // 使用 /users/me/login-history 端点（profile 路由已被注释）
      const response = await apiClient.post<LoginHistory>(
        "/users/me/login-history",
        { login_role: loginRole }
      );
      
      if (!response.data) {
        throw new ApiClientError('创建登录记录失败', {
          status: 500,
          type: ErrorType.NETWORK,
        })
      }
      
      return response.data;
    } catch (error) {
      console.error('创建登录记录失败:', error);
      throw this.handleError(error, '创建登录记录失败');
    }
  }

  /**
   * 检查是否应该应用默认角色（首次登录逻辑）
   * 注意：此功能可能需要根据业务逻辑实现，暂时返回 false
   */
  async shouldApplyDefaultRole(): Promise<{ should_apply: boolean; default_role?: string }> {
    try {
      // profile 路由已被注释，此功能暂时返回 false
      // 如果需要实现，可以在后端添加 /users/me/should-apply-default-role 端点
      return { should_apply: false };
    } catch (error) {
      console.error('检查默认角色应用失败:', error);
      return { should_apply: false };
    }
  }

  /**
   * 获取当前用户的基本信息（复用auth/me接口）
   */
  async getMyBasicInfo(): Promise<BasicUserInfo> {
    try {
      // 后端返回的是 UserResponse，需要映射到 BasicUserInfo
      const response = await apiClient.get<any>('/auth/me');
      
      if (!response.data) {
        throw new ApiClientError('获取用户基本信息失败', {
          status: 500,
          type: ErrorType.NETWORK,
        })
      }
      
      const userData = response.data;
      
      // 调试日志
      console.log('[getMyBasicInfo] 后端返回的原始数据:', userData);
      console.log('[getMyBasicInfo] is_active:', userData.is_active, typeof userData.is_active);
      console.log('[getMyBasicInfo] isActive:', userData.isActive, typeof userData.isActive);
      console.log('[getMyBasicInfo] active_role:', userData.active_role);
      console.log('[getMyBasicInfo] activeRole:', userData.activeRole);
      console.log('[getMyBasicInfo] created_at:', userData.created_at);
      console.log('[getMyBasicInfo] createdAt:', userData.createdAt);
      
      // 映射数据，支持驼峰和下划线两种格式
      const basicInfo: BasicUserInfo = {
        id: userData.id || '',
        username: userData.username || '',
        email: userData.email || '',
        phone: userData.phone || undefined,
        avatar: userData.avatar || undefined,
        is_active: userData.is_active ?? userData.isActive ?? true,
        created_at: userData.created_at || userData.createdAt || '',
        roles: userData.roles || [],
        active_role: userData.active_role || userData.activeRole || undefined
      };
      
      console.log('[getMyBasicInfo] 映射后的数据:', basicInfo);
      
      return basicInfo;
    } catch (error) {
      console.error('获取用户基本信息失败:', error);
      throw this.handleError(error, '获取用户基本信息失败');
    }
  }

  /**
   * 更新当前用户的基本信息（复用users/me接口）
   */
  async updateMyBasicInfo(userInfo: Partial<BasicUserInfo>): Promise<BasicUserInfo> {
    try {
      const response = await apiClient.put<BasicUserInfo>('/users/me', userInfo);
      
      if (!response.data) {
        throw new ApiClientError('更新用户基本信息失败', {
          status: 500,
          type: ErrorType.NETWORK,
        })
      }
      
      return response.data;
    } catch (error) {
      console.error('更新用户基本信息失败:', error);
      throw this.handleError(error, '更新用户基本信息失败');
    }
  }

  /**
   * 修改当前用户的密码
   */
  async changePassword(passwordData: ChangePasswordRequest): Promise<{ success: boolean; message: string }> {
    try {
      // 使用 /users/me/change-password 端点（profile 路由已被注释）
      const response = await apiClient.post<{ success: boolean; message: string }>(
        "/users/me/change-password",
        passwordData
      );
      
      if (!response.data) {
        throw new ApiClientError('修改密码失败', {
          status: 500,
          type: ErrorType.NETWORK,
        })
      }
      
      return response.data;
    } catch (error) {
      console.error('修改密码失败:', error);
      throw this.handleError(error, '修改密码失败');
    }
  }

  /**
   * 错误处理辅助方法
   */
  private handleError(error: unknown, defaultMessage: string): ApiClientError {
    if (error instanceof ApiClientError) {
      return error;
    }
    
    if (error instanceof Error) {
      return new ApiClientError(defaultMessage, {
        status: 500,
        type: ErrorType.NETWORK,
        responseData: error.message,
      })
    }
    
    return new ApiClientError(defaultMessage, {
      status: 500,
      type: ErrorType.UNKNOWN,
    })
  }
}

// 导出服务实例
export const profileService = new ProfileService(); 