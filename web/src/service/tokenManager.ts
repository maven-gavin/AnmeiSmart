/**
 * 令牌管理器
 * 统一管理访问令牌的存储、获取、验证和刷新
 */

import { jwtUtils } from './jwt';
import { ApiClientError, ErrorType, apiClient } from './apiClient';
import { AUTH_CONFIG } from '@/config';

type RefreshTokenResponse = {
  access_token: string;
  refresh_token?: string;
  token_type?: string;
};

type RefreshTokenPayload = {
  token: string;
};

// 检查是否在浏览器环境
const isBrowser = typeof window !== 'undefined';

/**
 * 安全的本地存储工具
 */
const secureStorage = {
  getItem(key: string): string | null {
    if (!isBrowser) return null;
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  },

  setItem(key: string, value: string): boolean {
    if (!isBrowser) return false;
    try {
      localStorage.setItem(key, value);
      return true;
    } catch {
      return false;
    }
  },

  removeItem(key: string): boolean {
    if (!isBrowser) return false;
    try {
      localStorage.removeItem(key);
      return true;
    } catch {
      return false;
    }
  },

  clear(): boolean {
    if (!isBrowser) return false;
    try {
      Object.values(AUTH_CONFIG).forEach(key => {
        localStorage.removeItem(key);
      });
      return true;
    } catch {
      return false;
    }
  }
};

/**
 * 令牌管理器类
 */
export class TokenManager {
  private refreshPromise: Promise<string> | null = null;
  private readonly retryDelay = 1000;

  /**
   * 获取当前存储的访问令牌
   */
  getToken(): string | null {
    const token = secureStorage.getItem(AUTH_CONFIG.TOKEN_STORAGE_KEY);
    return token && jwtUtils.isValidFormat(token) ? token : null;
  }

  /**
   * 获取当前存储的刷新令牌
   */
  getRefreshToken(): string | null {
    const token = secureStorage.getItem(AUTH_CONFIG.REFRESH_TOKEN_KEY);
    return token && jwtUtils.isValidFormat(token) ? token : null;
  }

  /**
   * 存储访问令牌
   */
  setToken(token: string): boolean {
    if (!jwtUtils.isValidFormat(token)) {
      console.error('尝试存储无效格式的访问令牌');
      return false;
    }
    return secureStorage.setItem(AUTH_CONFIG.TOKEN_STORAGE_KEY, token);
  }

  /**
   * 存储刷新令牌
   */
  setRefreshToken(token: string): boolean {
    if (!jwtUtils.isValidFormat(token)) {
      console.error('尝试存储无效格式的刷新令牌');
      return false;
    }
    return secureStorage.setItem(AUTH_CONFIG.REFRESH_TOKEN_KEY, token);
  }

  /**
   * 存储令牌对（访问令牌和刷新令牌）
   */
  setTokens(accessToken: string, refreshToken: string): boolean {
    return this.setToken(accessToken) && this.setRefreshToken(refreshToken);
  }

  /**
   * 检查访问令牌是否过期
   */
  isTokenExpired(token?: string): boolean {
    const tokenToCheck = token || this.getToken();
    return !tokenToCheck || jwtUtils.isExpired(tokenToCheck);
  }

  /**
   * 获取有效的访问令牌（如果过期会自动刷新）
   */
  async getValidToken(isSmartBrainAPI?: boolean): Promise<string | null> {
    try {
      const token = this.getToken();
      
      if (!token) {
        return null;
      }
      
      // 如果令牌未过期，直接返回
      if (!this.isTokenExpired(token)) {
        return token;
      }
      
      // 令牌过期，尝试刷新
      return await this.refreshToken(isSmartBrainAPI);
    } catch (error) {
      console.error('获取有效令牌失败:', error);
      return null;
    }
  }

  /**
   * 刷新令牌
   */
  async refreshToken(isSmartBrainAPI?: boolean): Promise<string> {
    // 如果已经有刷新请求在进行中，等待其完成
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new ApiClientError('没有可用的刷新令牌', {
        status: 401,
        type: ErrorType.AUTHENTICATION,
      })
    }

    // 创建刷新请求
    this.refreshPromise = this.performTokenRefresh(refreshToken, isSmartBrainAPI);

    try {
      const newToken = await this.refreshPromise;
      return newToken;
    } catch (error) {
      // 刷新失败，清除令牌
      this.clearTokens();
      throw error;
    } finally {
      // 清除刷新承诺
      this.refreshPromise = null;
    }
  }

  /**
   * 执行令牌刷新请求
   */
  private async performTokenRefresh(refreshToken: string, isSmartBrainAPI?: boolean): Promise<string> {
    const maxRetries = 3;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const data = await this.requestRefreshToken(
          { token: refreshToken },
          isSmartBrainAPI
        );

        this.persistTokenPair(data);
        return data.access_token;
      } catch (error) {
        if (attempt === maxRetries) {
          if (error instanceof ApiClientError) {
            throw error;
          }
          throw new ApiClientError('令牌刷新失败', {
            status: 500,
            type: ErrorType.AUTHENTICATION,
            responseData: error instanceof Error ? error.message : String(error),
          });
        }

        await this.waitForRetry(attempt);
      }
    }

    throw new ApiClientError('令牌刷新失败', {
      status: 500,
      type: ErrorType.AUTHENTICATION,
    });
  }

  private async waitForRetry(attempt: number): Promise<void> {
    const delay = this.retryDelay * attempt;
    await new Promise((resolve) => setTimeout(resolve, delay));
  }

  private async requestRefreshToken(
    payload: RefreshTokenPayload,
    isSmartBrainAPI?: boolean
  ): Promise<RefreshTokenResponse> {
    const response = await apiClient.post<RefreshTokenResponse>(
      '/auth/refresh-token',
      {
        body: payload,
      },
      {
        skipAuth: true,
        isSmartBrainAPI,
        silent: true,
      }
    );

    if (!response.data) {
      throw new ApiClientError('刷新令牌失败，服务器无返回数据', {
        status: 500,
        type: ErrorType.AUTHENTICATION,
      });
    }

    return response.data;
  }

  private persistTokenPair(data: RefreshTokenResponse): void {
    if (!data.access_token || !jwtUtils.isValidFormat(data.access_token)) {
      throw new ApiClientError('服务器返回无效访问令牌', {
        status: 500,
        type: ErrorType.AUTHENTICATION,
      });
    }

    this.setToken(data.access_token);
    if (data.refresh_token && jwtUtils.isValidFormat(data.refresh_token)) {
      this.setRefreshToken(data.refresh_token);
    }
  }

  /**
   * 清除所有令牌
   */
  clearTokens(): boolean {
    return secureStorage.clear();
  }

  /**
   * 获取令牌剩余时间
   */
  getTokenTimeToExpiry(): number {
    const token = this.getToken();
    return token ? jwtUtils.getTimeToExpiry(token) : 0;
  }
}

// 导出单例实例
export const tokenManager = new TokenManager(); 