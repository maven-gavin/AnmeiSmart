/**
 * 权限检查Hook
 * 
 * 提供权限检查功能，用于控制UI元素的显示和功能访问
 */

import { useMemo } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import { escapeRegExp } from '@/utils/regex';

export interface UsePermissionReturn {
  /**
   * 检查用户是否有指定权限
   */
  hasPermission: (permission: string) => boolean;
  
  /**
   * 检查用户是否有指定角色
   */
  hasRole: (role: string) => boolean;
  
  /**
   * 检查用户是否有任意一个指定权限
   */
  hasAnyPermission: (permissions: string[]) => boolean;
  
  /**
   * 检查用户是否有任意一个指定角色
   */
  hasAnyRole: (roles: string[]) => boolean;
  
  /**
   * 检查用户是否有指定资源权限
   */
  hasResource: (resourceName: string) => boolean;
  
  /**
   * 检查用户是否为管理员
   */
  isAdmin: boolean;
  
  /**
   * 用户的所有权限列表
   */
  permissions: string[];
  
  /**
   * 用户的所有角色列表
   */
  roles: string[];
}

/**
 * 权限检查Hook
 * 
 * @example
 * ```tsx
 * const { hasPermission, isAdmin } = usePermission();
 * 
 * {hasPermission('user:create') && (
 *   <Button onClick={handleCreate}>创建用户</Button>
 * )}
 * 
 * {isAdmin && (
 *   <AdminPanel />
 * )}
 * ```
 */
export function usePermission(): UsePermissionReturn {
  const { user } = useAuthContext();

  const permissions = useMemo(() => {
    if (!user) return [];
    
    // 从用户对象中获取权限列表
    // 这里假设用户对象有permissions字段，如果没有则需要从API获取
    if (user.permissions && Array.isArray(user.permissions)) {
      return user.permissions;
    }
    
    // 如果没有权限列表，返回空数组
    return [];
  }, [user]);

  const roles = useMemo(() => {
    if (!user) return [];
    
    // 从用户对象中获取角色列表
    if (user.roles && Array.isArray(user.roles)) {
      return user.roles;
    }
    
    // 如果没有角色列表，尝试从currentRole获取
    if (user.currentRole) {
      return [user.currentRole];
    }
    
    return [];
  }, [user]);

  const isAdmin = useMemo(() => {
    if (!user) return false;
    
    // 优先使用isAdmin字段（从API返回）
    if (user.isAdmin === true) {
      return true;
    }
    
    // 检查是否为管理员角色（包括administrator）
    // 注意：normalizeRole会将administrator转换为admin，但我们需要检查原始角色
    const adminRoles = ['admin', 'administrator', 'operator'];
    const userRoles = user.roles || [];
    
    // 检查原始角色列表（可能包含administrator）
    if (userRoles.some(role => adminRoles.includes(role.toLowerCase()))) {
      return true;
    }
    
    // 也检查normalized后的角色（如果roles已经被normalize）
    return roles.some(role => adminRoles.includes(role.toLowerCase()));
  }, [user, roles]);

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    
    // 管理员拥有所有权限
    if (isAdmin) return true;
    
    // 检查用户是否有指定权限
    return permissions.includes(permission);
  };

  const hasRole = (role: string): boolean => {
    if (!user) return false;
    
    return roles.some(r => r.toLowerCase() === role.toLowerCase());
  };

  const hasAnyPermission = (permissionList: string[]): boolean => {
    if (!user) return false;
    
    // 管理员拥有所有权限
    if (isAdmin) return true;
    
    return permissionList.some(permission => permissions.includes(permission));
  };

  const hasAnyRole = (roleList: string[]): boolean => {
    if (!user) return false;
    
    return roleList.some(role => roles.some(r => r.toLowerCase() === role.toLowerCase()));
  };

  const hasResource = (resourceName: string): boolean => {
    if (!user) return false;
    
    // 管理员拥有所有资源访问权限
    if (isAdmin) return true;
    
    // 检查用户是否有资源权限
    // 资源权限格式：menu:home, api:user:create
    return permissions.some(permission => {
      // 直接匹配
      if (permission === resourceName) return true;
      
      // 支持通配符匹配（如 menu:* 匹配所有菜单资源）
      if (permission.includes('*')) {
        // 先整体转义，再把 \* 恢复成通配符 .*
        // 这样即使 permission 里包含正则特殊字符（包括 (?< ）也不会导致企业微信 WebKit 报错
        const escaped = escapeRegExp(permission);
        const pattern = escaped.replace(/\\\*/g, '.*');
        try {
          const regex = new RegExp(`^${pattern}$`);
          return regex.test(resourceName);
        } catch (e) {
          // 写到页面日志（ErrorHandler 会读取并展示）
          try {
            const key = '__anmei_client_error_logs__';
            const raw = sessionStorage.getItem(key);
            const prev = raw ? (JSON.parse(raw) as any[]) : [];
            const next = [
              ...(Array.isArray(prev) ? prev : []),
              {
                id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
                time: new Date().toLocaleTimeString('zh-CN'),
                message: `权限正则构造失败: permission=${permission} pattern=${pattern} error=${String(e)}`,
              },
            ].slice(-20);
            sessionStorage.setItem(key, JSON.stringify(next));
          } catch {
            // ignore
          }
          return false;
        }
      }
      
      return false;
    });
  };

  return {
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAnyRole,
    hasResource,
    isAdmin,
    permissions,
    roles,
  };
}

