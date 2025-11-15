export type UserRole = 'consultant' | 'doctor' | 'operator' | 'customer' | 'admin';

export interface AuthUser {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  avatar?: string;
  roles: UserRole[];
  currentRole?: UserRole;
  // 新增权限相关字段
  permissions?: string[];
  isAdmin?: boolean;
  tenantId?: string;
}

export interface LoginCredentials {
  username: string; // 可以是邮箱或手机号
  password: string;
}

export interface LoginResponse {
  user: AuthUser;
  token: string;
}

export interface AuthState {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

export interface RoleOption {
  id: UserRole;
  name: string;
  path: string;
  icon?: string;
}

// 新增权限相关类型定义
export interface Permission {
  id: string;
  name: string;
  displayName?: string;
  description?: string;
  permissionType: 'action' | 'resource' | 'feature' | 'system';
  scope: 'system' | 'tenant' | 'user' | 'resource';
  resource?: string;
  action?: string;
  isActive: boolean;
  isSystem: boolean;
  isAdmin: boolean;
  priority: number;
  tenantId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Role {
  id: string;
  name: string;
  displayName?: string;
  description?: string;
  isActive: boolean;
  isSystem: boolean;
  isAdmin: boolean;
  priority: number;
  tenantId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Tenant {
  id: string;
  name: string;
  displayName?: string;
  description?: string;
  tenantType: 'system' | 'standard' | 'premium' | 'enterprise';
  status: 'active' | 'inactive' | 'suspended' | 'pending';
  isSystem: boolean;
  isAdmin: boolean;
  priority: number;
  encryptedPubKey?: string;
  contactName?: string;
  contactEmail?: string;
  contactPhone?: string;
  createdAt: string;
  updatedAt: string;
}

export interface UserPermissionSummary {
  userId: string;
  username: string;
  roles: string[];
  permissions: string[];
  isAdmin: boolean;
  tenantId?: string;
} 