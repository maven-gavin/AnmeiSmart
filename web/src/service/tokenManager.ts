/**
 * 令牌管理器
 * 统一管理访问令牌的存储、获取、验证和刷新
 */

import { jwtUtils } from './jwt';
import { AppError, ErrorType } from './errors';
import { API_BASE_URL, AUTH_CONFIG } from '@/config';

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

  /**
   * 获取当前存储的令牌
   */
  getToken(): string | null {
    const token = secureStorage.getItem(AUTH_CONFIG.TOKEN_STORAGE_KEY);
    return token && jwtUtils.isValidFormat(token) ? token : null;
  }

  /**
   * 存储令牌
   */
  setToken(token: string): boolean {
    if (!jwtUtils.isValidFormat(token)) {
      console.error('尝试存储无效格式的令牌');
      return false;
    }
    return secureStorage.setItem(AUTH_CONFIG.TOKEN_STORAGE_KEY, token);
  }

  /**
   * 检查令牌是否过期
   */
  isTokenExpired(token?: string): boolean {
    const tokenToCheck = token || this.getToken();
    return !tokenToCheck || jwtUtils.isExpired(tokenToCheck);
  }

  /**
   * 获取有效的令牌（如果过期会自动刷新）
   */
  async getValidToken(): Promise<string | null> {
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
      return await this.refreshToken();
    } catch (error) {
      console.error('获取有效令牌失败:', error);
      return null;
    }
  }

  /**
   * 刷新令牌
   */
  async refreshToken(): Promise<string> {
    // 如果已经有刷新请求在进行中，等待其完成
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const token = this.getToken();
    if (!token) {
      throw new AppError(ErrorType.AUTHENTICATION, 401, '没有可用的令牌');
    }

    // 创建刷新请求
    this.refreshPromise = this.performTokenRefresh(token);

    try {
      const newToken = await this.refreshPromise;
      this.setToken(newToken);
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
  private async performTokenRefresh(token: string): Promise<string> {
    const maxRetries = 3;
    const retryDelay = 1000; // 1秒

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5秒超时

        const response = await fetch(`${API_BASE_URL}/auth/refresh-token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token }),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: '令牌刷新失败' }));
          throw new AppError(
            ErrorType.AUTHENTICATION,
            response.status,
            errorData.detail || '令牌刷新失败'
          );
        }

        const data = await response.json();
        const newToken = data.access_token;

        if (!newToken || !jwtUtils.isValidFormat(newToken)) {
          throw new AppError(ErrorType.AUTHENTICATION, 500, '服务器返回无效令牌');
        }

        console.log('令牌刷新成功');
        return newToken;

      } catch (error) {
        console.warn(`令牌刷新尝试 ${attempt}/${maxRetries} 失败:`, error);

        // 如果是最后一次尝试，抛出错误
        if (attempt === maxRetries) {
          if (error instanceof AppError) {
            throw error;
          }
          throw new AppError(
            ErrorType.AUTHENTICATION,
            500,
            `令牌刷新失败: ${error instanceof Error ? error.message : String(error)}`
          );
        }

        // 等待后重试
        await new Promise(resolve => setTimeout(resolve, retryDelay * attempt));
      }
    }

    throw new AppError(ErrorType.AUTHENTICATION, 500, '令牌刷新失败');
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