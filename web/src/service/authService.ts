import { AuthUser, LoginCredentials, UserRole } from '@/types/auth';
import { mockUsers } from './mockData';

// 检查是否在浏览器环境中运行
const isBrowser = typeof window !== 'undefined';

// API基础URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// 身份验证服务
export const authService = {
  // 登录
  async login(credentials: LoginCredentials): Promise<{ user: AuthUser; token: string }> {
    try {
      // 调用后端登录接口
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: credentials.username,
          password: credentials.password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '登录失败');
      }

      // 获取令牌
      const tokenData = await response.json();
      const token = tokenData.access_token;

      // 获取用户信息
      const userResponse = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!userResponse.ok) {
        throw new Error('获取用户信息失败');
      }

      const userData = await userResponse.json();

      // 获取用户角色
      const rolesResponse = await fetch(`${API_BASE_URL}/auth/roles`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!rolesResponse.ok) {
        throw new Error('获取用户角色失败');
      }

      const roles = await rolesResponse.json();

      // 转换为前端用户模型
      const authUser: AuthUser = {
        id: userData.id.toString(),
        name: userData.username,
        email: userData.email,
        roles: roles,
        currentRole: roles.length > 0 ? roles[0] : undefined,
      };

      // 存储用户信息和 token 到本地存储
      if (isBrowser) {
        localStorage.setItem('auth_user', JSON.stringify(authUser));
        localStorage.setItem('auth_token', token);
      }

      return { user: authUser, token };
    } catch (error) {
      console.error('登录失败', error);
      throw error;
    }
  },

  // 登出
  async logout(): Promise<void> {
    // 清除本地存储的用户信息和 token
    if (isBrowser) {
      localStorage.removeItem('auth_user');
      localStorage.removeItem('auth_token');
    }
  },
  
  // 获取当前登录的用户
  getCurrentUser(): AuthUser | null {
    if (!isBrowser) {
      return null;
    }
    
    try {
      const userStr = localStorage.getItem('auth_user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('Failed to parse user from localStorage', error);
      return null;
    }
  },
  
  // 获取 token
  getToken(): string | null {
    if (!isBrowser) {
      return null;
    }
    return localStorage.getItem('auth_token');
  },
  
  // 切换角色
  async switchRole(role: UserRole): Promise<AuthUser> {
    // 获取当前用户
    const currentUser = this.getCurrentUser();
    
    if (!currentUser) {
      throw new Error('用户未登录');
    }
    
    if (!currentUser.roles.includes(role)) {
      throw new Error('用户没有该角色权限');
    }
    
    // 更新当前角色
    const updatedUser: AuthUser = {
      ...currentUser,
      currentRole: role,
    };
    
    // 更新本地存储
    if (isBrowser) {
      localStorage.setItem('auth_user', JSON.stringify(updatedUser));
    }
    
    return updatedUser;
  },
  
  // 检查是否已登录
  isLoggedIn(): boolean {
    return !!this.getToken() && !!this.getCurrentUser();
  },

  // 刷新令牌
  async refreshToken(): Promise<string> {
    const token = this.getToken();
    
    if (!token) {
      throw new Error('无效的令牌');
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });
      
      if (!response.ok) {
        throw new Error('刷新令牌失败');
      }
      
      const data = await response.json();
      const newToken = data.access_token;
      
      // 更新本地存储中的令牌
      if (isBrowser) {
        localStorage.setItem('auth_token', newToken);
      }
      
      return newToken;
    } catch (error) {
      // 刷新令牌失败，清除用户状态
      this.logout();
      throw error;
    }
  },

  // 检查JWT令牌是否过期
  isTokenExpired(token: string): boolean {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        window
          .atob(base64)
          .split('')
          .map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
          })
          .join('')
      );
      
      const { exp } = JSON.parse(jsonPayload);
      const currentTime = Math.floor(Date.now() / 1000);
      
      // 提前5分钟视为过期，提供安全边际
      return exp < currentTime + 300; // 5分钟 = 300秒
    } catch (error) {
      // 解析失败，视为已过期
      console.error('JWT解析失败:', error);
      return true;
    }
  },
  
  // 获取有效的认证令牌（如过期自动刷新）
  async getValidToken(): Promise<string | null> {
    try {
      const token = this.getToken();
      
      if (!token) {
        return null;
      }
      
      // 检查令牌是否过期
      if (this.isTokenExpired(token)) {
        // 令牌已过期或即将过期，尝试刷新
        try {
          return await this.refreshToken();
        } catch (error) {
          // 刷新失败，登出并返回null
          this.logout();
          return null;
        }
      }
      
      // 令牌有效，直接返回
      return token;
    } catch (error) {
      console.error('获取有效令牌失败:', error);
      return null;
    }
  },

  // 获取当前用户ID
  getCurrentUserId(): string | null {
    const user = this.getCurrentUser();
    return user ? user.id : null;
  },

  // 获取当前用户角色
  getCurrentUserRole(): UserRole | null {
    const user = this.getCurrentUser();
    return user && user.currentRole !== undefined ? user.currentRole : null;
  },
};

// 角色选项
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
];