import { authService } from './authService';

// API基础URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

interface ApiResponse<T = any> extends Response {
  data?: T;
  bodyUsed: boolean; // 添加一个明确的标记，表示body是否已被使用
}

interface ApiError {
  status: number;
  message: string;
  detail?: string;
}

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

export const apiClient = {
  /**
   * 通用请求方法
   */
  async request<T = any>(
    endpoint: string,
    method: string = 'GET',
    data?: any
  ): Promise<ApiResponse<T>> {
    const url = endpoint.startsWith('http')
      ? endpoint
      : `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    // 添加身份验证头 - 使用 getValidToken 确保获取有效令牌
    try {
      const token = await authService.getValidToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('获取有效令牌失败:', error);
      // 令牌问题不阻止无需认证的请求继续进行
    }

    const options: RequestInit = {
      method,
      headers,
      credentials: 'include',
    };

    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);

      // 处理401未授权错误（令牌过期）
      if (response.status === 401) {
        // 尝试刷新令牌
        try {
          const newToken = await authService.refreshToken();
          
          // 使用新令牌重试请求
          headers['Authorization'] = `Bearer ${newToken}`;
          const retryOptions = { ...options, headers };
          const retryResponse = await fetch(url, retryOptions);
          
          // 如果重试也返回401，则可能是权限问题而非令牌过期
          if (retryResponse.status === 401) {
            // 清除会话并重定向到登录页
            authService.logout();
            redirectToLogin('登录已过期或权限不足，请重新登录');
            throw new Error('无权访问此资源');
          }
          
          return retryResponse as ApiResponse<T>;
        } catch (refreshError) {
          // 刷新令牌失败，清除会话并重定向到登录页
          authService.logout();
          redirectToLogin('会话已过期，请重新登录');
          throw new Error('会话已过期，请重新登录');
        }
      }

      // 增强响应对象，添加data属性
      const enhancedResponse = response as ApiResponse<T>;
      
      // 对于非204状态码，尝试解析JSON（仅当body未被读取时）
      if (response.status !== 204 && !response.bodyUsed) {
        try {
          // 克隆response以避免"body已被读取"的错误
          const responseClone = response.clone();
          enhancedResponse.data = await responseClone.json();
        } catch (e) {
          // 忽略JSON解析错误
          console.warn('JSON解析失败:', e);
        }
      }
      
      return enhancedResponse;
    } catch (error) {
      // 处理网络错误
      const apiError: ApiError = {
        status: 0,
        message: error instanceof Error ? error.message : '网络请求失败',
      };
      
      throw apiError;
    }
  },

  /**
   * GET请求
   */
  async get<T = any>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, 'GET');
  },

  /**
   * POST请求
   */
  async post<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, 'POST', data);
  },

  /**
   * PUT请求
   */
  async put<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, 'PUT', data);
  },

  /**
   * PATCH请求
   */
  async patch<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, 'PATCH', data);
  },

  /**
   * DELETE请求
   */
  async delete<T = any>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, 'DELETE');
  },

  /**
   * 获取有效的认证令牌
   * @returns 认证令牌
   */
  async getAuthToken(): Promise<string | null> {
    // 直接使用 authService 的 getValidToken 方法
    return authService.getValidToken();
  },

  /**
   * 检查JWT令牌是否过期
   * @param token JWT令牌
   * @returns 是否过期
   */
  isTokenExpired(token: string): boolean {
    // 直接使用 authService 的 isTokenExpired 方法
    return authService.isTokenExpired(token);
  }
}; 