/**
 * 菜单资源同步工具
 * 
 * 负责将前端菜单配置同步到后端资源库
 */

import { menuConfig } from '@/config/menuConfig';
import { apiClient } from '@/service/apiClient';
import type { MenuItem as ConfigMenuItem } from '@/types/menu';

export interface MenuItem {
  name: string;
  displayName: string;
  resourceType: 'menu';
  resourcePath: string;
  parentId?: string | null;
  priority?: number;
}

function flattenConfigMenus(items: ConfigMenuItem[], parentId?: string | null): MenuItem[] {
  const result: MenuItem[] = [];

  for (const item of items) {
    if (item.children?.length) {
      result.push({
        name: `menu:${item.id}`,
        displayName: item.label.trim(),
        resourceType: 'menu',
        resourcePath: item.path,
        parentId: parentId || null,
        priority: item.priority || 0,
      });
      result.push(...flattenConfigMenus(item.children, item.id));
      continue;
    }

    result.push({
      name: `menu:${item.id}`,
      displayName: item.label.trim(),
      resourceType: 'menu',
      resourcePath: item.path,
      parentId: parentId || null,
      priority: item.priority || 0,
    });
  }

  return result;
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
  const menuItems: MenuItem[] = flattenConfigMenus(menuConfig.items);
  
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

