/**
 * API 客户端
 * 提供统一的HTTP请求接口，支持自动认证和错误处理
 */

import { tokenManager } from './tokenManager';
import { AppError, ErrorType, errorHandler } from './errors';
import { API_BASE_URL } from '@/config';

/**
 * API 响应接口
 */
export interface ApiResponse<T = unknown> {
  data?: T;
  status: number;
  statusText: string;
  headers: Headers;
}

/**
 * 请求配置接口
 */
export interface RequestConfig extends RequestInit {
  skipAuth?: boolean;
  timeout?: number;
  skipContentType?: boolean;
}

/**
 * HTTP请求拦截器
 */
class RequestInterceptor {
  /**
   * 准备请求头
   */
  async prepareHeaders(config: RequestConfig): Promise<Record<string, string>> {
    const headers: Record<string, string> = {};

    // 只有在不跳过Content-Type时才设置默认值
    if (!config.skipContentType) {
      headers['Content-Type'] = 'application/json';
    }

    // 添加配置中的headers
    if (config.headers) {
      Object.assign(headers, config.headers);
    }

    // 如果不跳过认证，添加授权头
    if (!config.skipAuth) {
      try {
        const token = await tokenManager.getValidToken();
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      } catch (error) {
        console.error('获取认证令牌失败:', error);
        // 认证错误不阻止请求继续，让服务器决定如何处理
      }
    }

    return headers;
  }

  /**
   * 处理请求超时
   */
  createTimeoutController(timeout?: number): AbortController {
    const controller = new AbortController();
    
    if (timeout && timeout > 0) {
      setTimeout(() => controller.abort(), timeout);
    }
    
    return controller;
  }
}

/**
 * HTTP响应处理器
 */
class ResponseHandler {
  /**
   * 处理成功响应
   */
  async handleSuccess<T>(response: Response): Promise<ApiResponse<T>> {
    let data: T | undefined;

    // 对于204无内容状态码，不解析响应体
    if (response.status !== 204) {
      try {
        const contentType = response.headers.get('content-type');
        if (contentType?.includes('application/json')) {
          data = await response.json();
        } else if (contentType?.startsWith('image/') || 
                   contentType?.startsWith('audio/') ||
                   contentType?.startsWith('video/') ||
                   contentType?.includes('pdf') || 
                   contentType?.includes('octet-stream')) {
          // 对于二进制数据，返回Blob
          data = await response.blob() as unknown as T;
        } else {
          // 非JSON响应，尝试解析为文本
          data = await response.text() as unknown as T;
        }
      } catch (error) {
        console.warn('响应体解析失败:', error);
        // 解析失败不抛出错误，返回空数据
      }
    }

    return {
      data,
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    };
  }

  /**
   * 处理错误响应
   */
  async handleError(response: Response): Promise<never> {
    // 对于401错误，尝试刷新令牌
    if (response.status === 401) {
      try {
        await tokenManager.refreshToken();
        // 刷新成功，抛出特殊错误以便调用者重试
        throw new AppError(ErrorType.AUTHENTICATION, 401, 'TOKEN_REFRESHED');
      } catch (refreshError: unknown) {
        // 刷新失败，重定向到登录页
        errorHandler.redirectToLogin('会话已过期，请重新登录');
        throw new AppError(ErrorType.AUTHENTICATION, 401, '会话已过期，请重新登录');
      }
    }

    // 其他错误状态码
    throw await errorHandler.fromResponse(response);
  }
}

/**
 * API客户端类
 */
class ApiClient {
  private interceptor = new RequestInterceptor();
  private responseHandler = new ResponseHandler();

  /**
   * 构建完整URL
   */
  private buildUrl(endpoint: string): string {
    if (endpoint.startsWith('http')) {
      return endpoint;
    }
    
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${API_BASE_URL}${cleanEndpoint}`;
  }

  /**
   * 核心请求方法
   */
  async request<T = unknown>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const url = this.buildUrl(endpoint);
    const maxRetries = 1; // 最多重试一次（用于令牌刷新后的重试）

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        // 准备请求配置
        const headers = await this.interceptor.prepareHeaders(config);
        const controller = this.interceptor.createTimeoutController(config.timeout);

        const requestConfig: RequestInit = {
          ...config,
          headers,
          signal: controller.signal,
          // 移除 credentials: 'include'，因为使用 JWT Token 认证
        };

        // 发起请求
        const response = await fetch(url, requestConfig);

        // 处理响应
        if (response.ok) {
          return await this.responseHandler.handleSuccess<T>(response);
        } else {
          await this.responseHandler.handleError(response);
        }
      } catch (error: unknown) {
        // 如果是令牌刷新成功的标记，重试请求
        if (error instanceof AppError && 
            error.message === 'TOKEN_REFRESHED' && 
            attempt === 0) {
          continue;
        }

        // 处理网络错误
        if (error instanceof TypeError || 
            (error instanceof Error && error.name === 'AbortError')) {
          throw errorHandler.fromNetworkError(error);
        }

        // 重新抛出其他错误
        throw error;
      }
    }

    throw new AppError(ErrorType.UNKNOWN, 500, '请求失败');
  }

  /**
   * GET请求
   */
  async get<T = unknown>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  /**
   * POST请求
   */
  async post<T = unknown>(
    endpoint: string, 
    data?: unknown, 
    config?: RequestConfig
  ): Promise<ApiResponse<T>> {
    const requestConfig: RequestConfig = {
      ...config,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    };

    return this.request<T>(endpoint, requestConfig);
  }

  /**
   * PUT请求
   */
  async put<T = unknown>(
    endpoint: string, 
    data?: unknown, 
    config?: RequestConfig
  ): Promise<ApiResponse<T>> {
    const requestConfig: RequestConfig = {
      ...config,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    };

    return this.request<T>(endpoint, requestConfig);
  }

  /**
   * PATCH请求
   */
  async patch<T = unknown>(
    endpoint: string, 
    data?: unknown, 
    config?: RequestConfig
  ): Promise<ApiResponse<T>> {
    const requestConfig: RequestConfig = {
      ...config,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    };

    return this.request<T>(endpoint, requestConfig);
  }

  /**
   * DELETE请求
   */
  async delete<T = unknown>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }

  /**
   * 文件上传请求
   */
  async upload<T = unknown>(
    endpoint: string,
    formData: FormData,
    config?: RequestConfig
  ): Promise<ApiResponse<T>> {
    // 为文件上传创建特殊的配置，跳过默认的Content-Type设置
    const requestConfig: RequestConfig = {
      ...config,
      method: 'POST',
      body: formData,
      headers: {
        ...config?.headers,
        // 不设置Content-Type，让浏览器自动设置multipart/form-data边界
      },
      skipContentType: true, // 添加标记来跳过Content-Type设置
    };

    return this.request<T>(endpoint, requestConfig);
  }

  /**
   * 获取认证令牌
   */
  async getAuthToken(): Promise<string | null> {
    return tokenManager.getValidToken();
  }

  /**
   * 检查令牌是否过期
   */
  isTokenExpired(token?: string): boolean {
    return tokenManager.isTokenExpired(token);
  }
}

// 导出单例实例
export const apiClient = new ApiClient(); 