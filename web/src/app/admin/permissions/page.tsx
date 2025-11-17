'use client';

import React, { useState, useEffect, useRef, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { usePermission } from '@/hooks/usePermission';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { permissionService } from '@/service/permissionService';
import { handleApiError } from '@/service/apiClient';
import { Permission, Role, Tenant } from '@/types/auth';
import toast from 'react-hot-toast';
import AppLayout from '@/components/layout/AppLayout';
import { EnhancedPagination } from '@/components/ui/pagination';

export default function PermissionsPage() {
  const { user } = useAuthContext();
  const { isAdmin } = usePermission();
  const router = useRouter();
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTenant, setSelectedTenant] = useState<string>('all');

  // 权限相关状态
  const [isCreatePermissionDialogOpen, setIsCreatePermissionDialogOpen] = useState(false);
  const [permissionForm, setPermissionForm] = useState<{
    name: string;
    displayName: string;
    description: string;
    permissionType: 'action' | 'resource' | 'feature' | 'system';
    scope: 'system' | 'tenant' | 'user' | 'resource';
    resource: string;
    action: string;
    isActive: boolean;
    isSystem: boolean;
    isAdmin: boolean;
    priority: number;
  }>({
    name: '',
    displayName: '',
    description: '',
    permissionType: 'action',
    scope: 'tenant',
    resource: '',
    action: '',
    isActive: true,
    isSystem: false,
    isAdmin: false,
    priority: 0
  });
  const [permissionFormLoading, setPermissionFormLoading] = useState(false);
  const [permissionFormError, setPermissionFormError] = useState<string | null>(null);
  const [editingPermission, setEditingPermission] = useState<Permission | null>(null);
  const [isEditPermissionDialogOpen, setIsEditPermissionDialogOpen] = useState(false);
  const [deletePermissionTarget, setDeletePermissionTarget] = useState<Permission | null>(null);
  const [isDeletePermissionDialogOpen, setIsDeletePermissionDialogOpen] = useState(false);
  const [deletePermissionLoading, setDeletePermissionLoading] = useState(false);


  // 搜索和分页
  const [searchText, setSearchText] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);

  // 检查用户是否有管理员权限
  useEffect(() => {
    if (user && !isAdmin) {
      router.push('/unauthorized');
    }
  }, [user, isAdmin, router]);

  // 加载数据
  useEffect(() => {
    loadData();
  }, [selectedTenant]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [permissionsData, tenantsData] = await Promise.all([
        permissionService.getPermissions(selectedTenant === 'all' ? undefined : selectedTenant),
        permissionService.getTenants()
      ]);
      setPermissions(permissionsData);
      setTenants(tenantsData);
    } catch (err) {
      const message = handleApiError(err, '加载数据失败');
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  // 权限相关函数
  const resetPermissionForm = () => {
    setPermissionForm({
      name: '',
      displayName: '',
      description: '',
      permissionType: 'action',
      scope: 'tenant',
      resource: '',
      action: '',
      isActive: true,
      isSystem: false,
      isAdmin: false,
      priority: 0
    });
    setPermissionFormError(null);
  };

  const handleCreatePermission = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const name = permissionForm.name.trim();
    if (!name) {
      setPermissionFormError('权限名称不能为空');
      return;
    }

    setPermissionFormLoading(true);
    setPermissionFormError(null);

    try {
      await permissionService.createPermission({
        name,
        displayName: permissionForm.displayName.trim() || undefined,
        description: permissionForm.description.trim() || undefined,
        permissionType: permissionForm.permissionType,
        scope: permissionForm.scope,
        resource: permissionForm.resource.trim() || undefined,
        action: permissionForm.action.trim() || undefined,
        isActive: permissionForm.isActive,
        isSystem: permissionForm.isSystem,
        isAdmin: permissionForm.isAdmin,
        priority: permissionForm.priority,
        tenantId: selectedTenant === 'all' ? undefined : selectedTenant
      });
      toast.success('权限创建成功');
      resetPermissionForm();
      setIsCreatePermissionDialogOpen(false);
      loadData();
    } catch (err) {
      const message = handleApiError(err, '创建权限失败');
      setPermissionFormError(message);
    } finally {
      setPermissionFormLoading(false);
    }
  };

  const handleOpenEditPermission = (permission: Permission) => {
    setEditingPermission(permission);
    setPermissionForm({
      name: permission.name,
      displayName: permission.displayName || '',
      description: permission.description || '',
      permissionType: permission.permissionType,
      scope: permission.scope,
      resource: permission.resource || '',
      action: permission.action || '',
      isActive: permission.isActive,
      isSystem: permission.isSystem,
      isAdmin: permission.isAdmin,
      priority: permission.priority
    });
    setPermissionFormError(null);
    setIsEditPermissionDialogOpen(true);
  };

  const handleEditPermission = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editingPermission) return;

    setPermissionFormLoading(true);
    setPermissionFormError(null);

    try {
      const payload: any = {
        displayName: permissionForm.displayName.trim() || undefined,
        description: permissionForm.description.trim() || undefined,
        permissionType: permissionForm.permissionType,
        scope: permissionForm.scope,
        resource: permissionForm.resource.trim() || undefined,
        action: permissionForm.action.trim() || undefined,
        isActive: permissionForm.isActive,
        isSystem: permissionForm.isSystem,
        isAdmin: permissionForm.isAdmin,
        priority: permissionForm.priority
      };

      if (!editingPermission.isSystem) {
        payload.name = permissionForm.name.trim();
      }

      await permissionService.updatePermission(editingPermission.id, payload);
      toast.success('权限更新成功');
      setIsEditPermissionDialogOpen(false);
      setEditingPermission(null);
      loadData();
    } catch (err) {
      const message = handleApiError(err, '更新权限失败');
      setPermissionFormError(message);
    } finally {
      setPermissionFormLoading(false);
    }
  };

  const handleRequestDeletePermission = (permission: Permission) => {
    setDeletePermissionTarget(permission);
    setIsDeletePermissionDialogOpen(true);
  };

  const handleDeletePermission = async () => {
    if (!deletePermissionTarget) return;

    setDeletePermissionLoading(true);
    try {
      await permissionService.deletePermission(deletePermissionTarget.id);
      toast.success('权限删除成功');
      setIsDeletePermissionDialogOpen(false);
      setDeletePermissionTarget(null);
      loadData();
    } catch (err) {
      handleApiError(err, '删除权限失败');
    } finally {
      setDeletePermissionLoading(false);
    }
  };


  // 搜索和过滤
  const filterItems = () => {
    setCurrentPage(1);
    // 搜索逻辑在显示时处理
  };

  const resetFilters = () => {
    setSearchText('');
    setCurrentPage(1);
  };

  // 获取当前显示的数据
  const getFilteredData = () => {
    let data: Permission[] = permissions;

    if (searchText.trim()) {
      const searchLower = searchText.toLowerCase();
      data = data.filter((p) => 
        p.name.toLowerCase().includes(searchLower) ||
        (p.displayName && p.displayName.toLowerCase().includes(searchLower)) ||
        (p.description && p.description.toLowerCase().includes(searchLower))
      );
    }

    return data;
  };

  // 分页逻辑
  const filteredData = getFilteredData();
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentPermissions = filteredData.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredData.length / itemsPerPage);

  if (loading && permissions.length === 0) {
    return (
      <AppLayout requiredRole={user?.currentRole}>
        <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
        </div>
      </AppLayout>
    );
  }

  const getPermissionTypeStyle = (type: string) => {
    const styles: Record<string, string> = {
      action: 'bg-blue-100 text-blue-800',
      resource: 'bg-green-100 text-green-800',
      feature: 'bg-purple-100 text-purple-800',
      system: 'bg-red-100 text-red-800'
    };
    return styles[type] || 'bg-gray-100 text-gray-800';
  };

  const getScopeStyle = (scope: string) => {
    const styles: Record<string, string> = {
      system: 'bg-red-100 text-red-800',
      tenant: 'bg-orange-100 text-orange-800',
      user: 'bg-blue-100 text-blue-800',
      resource: 'bg-green-100 text-green-800'
    };
    return styles[scope] || 'bg-gray-100 text-gray-800';
  };


  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">权限管理</h1>
            <p className="text-sm text-gray-600 mt-1">管理系统权限</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Label htmlFor="tenant-select" className="text-sm">选择租户:</Label>
              <Select value={selectedTenant} onValueChange={setSelectedTenant}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="选择租户" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部租户</SelectItem>
                  {tenants.map((tenant) => (
                    <SelectItem key={tenant.id} value={tenant.id}>
                      {tenant.displayName || tenant.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button
              onClick={() => {
                setPermissionFormError(null);
                setIsCreatePermissionDialogOpen(true);
              }}
              className="bg-orange-500 hover:bg-orange-600"
            >
              创建权限
            </Button>
          </div>
        </div>

        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 flex-1">
              <Label htmlFor="search" className="w-24 flex-shrink-0">
                搜索:
              </Label>
              <Input
                id="search"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    filterItems();
                  }
                }}
                placeholder="搜索权限名称,显示名称,描述"
                className="flex-1"
              />
            </div>
            <div className="flex space-x-2 flex-shrink-0">
              <Button variant="outline" onClick={resetFilters}>
                重置
              </Button>
              <Button className="bg-orange-500 hover:bg-orange-600" onClick={filterItems}>
                查询
              </Button>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4 text-red-500">
            {error}
          </div>
        )}

        {/* 权限表格 */}
        <div className="overflow-hidden rounded-lg border border-gray-200 shadow">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    权限名称
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    显示名称
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    描述
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                    类型
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                    范围
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                    是否启用
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                    系统权限
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                    管理员权限
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {currentPermissions.map((permission) => {
                  return (
                    <tr key={permission.id} className="hover:bg-gray-50">
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                        {permission.id}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                        {permission.name}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {permission.displayName || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {permission.description || '-'}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-center text-sm">
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getPermissionTypeStyle(permission.permissionType)}`}>
                          {permission.permissionType === 'action' ? '动作' : 
                           permission.permissionType === 'resource' ? '资源' :
                           permission.permissionType === 'feature' ? '功能' : '系统'}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-center text-sm">
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getScopeStyle(permission.scope)}`}>
                          {permission.scope === 'system' ? '系统级' :
                           permission.scope === 'tenant' ? '租户级' :
                           permission.scope === 'user' ? '用户级' : '资源级'}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-center text-sm">
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          permission.isActive 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {permission.isActive ? '启用' : '禁用'}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-center text-sm">
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          permission.isSystem 
                            ? 'bg-blue-100 text-blue-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {permission.isSystem ? '是' : '否'}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-center text-sm">
                        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          permission.isAdmin 
                            ? 'bg-purple-100 text-purple-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {permission.isAdmin ? '是' : '否'}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                        <div className="flex justify-end space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleOpenEditPermission(permission)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            编辑
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRequestDeletePermission(permission)}
                            className="text-red-600 hover:text-red-800"
                            disabled={permission.isSystem}
                            title={permission.isSystem ? '系统权限不可删除' : undefined}
                          >
                            删除
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {currentPermissions.length === 0 && (
                  <tr>
                    <td colSpan={10} className="px-6 py-4 text-center text-sm text-gray-500">
                      暂无权限数据
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>


        {/* 分页 */}
        {filteredData.length > 0 && (
          <div className="mt-6">
            <EnhancedPagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={filteredData.length}
              itemsPerPage={itemsPerPage}
              itemsPerPageOptions={[5, 10, 20, 50, 100]}
              onPageChange={(page) => {
                setCurrentPage(page);
              }}
              onItemsPerPageChange={(newItemsPerPage) => {
                setItemsPerPage(newItemsPerPage);
                setCurrentPage(1);
              }}
              showPageInput={true}
            />
          </div>
        )}

        {/* 创建权限对话框 */}
        <Dialog
          open={isCreatePermissionDialogOpen}
          onOpenChange={(open) => {
            if (!open) {
              if (permissionFormLoading) return;
              setIsCreatePermissionDialogOpen(false);
              resetPermissionForm();
            } else {
              setIsCreatePermissionDialogOpen(true);
            }
          }}
        >
          <DialogContent className="sm:max-w-2xl bg-white max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>创建权限</DialogTitle>
              <DialogDescription>
                创建一个新的权限，设置权限名称、显示名称、描述和其他属性
              </DialogDescription>
            </DialogHeader>
            {permissionFormError && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-500">
                {permissionFormError}
              </div>
            )}
            <form onSubmit={handleCreatePermission} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="createPermissionName">权限名称 *</Label>
                  <Input
                    id="createPermissionName"
                    value={permissionForm.name}
                    onChange={(e) => setPermissionForm({ ...permissionForm, name: e.target.value })}
                    disabled={permissionFormLoading}
                    placeholder="例如: user:create"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="createPermissionDisplayName">显示名称</Label>
                  <Input
                    id="createPermissionDisplayName"
                    value={permissionForm.displayName}
                    onChange={(e) => setPermissionForm({ ...permissionForm, displayName: e.target.value })}
                    disabled={permissionFormLoading}
                    placeholder="例如: 创建用户"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="createPermissionDescription">权限描述</Label>
                <Textarea
                  id="createPermissionDescription"
                  value={permissionForm.description}
                  onChange={(e) => setPermissionForm({ ...permissionForm, description: e.target.value })}
                  disabled={permissionFormLoading}
                  rows={3}
                  placeholder="可选: 权限的详细描述"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="createPermissionType">权限类型</Label>
                  <Select
                    value={permissionForm.permissionType}
                    onValueChange={(value: any) => setPermissionForm({ ...permissionForm, permissionType: value })}
                    disabled={permissionFormLoading}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="action">动作权限</SelectItem>
                      <SelectItem value="resource">资源权限</SelectItem>
                      <SelectItem value="feature">功能权限</SelectItem>
                      <SelectItem value="system">系统权限</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="createPermissionScope">权限范围</Label>
                  <Select
                    value={permissionForm.scope}
                    onValueChange={(value: any) => setPermissionForm({ ...permissionForm, scope: value })}
                    disabled={permissionFormLoading}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="system">系统级</SelectItem>
                      <SelectItem value="tenant">租户级</SelectItem>
                      <SelectItem value="user">用户级</SelectItem>
                      <SelectItem value="resource">资源级</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="createPermissionResource">资源</Label>
                  <Input
                    id="createPermissionResource"
                    value={permissionForm.resource}
                    onChange={(e) => setPermissionForm({ ...permissionForm, resource: e.target.value })}
                    disabled={permissionFormLoading}
                    placeholder="例如: user"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="createPermissionAction">动作</Label>
                  <Input
                    id="createPermissionAction"
                    value={permissionForm.action}
                    onChange={(e) => setPermissionForm({ ...permissionForm, action: e.target.value })}
                    disabled={permissionFormLoading}
                    placeholder="例如: create"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="createPermissionIsActive">是否启用</Label>
                  <Switch
                    id="createPermissionIsActive"
                    checked={permissionForm.isActive}
                    onCheckedChange={(checked) => setPermissionForm({ ...permissionForm, isActive: checked })}
                    disabled={permissionFormLoading}
                  />
                </div>
                <p className="text-xs text-gray-500">禁用的权限将无法被使用</p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="createPermissionIsSystem">是否系统权限</Label>
                  <Switch
                    id="createPermissionIsSystem"
                    checked={permissionForm.isSystem}
                    onCheckedChange={(checked) => setPermissionForm({ ...permissionForm, isSystem: checked })}
                    disabled={permissionFormLoading}
                  />
                </div>
                <p className="text-xs text-gray-500">系统权限通常由系统自动创建，请谨慎设置</p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="createPermissionIsAdmin">是否管理员权限</Label>
                  <Switch
                    id="createPermissionIsAdmin"
                    checked={permissionForm.isAdmin}
                    onCheckedChange={(checked) => setPermissionForm({ ...permissionForm, isAdmin: checked })}
                    disabled={permissionFormLoading}
                  />
                </div>
                <p className="text-xs text-gray-500">管理员权限拥有系统管理权限</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="createPermissionPriority">权限优先级</Label>
                <Input
                  id="createPermissionPriority"
                  type="number"
                  value={permissionForm.priority}
                  onChange={(e) => setPermissionForm({ ...permissionForm, priority: Number(e.target.value) || 0 })}
                  disabled={permissionFormLoading}
                  placeholder="数字越大优先级越高"
                  min="0"
                />
                <p className="text-xs text-gray-500">用于权限排序和判断，数字越大优先级越高</p>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    if (permissionFormLoading) return;
                    setIsCreatePermissionDialogOpen(false);
                    resetPermissionForm();
                  }}
                  disabled={permissionFormLoading}
                >
                  取消
                </Button>
                <Button type="submit" disabled={permissionFormLoading} className="bg-orange-500 hover:bg-orange-600">
                  {permissionFormLoading ? '创建中...' : '创建权限'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* 编辑权限对话框 */}
        <Dialog
          open={isEditPermissionDialogOpen}
          onOpenChange={(open) => {
            if (!open) {
              if (permissionFormLoading) return;
              setIsEditPermissionDialogOpen(false);
              setEditingPermission(null);
            } else {
              setIsEditPermissionDialogOpen(true);
            }
          }}
        >
          <DialogContent className="sm:max-w-2xl bg-white max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>编辑权限</DialogTitle>
              <DialogDescription>
                修改权限信息
              </DialogDescription>
            </DialogHeader>
            {permissionFormError && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-500">
                {permissionFormError}
              </div>
            )}
            <form onSubmit={handleEditPermission} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="editPermissionName">权限名称 *</Label>
                  <Input
                    id="editPermissionName"
                    value={permissionForm.name}
                    onChange={(e) => setPermissionForm({ ...permissionForm, name: e.target.value })}
                    disabled={permissionFormLoading || editingPermission?.isSystem}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="editPermissionDisplayName">显示名称</Label>
                  <Input
                    id="editPermissionDisplayName"
                    value={permissionForm.displayName}
                    onChange={(e) => setPermissionForm({ ...permissionForm, displayName: e.target.value })}
                    disabled={permissionFormLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="editPermissionDescription">权限描述</Label>
                <Textarea
                  id="editPermissionDescription"
                  value={permissionForm.description}
                  onChange={(e) => setPermissionForm({ ...permissionForm, description: e.target.value })}
                  disabled={permissionFormLoading}
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="editPermissionType">权限类型</Label>
                  <Select
                    value={permissionForm.permissionType}
                    onValueChange={(value: any) => setPermissionForm({ ...permissionForm, permissionType: value })}
                    disabled={permissionFormLoading}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="action">动作权限</SelectItem>
                      <SelectItem value="resource">资源权限</SelectItem>
                      <SelectItem value="feature">功能权限</SelectItem>
                      <SelectItem value="system">系统权限</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="editPermissionScope">权限范围</Label>
                  <Select
                    value={permissionForm.scope}
                    onValueChange={(value: any) => setPermissionForm({ ...permissionForm, scope: value })}
                    disabled={permissionFormLoading}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="system">系统级</SelectItem>
                      <SelectItem value="tenant">租户级</SelectItem>
                      <SelectItem value="user">用户级</SelectItem>
                      <SelectItem value="resource">资源级</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="editPermissionResource">资源</Label>
                  <Input
                    id="editPermissionResource"
                    value={permissionForm.resource}
                    onChange={(e) => setPermissionForm({ ...permissionForm, resource: e.target.value })}
                    disabled={permissionFormLoading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="editPermissionAction">动作</Label>
                  <Input
                    id="editPermissionAction"
                    value={permissionForm.action}
                    onChange={(e) => setPermissionForm({ ...permissionForm, action: e.target.value })}
                    disabled={permissionFormLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="editPermissionIsActive">是否启用</Label>
                  <Switch
                    id="editPermissionIsActive"
                    checked={permissionForm.isActive}
                    onCheckedChange={(checked) => setPermissionForm({ ...permissionForm, isActive: checked })}
                    disabled={permissionFormLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="editPermissionIsSystem">是否系统权限</Label>
                  <Switch
                    id="editPermissionIsSystem"
                    checked={permissionForm.isSystem}
                    onCheckedChange={(checked) => setPermissionForm({ ...permissionForm, isSystem: checked })}
                    disabled={permissionFormLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="editPermissionIsAdmin">是否管理员权限</Label>
                  <Switch
                    id="editPermissionIsAdmin"
                    checked={permissionForm.isAdmin}
                    onCheckedChange={(checked) => setPermissionForm({ ...permissionForm, isAdmin: checked })}
                    disabled={permissionFormLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="editPermissionPriority">权限优先级</Label>
                <Input
                  id="editPermissionPriority"
                  type="number"
                  value={permissionForm.priority}
                  onChange={(e) => setPermissionForm({ ...permissionForm, priority: Number(e.target.value) || 0 })}
                  disabled={permissionFormLoading}
                  min="0"
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    if (permissionFormLoading) return;
                    setIsEditPermissionDialogOpen(false);
                    setEditingPermission(null);
                  }}
                  disabled={permissionFormLoading}
                >
                  取消
                </Button>
                <Button type="submit" disabled={permissionFormLoading} className="bg-orange-500 hover:bg-orange-600">
                  {permissionFormLoading ? '更新中...' : '更新权限'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* 删除权限确认对话框 */}
        <AlertDialog open={isDeletePermissionDialogOpen} onOpenChange={setIsDeletePermissionDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>确认删除</AlertDialogTitle>
              <AlertDialogDescription>
                确定要删除权限 "{deletePermissionTarget?.displayName || deletePermissionTarget?.name}" 吗？此操作不可撤销。
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={deletePermissionLoading}>取消</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDeletePermission}
                disabled={deletePermissionLoading}
                className="bg-red-600 hover:bg-red-700"
              >
                {deletePermissionLoading ? '删除中...' : '删除'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* 删除权限确认对话框 */}
        <AlertDialog open={isDeletePermissionDialogOpen} onOpenChange={setIsDeletePermissionDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>确认删除</AlertDialogTitle>
              <AlertDialogDescription>
                确定要删除权限 "{deletePermissionTarget?.displayName || deletePermissionTarget?.name}" 吗？此操作不可撤销。
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={deletePermissionLoading}>取消</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDeletePermission}
                disabled={deletePermissionLoading}
                className="bg-red-600 hover:bg-red-700"
              >
                {deletePermissionLoading ? '删除中...' : '删除'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </AppLayout>
  );
}
