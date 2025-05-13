import { authService } from './authService';

// API基础URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// 跳转到登录页面并显示错误信息
const redirectToLogin = (message: string) => {
  // 清除用户状态
  authService.logout();
  
  // 保存当前URL，以便登录后重定向回来
  const currentPath = window.location.pathname;
  const returnUrl = encodeURIComponent(currentPath);
  
  // 将错误消息作为参数传递给登录页面
  const errorMsg = encodeURIComponent(message);
  
  // 重定向到登录页
  window.location.href = `/login?returnUrl=${returnUrl}&error=${errorMsg}`;
};

// 自定义API客户端
export const apiClient = {
  /**
   * 发送GET请求
   * @param endpoint API端点
   * @param authenticated 是否需要认证
   * @returns 响应数据
   */
  async get<T>(endpoint: string, authenticated: boolean = true): Promise<T> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (authenticated) {
        const token = await this.getAuthToken();
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'GET',
        headers,
      });

      console.log('response', response);

      if (response.status === 401) {
        // 获取具体错误信息
        let errorMessage = '会话已过期，请重新登录';
        try {
          const errorData = await response.json();
          if (errorData && errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch (e) {
          // 忽略JSON解析错误
        }
        
        // 401未授权，重定向到登录页
        redirectToLogin(errorMessage);
        throw new Error(errorMessage);
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '请求失败');
      }

      return await response.json();
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  },

  /**
   * 发送POST请求
   * @param endpoint API端点
   * @param data 请求数据
   * @param authenticated 是否需要认证
   * @returns 响应数据
   */
  async post<T>(endpoint: string, data: any, authenticated: boolean = true): Promise<T> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (authenticated) {
        const token = await this.getAuthToken();
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      });

      if (response.status === 401) {
        // 获取具体错误信息
        let errorMessage = '会话已过期，请重新登录';
        try {
          const errorData = await response.json();
          if (errorData && errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch (e) {
          // 忽略JSON解析错误
        }
        
        // 401未授权，重定向到登录页
        redirectToLogin(errorMessage);
        throw new Error(errorMessage);
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '请求失败');
      }

      return await response.json();
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  },

  /**
   * 发送PUT请求
   * @param endpoint API端点
   * @param data 请求数据
   * @param authenticated 是否需要认证
   * @returns 响应数据
   */
  async put<T>(endpoint: string, data: any, authenticated: boolean = true): Promise<T> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (authenticated) {
        const token = await this.getAuthToken();
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(data),
      });

      if (response.status === 401) {
        // 获取具体错误信息
        let errorMessage = '会话已过期，请重新登录';
        try {
          const errorData = await response.json();
          if (errorData && errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch (e) {
          // 忽略JSON解析错误
        }
        
        // 401未授权，重定向到登录页
        redirectToLogin(errorMessage);
        throw new Error(errorMessage);
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '请求失败');
      }

      return await response.json();
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  },

  /**
   * 发送DELETE请求
   * @param endpoint API端点
   * @param authenticated 是否需要认证
   * @returns 响应数据
   */
  async delete<T>(endpoint: string, authenticated: boolean = true): Promise<T> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (authenticated) {
        const token = await this.getAuthToken();
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'DELETE',
        headers,
      });

      if (response.status === 401) {
        // 获取具体错误信息
        let errorMessage = '会话已过期，请重新登录';
        try {
          const errorData = await response.json();
          if (errorData && errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch (e) {
          // 忽略JSON解析错误
        }
        
        // 401未授权，重定向到登录页
        redirectToLogin(errorMessage);
        throw new Error(errorMessage);
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '请求失败');
      }

      return await response.json();
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  },

  /**
   * 获取有效的认证令牌
   * @returns 认证令牌
   */
  async getAuthToken(): Promise<string | null> {
    try {
      // 获取当前令牌
      const token = authService.getToken();
      
      if (!token) {
        return null;
      }
      
      // 在这里可以添加令牌过期检查逻辑，如果过期，则刷新令牌
      // 简单的JWT过期检查
      const isTokenExpired = this.isTokenExpired(token);
      
      if (isTokenExpired) {
        // 令牌已过期，尝试刷新
        try {
          return await authService.refreshToken();
        } catch (error) {
          // 刷新令牌失败，重定向到登录页
          redirectToLogin('登录已过期，请重新登录');
          return null;
        }
      }
      
      return token;
    } catch (error) {
      console.error('获取认证令牌失败:', error);
      return null;
    }
  },

  /**
   * 检查JWT令牌是否过期
   * @param token JWT令牌
   * @returns 是否过期
   */
  isTokenExpired(token: string): boolean {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      
      const { exp } = JSON.parse(jsonPayload);
      const currentTime = Math.floor(Date.now() / 1000);
      
      return exp < currentTime;
    } catch (error) {
      // 解析失败，视为已过期，需要重新登录
      console.error('JWT解析失败:', error);
      return true;
    }
  }
}; 