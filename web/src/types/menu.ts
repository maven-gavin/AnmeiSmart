import { UserRole } from "./auth";

export interface MenuItem {
  id: string;
  label: string;
  path: string;
  icon: string;
  roles?: UserRole[];  // 向后兼容：基于角色的菜单控制
  permission?: string;  // 基于权限的菜单控制（优先级更高）
  parentId?: string;  // 父菜单ID（用于层级菜单）
  priority?: number;  // 菜单优先级
  children?: MenuItem[];
}

export interface MenuConfig {
  items: MenuItem[];
} 