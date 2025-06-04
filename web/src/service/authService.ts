/**
 * 身份验证服务
 * 专注于用户身份验证、角色管理和会话控制
 */

import { AuthUser, LoginCredentials, UserRole } from '@/types/auth';
import { tokenManager } from './tokenManager';
import { AppError, ErrorType, errorHandler } from './errors';
// 移除未使用的导入
// import { mockUsers } from './mockData';

// 检查是否在浏览器环境中运行
const isBrowser = typeof window !== 'undefined';

// API基础URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

// 用户存储键
const USER_STORAGE_KEY = 'auth_user';

/**
 * 安全的用户存储工具
 */
const userStorage = {
  getUser(): AuthUser | null {
    if (!isBrowser) return null;
    
    try {
      const userStr = localStorage.getItem(USER_STORAGE_KEY);
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('用户信息解析失败:', error);
      return null;
    }
  },

  setUser(user: AuthUser): boolean {
    if (!isBrowser) return false;
    
    try {
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
      return true;
    } catch (error) {
      console.error('用户信息存储失败:', error);
      return false;
    }
  },

  removeUser(): boolean {
    if (!isBrowser) return false;
    
    try {
      localStorage.removeItem(USER_STORAGE_KEY);
      return true;
    } catch {
      return false;
    }
  }
};

/**
 * API 请求工具
 */
const apiRequest = {
  async post<T = unknown>(endpoint: string, data?: unknown, includeAuth = false): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    // 如果需要认证，添加令牌
    if (includeAuth) {
      const token = await tokenManager.getValidToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: data ? JSON.stringify(data) : undefined,
      });

      if (!response.ok) {
        throw await errorHandler.fromResponse(response);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof AppError) {
        throw error;
      }
      throw errorHandler.fromNetworkError(error as Error);
    }
  },

  async get<T = unknown>(endpoint: string): Promise<T> {
    const token = await tokenManager.getValidToken();
    if (!token) {
      throw new AppError(ErrorType.AUTHENTICATION, 401, '未授权访问');
    }

    const url = `${API_BASE_URL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw await errorHandler.fromResponse(response);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof AppError) {
        throw error;
      }
      throw errorHandler.fromNetworkError(error as Error);
    }
  }
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
      // 调用登录接口
      const formData = new URLSearchParams({
        username: credentials.username,
        password: credentials.password,
      });

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      if (!response.ok) {
        throw await errorHandler.fromResponse(response);
      }

      const tokenData = await response.json();
      const token = tokenData.access_token;

      if (!token) {
        throw new AppError(ErrorType.AUTHENTICATION, 500, '服务器未返回访问令牌');
      }

      // 存储令牌
      tokenManager.setToken(token);

      // 获取用户信息和角色
      const [userData, roles] = await Promise.all([
        apiRequest.get<any>('/auth/me'),
        apiRequest.get<UserRole[]>('/auth/roles')
      ]);

      // 创建用户对象
      const authUser: AuthUser = {
        id: userData.id.toString(),
        name: userData.username,
        email: userData.email,
        roles,
        currentRole: roles.length > 0 ? roles[0] : undefined,
      };

      // 存储用户信息
      userStorage.setUser(authUser);

      return { user: authUser, token };
    } catch (error) {
      console.error('登录失败:', error);
      
      if (error instanceof AppError) {
        throw error;
      }
      
      throw new AppError(
        ErrorType.AUTHENTICATION,
        500,
        '登录失败，请稍后重试',
        error instanceof Error ? error.message : String(error)
      );
    }
  }

  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    try {
      // 关闭WebSocket连接（避免循环依赖）
      if (isBrowser && 'closeWebSocketConnection' in window) {
        try {
          (window as any).closeWebSocketConnection();
        } catch (error) {
          console.warn('关闭WebSocket连接失败:', error);
        }
      }
    } catch (error) {
      console.warn('清理资源时出错:', error);
    }

    // 清除存储的数据
    tokenManager.clearTokens();
    userStorage.removeUser();
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
      throw new AppError(ErrorType.AUTHENTICATION, 401, '用户未登录');
    }
    
    if (!currentUser.roles.includes(role)) {
      throw new AppError(ErrorType.AUTHORIZATION, 403, '用户没有该角色权限');
    }
    
    const updatedUser: AuthUser = {
      ...currentUser,
      currentRole: role,
    };
    
    userStorage.setUser(updatedUser);
    return updatedUser;
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
    errorHandler.redirectToLogin('会话已过期，请重新登录');
  }

  /**
   * 检查用户是否具有特定角色
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
    name: '顾客端',
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