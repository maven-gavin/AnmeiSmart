/**
 * JWT 工具函数模块
 * 提供 JWT 令牌的解析、验证等功能
 */

export interface JwtPayload {
  sub: string;
  exp: number;
  iat: number;
  [key: string]: unknown;
}

/**
 * JWT 工具类
 */
export const jwtUtils = {
  /**
   * 解析 JWT 令牌
   */
  parseToken(token: string): JwtPayload | null {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        throw new Error('无效的JWT格式');
      }

      const base64Url = parts[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('JWT解析失败:', error);
      return null;
    }
  },
  
  /**
   * 检查 JWT 令牌是否过期
   * @param token JWT令牌
   * @param bufferTime 缓冲时间（秒），默认5分钟
   */
  isExpired(token: string, bufferTime: number = 300): boolean {
    try {
      const payload = this.parseToken(token);
      if (!payload?.exp) return true;
      
      const currentTime = Math.floor(Date.now() / 1000);
      return payload.exp < currentTime + bufferTime;
    } catch {
      return true;
    }
  },

  /**
   * 获取令牌剩余有效时间（秒）
   */
  getTimeToExpiry(token: string): number {
    try {
      const payload = this.parseToken(token);
      if (!payload?.exp) return 0;
      
      const currentTime = Math.floor(Date.now() / 1000);
      return Math.max(0, payload.exp - currentTime);
    } catch {
      return 0;
    }
  },

  /**
   * 验证令牌格式
   */
  isValidFormat(token: string): boolean {
    if (!token || typeof token !== 'string') return false;
    
    const parts = token.split('.');
    return parts.length === 3 && parts.every(part => part.length > 0);
  }
}; 