/**
 * 个人中心服务
 * 处理用户个人信息、偏好设置、默认角色、登录历史相关的API调用
 */

import { apiClient } from './apiClient';
import { AppError, ErrorType } from './errors';

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
      const response = await apiClient.get<UserProfile>(`${ProfileService.BASE_PATH}/me`);
      
      if (!response.data) {
        throw new AppError(ErrorType.NETWORK, 500, '获取个人信息失败');
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
      const response = await apiClient.get<UserPreferences>(`${ProfileService.BASE_PATH}/preferences`);
      
      if (!response.data) {
        throw new AppError(ErrorType.NETWORK, 500, '获取偏好设置失败');
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
      const response = await apiClient.put<UserPreferences>(
        `${ProfileService.BASE_PATH}/preferences`, 
        preferences
      );
      
      if (!response.data) {
        throw new AppError(ErrorType.NETWORK, 500, '更新偏好设置失败');
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
      const response = await apiClient.get<UserDefaultRole>(`${ProfileService.BASE_PATH}/default-role`);
      return response.data || null;
    } catch (error) {
      if (error instanceof AppError && error.status === 404) {
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
      const response = await apiClient.put<UserDefaultRole>(
        `${ProfileService.BASE_PATH}/default-role`, 
        defaultRole
      );
      
      if (!response.data) {
        throw new AppError(ErrorType.NETWORK, 500, '设置默认角色失败');
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
      const response = await apiClient.get<LoginHistory[]>(
        `${ProfileService.BASE_PATH}/login-history?limit=${limit}`
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
      const response = await apiClient.post<LoginHistory>(
        `${ProfileService.BASE_PATH}/login-history`,
        { login_role: loginRole }
      );
      
      if (!response.data) {
        throw new AppError(ErrorType.NETWORK, 500, '创建登录记录失败');
      }
      
      return response.data;
    } catch (error) {
      console.error('创建登录记录失败:', error);
      throw this.handleError(error, '创建登录记录失败');
    }
  }

  /**
   * 检查是否应该应用默认角色（首次登录逻辑）
   */
  async shouldApplyDefaultRole(): Promise<{ should_apply: boolean; default_role?: string }> {
    try {
      const response = await apiClient.get<{ should_apply: boolean; default_role?: string }>(
        `${ProfileService.BASE_PATH}/should-apply-default-role`
      );
      
      return response.data || { should_apply: false };
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
      const response = await apiClient.get<BasicUserInfo>('/auth/me');
      
      if (!response.data) {
        throw new AppError(ErrorType.NETWORK, 500, '获取用户基本信息失败');
      }
      
      return response.data;
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
        throw new AppError(ErrorType.NETWORK, 500, '更新用户基本信息失败');
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
      const response = await apiClient.post<{ success: boolean; message: string }>(
        `${ProfileService.BASE_PATH}/change-password`,
        passwordData
      );
      
      if (!response.data) {
        throw new AppError(ErrorType.NETWORK, 500, '修改密码失败');
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
  private handleError(error: unknown, defaultMessage: string): AppError {
    if (error instanceof AppError) {
      return error;
    }
    
    if (error instanceof Error) {
      return new AppError(ErrorType.NETWORK, 500, defaultMessage, error.message);
    }
    
    return new AppError(ErrorType.UNKNOWN, 500, defaultMessage);
  }
}

// 导出服务实例
export const profileService = new ProfileService(); 