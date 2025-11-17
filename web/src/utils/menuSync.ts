/**
 * 菜单资源同步工具
 * 
 * 负责将前端菜单配置同步到后端资源库
 */

import { menuConfig } from '@/config/menuConfig';
import { apiClient } from '@/service/apiClient';

export interface MenuItem {
  name: string;
  displayName: string;
  resourceType: 'menu';
  resourcePath: string;
  parentId?: string | null;
  priority?: number;
}

export interface SyncMenusResponse {
  synced_count: number;
  created_count: number;
  updated_count: number;
}

/**
 * 同步菜单资源到后端
 */
export async function syncMenuResources(): Promise<SyncMenusResponse> {
  const menuItems: MenuItem[] = menuConfig.items.map(item => ({
    name: `menu:${item.id}`,
    displayName: item.label.trim(),
    resourceType: 'menu' as const,
    resourcePath: item.path,
    parentId: item.parentId || null,
    priority: item.priority || 0,
  }));
  
  try {
    const response = await apiClient.post<SyncMenusResponse>(
      '/resources/sync-menus',
      { 
        menus: menuItems,
        version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0'
      }
    );
    
    console.log('菜单资源同步成功:', response.data);
    return response.data;
  } catch (error) {
    console.error('菜单资源同步失败:', error);
    throw error;
  }
}

/**
 * 检查是否需要同步菜单资源
 * 仅在开发环境或管理员登录时同步
 */
export function shouldSyncMenuResources(isAdmin: boolean = false): boolean {
  // 开发环境总是同步
  if (process.env.NODE_ENV === 'development') {
    return true;
  }
  
  // 生产环境仅管理员同步
  return isAdmin;
}

