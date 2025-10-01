'use client';

import React from 'react';
import { usePermissionGuard } from '@/hooks/usePermissionGuard';
import { useHasPermission, useHasRole, useIsAdmin, useHasAnyPermission, useHasAnyRole } from '@/hooks/usePermissionGuard';

interface PermissionGuardProps {
  children: React.ReactNode;
  requiredPermission?: string;
  requiredPermissions?: string[];
  requiredRole?: string;
  requiredRoles?: string[];
  requireAuth?: boolean;
  fallback?: React.ReactNode;
  loading?: React.ReactNode;
}

/**
 * 权限守卫组件
 * 根据用户权限和角色控制子组件的显示
 */
export function PermissionGuard({
  children,
  requiredPermission,
  requiredPermissions,
  requiredRole,
  requiredRoles,
  requireAuth = true,
  fallback = null,
  loading = <div>加载中...</div>
}: PermissionGuardProps) {
  const { isAuthorized, error, loading: authLoading } = usePermissionGuard({
    requiredPermission,
    requiredPermissions,
    requiredRole,
    requiredRoles,
    requireAuth
  });

  if (authLoading) {
    return <>{loading}</>;
  }

  if (!isAuthorized) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

interface HasPermissionProps {
  children: React.ReactNode;
  permission: string;
  fallback?: React.ReactNode;
}

/**
 * 权限检查组件
 * 检查用户是否有指定权限
 */
export function HasPermission({ children, permission, fallback = null }: HasPermissionProps) {
  const hasPermission = useHasPermission(permission);
  return hasPermission ? <>{children}</> : <>{fallback}</>;
}

interface HasRoleProps {
  children: React.ReactNode;
  role: string;
  fallback?: React.ReactNode;
}

/**
 * 角色检查组件
 * 检查用户是否有指定角色
 */
export function HasRole({ children, role, fallback = null }: HasRoleProps) {
  const hasRole = useHasRole(role);
  return hasRole ? <>{children}</> : <>{fallback}</>;
}

interface IsAdminProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * 管理员检查组件
 * 检查用户是否为管理员
 */
export function IsAdmin({ children, fallback = null }: IsAdminProps) {
  const isAdmin = useIsAdmin();
  return isAdmin ? <>{children}</> : <>{fallback}</>;
}

interface HasAnyPermissionProps {
  children: React.ReactNode;
  permissions: string[];
  fallback?: React.ReactNode;
}

/**
 * 任意权限检查组件
 * 检查用户是否有任意一个指定权限
 */
export function HasAnyPermission({ children, permissions, fallback = null }: HasAnyPermissionProps) {
  const hasAnyPermission = useHasAnyPermission(permissions);
  return hasAnyPermission ? <>{children}</> : <>{fallback}</>;
}

interface HasAnyRoleProps {
  children: React.ReactNode;
  roles: string[];
  fallback?: React.ReactNode;
}

/**
 * 任意角色检查组件
 * 检查用户是否有任意一个指定角色
 */
export function HasAnyRole({ children, roles, fallback = null }: HasAnyRoleProps) {
  const hasAnyRole = useHasAnyRole(roles);
  return hasAnyRole ? <>{children}</> : <>{fallback}</>;
}

// 所有组件已通过单独的export function声明导出
