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
    // 如果存在chatService模块，关闭WebSocket连接
    try {
      // 使用动态导入避免循环依赖
      const { closeWebSocketConnection } = await import('./chatService');
      closeWebSocketConnection();
      console.log('WebSocket连接已关闭');
    } catch (error) {
      console.error('关闭WebSocket连接失败:', error);
    }
    
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
      // 添加重试逻辑
      let retryCount = 0;
      const maxRetries = 3;
      
      while (retryCount < maxRetries) {
        try {
          console.log('尝试刷新令牌，当前尝试次数:', retryCount + 1);
          
          // 只发送令牌本身，不包含用户ID
          const response = await fetch(`${API_BASE_URL}/auth/refresh-token`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
              token: token,
              // 确保不发送其他可能导致类型错误的字段
            }),
            // 添加超时设置
            signal: AbortSignal.timeout(5000), // 5秒超时
          });
          
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: '刷新令牌失败' }));
            throw new Error(errorData.detail || '刷新令牌失败');
          }
          
          const data = await response.json();
          const newToken = data.access_token;
          
          // 更新本地存储中的令牌
          if (isBrowser) {
            localStorage.setItem('auth_token', newToken);
          }
          
          console.log('令牌刷新成功');
          return newToken;
        } catch (err) {
          retryCount++;
          // 捕获并记录详细错误信息
          const errorMessage = err instanceof Error ? err.message : String(err);
          console.warn(`刷新令牌失败，尝试重试 ${retryCount}/${maxRetries}:`, errorMessage);
          
          // 最后一次尝试失败则抛出错误
          if (retryCount >= maxRetries) {
            if (err instanceof Error) {
              throw new Error(`无法刷新令牌: ${err.message}`);
            } else {
              throw new Error(`无法刷新令牌: ${String(err)}`);
            }
          }
          
          // 等待一段时间再重试
          await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
        }
      }
      
      // 这行代码不应该被执行，但为了类型安全
      throw new Error('刷新令牌失败，已达到最大重试次数');
    } catch (error) {
      console.error('刷新令牌失败:', error);
      // 记录详细的错误信息
      if (error instanceof Error) {
        console.error('错误详情:', error.message);
      }
      
      // 刷新令牌失败，但不要立即清除用户状态
      // 我们在AuthContext中决定是否登出
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

// 处理请求错误，如果是401错误尝试刷新token，如果刷新失败则登出
export const handleApiError = async (error: any): Promise<void> => {
  // 检查是否是网络请求错误
  if (error && error.response && error.response.status === 401) {
    console.log('收到401错误，尝试刷新Token');
    try {
      // 尝试刷新token
      await authService.refreshToken();
    } catch (refreshError) {
      // 刷新失败，强制登出
      console.error('刷新Token失败，执行登出:', refreshError);
      authService.logout();
      // 如果在浏览器环境，重定向到登录页
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
  }
};

// 包装API请求，自动处理401错误
export const apiRequest = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const token = await authService.getValidToken();
  
  if (!token) {
    // 没有有效token，直接登出并重定向
    authService.logout();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('未登录或Token无效');
  }
  
  // 添加认证头
  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`,
  };
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });
    
    // 检查响应状态
    if (response.status === 401) {
      // 尝试刷新token
      try {
        const newToken = await authService.refreshToken();
        
        // 使用新token重试请求
        const retryResponse = await fetch(url, {
          ...options,
          headers: {
            ...options.headers,
            'Authorization': `Bearer ${newToken}`,
          },
        });
        
        return retryResponse;
      } catch (error) {
        // 刷新失败，登出并重定向
        authService.logout();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        throw new Error('Token刷新失败，请重新登录');
      }
    }
    
    return response;
  } catch (error) {
    // 处理网络错误等
    console.error('API请求失败:', error);
    throw error;
  }
};