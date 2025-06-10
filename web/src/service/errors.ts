/**
 * 统一错误处理模块
 * 提供标准化的错误类型和处理机制
 */

export enum ErrorType {
  AUTHENTICATION = 'AUTHENTICATION',
  AUTHORIZATION = 'AUTHORIZATION', 
  NETWORK = 'NETWORK',
  VALIDATION = 'VALIDATION',
  SERVER = 'SERVER',
  UNKNOWN = 'UNKNOWN'
}

export interface ApiError {
  type: ErrorType;
  status: number;
  message: string;
  detail?: string;
  timestamp: string;
}

export class AppError extends Error {
  constructor(
    public type: ErrorType,
    public status: number,
    message: string,
    public detail?: string
  ) {
    super(message);
    this.name = 'AppError';
    this.timestamp = new Date().toISOString();
  }

  timestamp: string;

  toApiError(): ApiError {
    return {
      type: this.type,
      status: this.status,
      message: this.message,
      detail: this.detail,
      timestamp: this.timestamp
    };
  }
}

/**
 * 错误处理工具函数
 */
export const errorHandler = {
  /**
   * 根据HTTP状态码创建错误
   */
  fromHttpStatus(status: number, message?: string | any, detail?: string): AppError {
    // 如果message是对象，尝试提取字符串
    let errorMessage = message;
    if (typeof message === 'object') {
      if (message && typeof message === 'object') {
        errorMessage = message.message || message.detail || JSON.stringify(message);
      }
    }
    switch (status) {
      case 401:
        return new AppError(
          ErrorType.AUTHENTICATION, 
          status, 
          errorMessage || '认证失败，请重新登录'
        );
      case 403:
        return new AppError(
          ErrorType.AUTHORIZATION, 
          status, 
          errorMessage || '权限不足，无法访问此资源'
        );
      case 422:
        return new AppError(
          ErrorType.VALIDATION, 
          status, 
          errorMessage || '请求参数验证失败',
          detail
        );
      case 500:
        return new AppError(
          ErrorType.SERVER, 
          status, 
          errorMessage || '服务器内部错误'
        );
      default:
        return new AppError(
          ErrorType.UNKNOWN, 
          status, 
          errorMessage || '未知错误'
        );
    }
  },

  /**
   * 处理网络错误
   */
  fromNetworkError(error: Error): AppError {
    return new AppError(
      ErrorType.NETWORK,
      0,
      '网络连接失败，请检查网络设置',
      error.message
    );
  },

  /**
   * 从响应创建错误
   */
  async fromResponse(response: Response): Promise<AppError> {
    let errorMessage = '请求失败';
    let detail: string | undefined;

    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
      detail = errorData.detail;
    } catch {
      // 忽略JSON解析错误
    }

    return this.fromHttpStatus(response.status, errorMessage, detail);
  },

  /**
   * 重定向到登录页面
   */
  redirectToLogin(message: string): void {
    if (typeof window === 'undefined') return;
    
    const currentPath = window.location.pathname;
    const returnUrl = encodeURIComponent(currentPath);
    const errorMsg = encodeURIComponent(message);
    
    window.location.href = `/login?returnUrl=${returnUrl}&error=${errorMsg}`;
  }
}; 