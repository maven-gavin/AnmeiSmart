'use client';

import { useState, useEffect, useRef, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
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
import toast from 'react-hot-toast';
import AppLayout from '@/components/layout/AppLayout';

type RoleItem = {
  id: string;
  name: string;
  description?: string | null;
  displayName?: string | null;
  isActive?: boolean;
  isSystem?: boolean;
  isAdmin?: boolean;
  priority?: number | null;
  tenantId?: string | null;
};

const normalizeRole = (role: any): RoleItem => {
  const id = role?.id ? String(role.id) : '';
  return {
    id,
    name: role?.name ?? '',
    description: role?.description ?? null,
    displayName: role?.displayName ?? role?.display_name ?? role?.name ?? '',
    isActive: role?.isActive ?? role?.is_active ?? true,
    isSystem: role?.isSystem ?? role?.is_system ?? false,
    isAdmin: role?.isAdmin ?? role?.is_admin ?? false,
    priority: typeof role?.priority === 'number' ? role.priority : Number(role?.priority ?? 0),
    tenantId: role?.tenantId ?? role?.tenant_id ?? null,
  };
};

const resolveErrorMessage = (error: unknown, fallback: string): string => {
  if (error && typeof error === 'object' && 'response' in error) {
    const response = (error as { response?: { data?: any } }).response;
    const apiMessage = response?.data?.message;
    if (typeof apiMessage === 'string') {
      return apiMessage;
    }
    const detail = response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
    if (typeof response?.data === 'string') {
      return response.data;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
};

export default function RolesPage() {
  const { user } = useAuthContext();
  const router = useRouter();
  const [roles, setRoles] = useState<RoleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [roleName, setRoleName] = useState('');
  const [roleDisplayName, setRoleDisplayName] = useState('');
  const [roleDescription, setRoleDescription] = useState('');
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  // 添加分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(5);
  
  // 添加搜索筛选状态
  const [searchId, setSearchId] = useState('');
  const [searchName, setSearchName] = useState('');
  const [searchDescription, setSearchDescription] = useState('');
  const [allRoles, setAllRoles] = useState<RoleItem[]>([]);
  const [editingRole, setEditingRole] = useState<RoleItem | null>(null);
  const [editForm, setEditForm] = useState({ name: '', displayName: '', description: '' });
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<RoleItem | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const createNameRef = useRef(roleName);

  useEffect(() => {
    createNameRef.current = roleName;
  }, [roleName]);

  function resetCreateForm() {
    setRoleName('');
    setRoleDisplayName('');
    setRoleDescription('');
    setFormError(null);
  }

  const handleCreateNameChange = (value: string) => {
    const previousName = createNameRef.current.trim();
    setRoleName(value);
    setRoleDisplayName((prev) => {
      const trimmedPrev = prev.trim();
      if (!trimmedPrev || trimmedPrev === previousName) {
        return value;
      }
      return prev;
    });
  };

  // 检查用户是否有管理员权限
  useEffect(() => {
    if (user && !user.roles.includes('admin')) {
      router.push('/unauthorized');
    }
  }, [user, router]);

  // 获取角色列表
  const fetchRoles = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await permissionService.getRoles();
      const normalized = Array.isArray(data) ? data.map(normalizeRole) : [];
      setAllRoles(normalized);
      setRoles(normalized);
    } catch (err) {
      const message = resolveErrorMessage(err, '获取角色列表失败');
      setError(message);
      toast.error(message);
      console.error('获取角色列表错误', err);
    } finally {
      setLoading(false);
    }
  };

  // 筛选角色
  const filterRoles = () => {
    setCurrentPage(1); // 重置到第一页
    let filteredRoles = [...allRoles];
    
    if (searchId) {
      const keyword = searchId.toLowerCase();
      filteredRoles = filteredRoles.filter((role) =>
        role.id.toLowerCase().includes(keyword)
      );
    }
    
    if (searchName) {
      const keyword = searchName.toLowerCase();
      filteredRoles = filteredRoles.filter((role) =>
        role.name.toLowerCase().includes(keyword)
      );
    }
    
    if (searchDescription) {
      const keyword = searchDescription.toLowerCase();
      filteredRoles = filteredRoles.filter(
        (role) =>
          (role.description ?? '').toLowerCase().includes(keyword)
      );
    }
    
    setRoles(filteredRoles);
  };

  // 重置筛选条件
  const resetFilters = () => {
    setSearchId('');
    setSearchName('');
    setSearchDescription('');
    setRoles(allRoles);
    setCurrentPage(1);
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  useEffect(() => {
    const totalPages = Math.max(1, Math.ceil(roles.length / itemsPerPage));
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [roles, currentPage, itemsPerPage]);

  // 创建角色
  const handleCreateRole = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!roleName.trim()) {
      setFormError('角色名称不能为空');
      return;
    }
    
    setFormLoading(true);
    setFormError(null);
    
    try {
      const nextDisplayName = roleDisplayName.trim();
      await permissionService.createRole({
        name: roleName.trim(),
        displayName: nextDisplayName || undefined,
        description: roleDescription.trim() || undefined
      });
      toast.success('角色创建成功');
      
      // 重置表单并刷新列表
      resetCreateForm();
      setIsCreateDialogOpen(false);
      fetchRoles();
    } catch (err) {
      const message = resolveErrorMessage(err, '创建角色失败');
      setFormError(message);
      toast.error(message);
      console.error('创建角色错误', err);
    } finally {
      setFormLoading(false);
    }
  };

  const handleOpenEdit = (role: RoleItem) => {
    setEditingRole(role);
    setEditForm({
      name: role.name,
      displayName: role.displayName ?? role.name,
      description: role.description ?? ''
    });
    setEditError(null);
    setIsEditDialogOpen(true);
  };

  const handleEditSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editingRole) {
      return;
    }

    const nextName = editForm.name.trim();
    if (!nextName) {
      setEditError('角色名称不能为空');
      return;
    }
    const nextDisplayName = editForm.displayName.trim();

    setEditLoading(true);
    setEditError(null);

    try {
      const payload: { name?: string; displayName?: string; description?: string } = {};

      if (!editingRole.isSystem) {
        payload.name = nextName;
      }
      payload.displayName = nextDisplayName || undefined;
      payload.description = editForm.description.trim() || undefined;

      await permissionService.updateRole(editingRole.id, payload);
      toast.success('角色更新成功');
      setIsEditDialogOpen(false);
      setEditingRole(null);
      fetchRoles();
    } catch (err) {
      const message = resolveErrorMessage(err, '更新角色失败');
      setEditError(message);
      toast.error(message);
    } finally {
      setEditLoading(false);
    }
  };

  const handleRequestDelete = (role: RoleItem) => {
    setDeleteTarget(role);
    setIsDeleteDialogOpen(true);
  };

  const handleDeleteRole = async () => {
    if (!deleteTarget) {
      return;
    }

    setDeleteLoading(true);
    try {
      await permissionService.deleteRole(deleteTarget.id);
      toast.success('角色删除成功');
      setIsDeleteDialogOpen(false);
      setDeleteTarget(null);
      fetchRoles();
    } catch (err) {
      const message = resolveErrorMessage(err, '删除角色失败');
      toast.error(message);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleCloseDeleteDialog = () => {
    if (deleteLoading) {
      return;
    }
    setIsDeleteDialogOpen(false);
    setDeleteTarget(null);
  };

  if (loading && roles.length === 0) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
      </div>
    );
  }

  // 角色名称样式映射
  const getRoleStyle = (name: string) => {
    const styles: Record<string, string> = {
      admin: 'bg-red-100 text-red-800',
      consultant: 'bg-blue-100 text-blue-800',
      doctor: 'bg-green-100 text-green-800',
      customer: 'bg-purple-100 text-purple-800',
      operator: 'bg-yellow-100 text-yellow-800'
    };
    
    return styles[name] || 'bg-gray-100 text-gray-800';
  };
  
  // 分页逻辑
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentRoles = roles.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(roles.length / itemsPerPage);

  // 页码变更
  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">角色管理</h1>
          <Button
            onClick={() => {
              setFormError(null);
              setIsCreateDialogOpen(true);
            }}
            className="bg-orange-500 hover:bg-orange-600"
          >
            创建角色
          </Button>
        </div>

        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
          <h2 className="mb-4 text-lg font-medium text-gray-800">组合查询</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <Label htmlFor="roleId" className="mb-2 block text-sm font-medium">
                角色ID
              </Label>
              <Input
                id="roleId"
                value={searchId}
                onChange={(e) => setSearchId(e.target.value)}
                placeholder="搜索角色ID"
                className="w-full"
              />
            </div>
            <div>
              <Label htmlFor="roleName" className="mb-2 block text-sm font-medium">
                角色名称
              </Label>
              <Input
                id="roleName"
                value={searchName}
                onChange={(e) => setSearchName(e.target.value)}
                placeholder="搜索角色名称"
                className="w-full"
              />
            </div>
            <div>
              <Label htmlFor="roleDescription" className="mb-2 block text-sm font-medium">
                角色描述
              </Label>
              <Input
                id="roleDescription"
                value={searchDescription}
                onChange={(e) => setSearchDescription(e.target.value)}
                placeholder="搜索角色描述"
                className="w-full"
              />
            </div>
          </div>
          <div className="mt-4 flex justify-end space-x-2">
            <Button variant="outline" onClick={resetFilters}>
              重置
            </Button>
            <Button className="bg-orange-500 hover:bg-orange-600" onClick={filterRoles}>
              查询
            </Button>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4 text-red-500">
            {error}
          </div>
        )}

        <div className="overflow-hidden rounded-lg border border-gray-200 shadow">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  角色名称
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  显示名称
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  描述
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {currentRoles.map((role) => (
                <tr key={role.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {role.id}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                    <span className={`rounded-full ${getRoleStyle(role.name)} px-3 py-1 text-sm font-medium`}>
                      {role.name}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    <div className="flex items-center space-x-2">
                      <span>{role.displayName || '-'}</span>
                      {role.isSystem && (
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                          系统角色
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {role.description || '-'}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                    <div className="flex justify-end space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleOpenEdit(role)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        编辑
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRequestDelete(role)}
                        className="text-red-600 hover:text-red-800"
                        disabled={role.isSystem}
                        title={role.isSystem ? '系统角色不可删除' : undefined}
                      >
                        删除
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}

              {roles.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                    暂无角色数据
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {roles.length > 0 && (
          <div className="mt-6 flex items-center justify-between">
            <div className="flex space-x-2">
              <Button
                onClick={() => paginate(currentPage - 1)}
                disabled={currentPage === 1}
                variant="outline"
                size="sm"
                className="px-3"
              >
                上一页
              </Button>

              {Array.from({ length: totalPages }, (_, i) => (
                <Button
                  key={i}
                  onClick={() => paginate(i + 1)}
                  variant={currentPage === i + 1 ? 'default' : 'outline'}
                  size="sm"
                  className={`px-3 ${currentPage === i + 1 ? 'bg-orange-500 hover:bg-orange-600' : ''}`}
                >
                  {i + 1}
                </Button>
              ))}

              <Button
                onClick={() => paginate(currentPage + 1)}
                disabled={currentPage === totalPages}
                variant="outline"
                size="sm"
                className="px-3"
              >
                下一页
              </Button>
            </div>
          </div>
        )}
      </div>

      <Dialog
        open={isCreateDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            if (formLoading) {
              return;
            }
            setIsCreateDialogOpen(false);
            resetCreateForm();
            return;
          }
          setIsCreateDialogOpen(true);
        }}
      >
        <DialogContent className="sm:max-w-md bg-white">
          <DialogHeader>
            <DialogTitle>创建角色</DialogTitle>
          </DialogHeader>
          {formError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-500">
              {formError}
            </div>
          )}
          <form onSubmit={handleCreateRole} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="createRoleName">角色名称 *</Label>
              <Input
                id="createRoleName"
                value={roleName}
                onChange={(e) => handleCreateNameChange(e.target.value)}
                disabled={formLoading}
                placeholder="例如: editor, manager"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="createRoleDisplayName">显示名称</Label>
              <Input
                id="createRoleDisplayName"
                value={roleDisplayName}
                onChange={(e) => setRoleDisplayName(e.target.value)}
                disabled={formLoading}
                placeholder="用于界面展示的名称，默认与角色名称一致"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="createRoleDescription">角色描述</Label>
              <Textarea
                id="createRoleDescription"
                value={roleDescription}
                onChange={(e) => setRoleDescription(e.target.value)}
                disabled={formLoading}
                rows={3}
                autoResize
                placeholder="可选: 角色的详细描述"
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  if (formLoading) {
                    return;
                  }
                  setIsCreateDialogOpen(false);
                  resetCreateForm();
                }}
                disabled={formLoading}
              >
                取消
              </Button>
              <Button type="submit" disabled={formLoading} className="bg-orange-500 hover:bg-orange-600">
                {formLoading ? '创建中...' : '创建角色'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog
        open={isEditDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            if (editLoading) {
              return;
            }
            setIsEditDialogOpen(false);
            setEditingRole(null);
            setEditError(null);
            return;
          }

          if (!editingRole) {
            setIsEditDialogOpen(false);
            return;
          }

          setIsEditDialogOpen(true);
        }}
      >
        <DialogContent className="sm:max-w-md bg-white">
          <DialogHeader>
            <DialogTitle>编辑角色</DialogTitle>
          </DialogHeader>
          {editError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-500">
              {editError}
            </div>
          )}
          <form onSubmit={handleEditSubmit} className="space-y-4">
            <div>
              <Label htmlFor="editRoleName">角色名称 *</Label>
              <Input
                id="editRoleName"
                value={editForm.name}
                onChange={(e) => setEditForm((prev) => ({ ...prev, name: e.target.value }))}
                disabled={editLoading || editingRole?.isSystem}
                placeholder="角色标识"
              />
              {editingRole?.isSystem && (
                <p className="mt-1 text-xs text-gray-500">系统角色名称不可修改</p>
              )}
            </div>
            <div>
              <Label htmlFor="editRoleDisplayName">显示名称</Label>
              <Input
                id="editRoleDisplayName"
                value={editForm.displayName}
                onChange={(e) => setEditForm((prev) => ({ ...prev, displayName: e.target.value }))}
                disabled={editLoading}
                placeholder="用于界面展示的名称"
              />
            </div>
            <div>
              <Label htmlFor="editRoleDescription">角色描述</Label>
              <Textarea
                id="editRoleDescription"
                value={editForm.description}
                onChange={(e) => setEditForm((prev) => ({ ...prev, description: e.target.value }))}
                rows={3}
                disabled={editLoading}
                placeholder="可选: 角色的详细描述"
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  if (editLoading) {
                    return;
                  }
                  setIsEditDialogOpen(false);
                  setEditingRole(null);
                  setEditError(null);
                }}
                disabled={editLoading}
              >
                取消
              </Button>
              <Button type="submit" disabled={editLoading}>
                {editLoading ? '保存中...' : '保存'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={isDeleteDialogOpen}
        onOpenChange={(open) => {
          if (open) {
            setIsDeleteDialogOpen(true);
          } else {
            handleCloseDeleteDialog();
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除角色</AlertDialogTitle>
            <AlertDialogDescription>
              删除后无法恢复，确定要删除角色
              <span className="font-semibold text-gray-900">
                {deleteTarget?.displayName || deleteTarget?.name}
              </span>
              吗？
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCloseDeleteDialog} disabled={deleteLoading}>
              取消
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteRole}
              className="bg-red-600 hover:bg-red-700"
              disabled={deleteLoading}
            >
              {deleteLoading ? '删除中...' : '确认删除'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </AppLayout>
  );
} 
