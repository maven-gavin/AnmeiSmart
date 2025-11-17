'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { usePermission } from '@/hooks/usePermission';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
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
import { resourceService, Resource, CreateResourceRequest, UpdateResourceRequest } from '@/service/resourceService';
import toast from 'react-hot-toast';
import AppLayout from '@/components/layout/AppLayout';
import { EnhancedPagination } from '@/components/ui/pagination';

export default function ResourcesPage() {
  const { user } = useAuthContext();
  const { isAdmin } = usePermission();
  const router = useRouter();
  const [resources, setResources] = useState<Resource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resourceTypeFilter, setResourceTypeFilter] = useState<'all' | 'api' | 'menu'>('all');

  // 资源表单状态
  const [isCreateResourceDialogOpen, setIsCreateResourceDialogOpen] = useState(false);
  const [resourceForm, setResourceForm] = useState<CreateResourceRequest>({
    name: '',
    displayName: '',
    description: '',
    resourceType: 'api',
    resourcePath: '',
    httpMethod: '',
    parentId: '',
    priority: 0,
  });
  const [resourceFormLoading, setResourceFormLoading] = useState(false);
  const [editingResource, setEditingResource] = useState<Resource | null>(null);
  const [isEditResourceDialogOpen, setIsEditResourceDialogOpen] = useState(false);
  const [deleteResourceTarget, setDeleteResourceTarget] = useState<Resource | null>(null);
  const [isDeleteResourceDialogOpen, setIsDeleteResourceDialogOpen] = useState(false);
  const [deleteResourceLoading, setDeleteResourceLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);

  // 搜索和分页
  const [searchText, setSearchText] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);
  const [total, setTotal] = useState(0);

  // 检查用户是否有管理员权限
  useEffect(() => {
    if (user && !isAdmin) {
      router.push('/unauthorized');
    }
  }, [user, isAdmin, router]);

  // 加载数据
  useEffect(() => {
    loadResources();
  }, [currentPage, itemsPerPage, resourceTypeFilter]);

  const loadResources = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await resourceService.getResources({
        resourceType: resourceTypeFilter === 'all' ? undefined : resourceTypeFilter,
        skip: (currentPage - 1) * itemsPerPage,
        limit: itemsPerPage,
      });
      setResources(response.resources);
      setTotal(response.total);
    } catch (err: any) {
      setError(err.message || '加载资源列表失败');
      toast.error('加载资源列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 创建资源
  const handleCreateResource = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setResourceFormLoading(true);
      await resourceService.createResource(resourceForm);
      toast.success('创建资源成功');
      setIsCreateResourceDialogOpen(false);
      setResourceForm({
        name: '',
        displayName: '',
        description: '',
        resourceType: 'api',
        resourcePath: '',
        httpMethod: '',
        parentId: '',
        priority: 0,
      });
      loadResources();
    } catch (err: any) {
      toast.error(err.message || '创建资源失败');
    } finally {
      setResourceFormLoading(false);
    }
  };

  // 更新资源
  const handleUpdateResource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingResource) return;
    
    try {
      setResourceFormLoading(true);
      const updateData: UpdateResourceRequest = {
        displayName: resourceForm.displayName,
        description: resourceForm.description,
        resourcePath: resourceForm.resourcePath,
        httpMethod: resourceForm.httpMethod,
        priority: resourceForm.priority,
      };
      await resourceService.updateResource(editingResource.id, updateData);
      toast.success('更新资源成功');
      setIsEditResourceDialogOpen(false);
      setEditingResource(null);
      loadResources();
    } catch (err: any) {
      toast.error(err.message || '更新资源失败');
    } finally {
      setResourceFormLoading(false);
    }
  };

  // 删除资源
  const handleDeleteResource = async () => {
    if (!deleteResourceTarget) return;
    
    try {
      setDeleteResourceLoading(true);
      await resourceService.deleteResource(deleteResourceTarget.id);
      toast.success('删除资源成功');
      setIsDeleteResourceDialogOpen(false);
      setDeleteResourceTarget(null);
      loadResources();
    } catch (err: any) {
      toast.error(err.message || '删除资源失败');
    } finally {
      setDeleteResourceLoading(false);
    }
  };

  // 同步菜单资源
  const handleSyncMenus = async () => {
    try {
      setSyncLoading(true);
      const { syncMenuResources } = await import('@/utils/menuSync');
      const result = await syncMenuResources();
      toast.success(`菜单资源同步成功：创建 ${result.created_count} 个，更新 ${result.updated_count} 个`);
      loadResources();
    } catch (err: any) {
      toast.error(err.message || '同步菜单资源失败');
    } finally {
      setSyncLoading(false);
    }
  };

  // 打开编辑对话框
  const openEditDialog = (resource: Resource) => {
    setEditingResource(resource);
    setResourceForm({
      name: resource.name,
      displayName: resource.displayName || '',
      description: resource.description || '',
      resourceType: resource.resourceType,
      resourcePath: resource.resourcePath,
      httpMethod: resource.httpMethod || '',
      parentId: resource.parentId || '',
      priority: resource.priority,
    });
    setIsEditResourceDialogOpen(true);
  };

  // 过滤资源
  const filteredResources = resources.filter(resource => {
    if (searchText) {
      const searchLower = searchText.toLowerCase();
      return (
        resource.name.toLowerCase().includes(searchLower) ||
        resource.displayName?.toLowerCase().includes(searchLower) ||
        resource.resourcePath.toLowerCase().includes(searchLower)
      );
    }
    return true;
  });

  return (
    <AppLayout>
      <div className="container mx-auto p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">资源管理</h1>
            <p className="mt-2 text-gray-600">管理API端点和菜单资源</p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleSyncMenus}
              disabled={syncLoading}
              variant="outline"
            >
              {syncLoading ? '同步中...' : '同步菜单资源'}
            </Button>
            <Button onClick={() => setIsCreateResourceDialogOpen(true)}>
              创建资源
            </Button>
          </div>
        </div>

        {/* 搜索和筛选 */}
        <div className="mb-4 flex gap-4">
          <Input
            placeholder="搜索资源名称、显示名称或路径..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="max-w-md"
          />
          <Select value={resourceTypeFilter} onValueChange={(value: any) => setResourceTypeFilter(value)}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="资源类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部</SelectItem>
              <SelectItem value="api">API资源</SelectItem>
              <SelectItem value="menu">菜单资源</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 资源列表 */}
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
          </div>
        ) : error ? (
          <div className="rounded-lg bg-red-50 p-4 text-red-800">{error}</div>
        ) : (
          <>
            <div className="rounded-lg border bg-white">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">资源名称</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">显示名称</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">类型</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">路径</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">HTTP方法</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">状态</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredResources.map((resource) => (
                    <tr key={resource.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">
                        <div className="font-medium text-gray-900">{resource.name}</div>
                        {resource.description && (
                          <div className="mt-1 text-xs text-gray-500">{resource.description}</div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {resource.displayName || '-'}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <Badge variant={resource.resourceType === 'api' ? 'default' : 'secondary'}>
                          {resource.resourceType === 'api' ? 'API' : '菜单'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">{resource.resourcePath}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {resource.httpMethod ? (
                          <Badge variant="outline">{resource.httpMethod}</Badge>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <Badge variant={resource.isActive ? 'default' : 'destructive'}>
                          {resource.isActive ? '启用' : '禁用'}
                        </Badge>
                        {resource.isSystem && (
                          <Badge variant="outline" className="ml-2">系统</Badge>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditDialog(resource)}
                            disabled={resource.isSystem}
                          >
                            编辑
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setDeleteResourceTarget(resource);
                              setIsDeleteResourceDialogOpen(true);
                            }}
                            disabled={resource.isSystem}
                            className="text-red-600 hover:text-red-700"
                          >
                            删除
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 分页 */}
            <div className="mt-4">
              <EnhancedPagination
                currentPage={currentPage}
                totalPages={Math.ceil(total / itemsPerPage)}
                onPageChange={setCurrentPage}
                itemsPerPage={itemsPerPage}
                onItemsPerPageChange={setItemsPerPage}
                totalItems={total}
              />
            </div>
          </>
        )}

        {/* 创建资源对话框 */}
        <Dialog open={isCreateResourceDialogOpen} onOpenChange={setIsCreateResourceDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>创建资源</DialogTitle>
              <DialogDescription>创建一个新的API或菜单资源</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateResource}>
              <div className="space-y-4 py-4">
                <div>
                  <Label htmlFor="name">资源名称 *</Label>
                  <Input
                    id="name"
                    value={resourceForm.name}
                    onChange={(e) => setResourceForm({ ...resourceForm, name: e.target.value })}
                    placeholder="如: api:user:create 或 menu:home"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="displayName">显示名称</Label>
                  <Input
                    id="displayName"
                    value={resourceForm.displayName}
                    onChange={(e) => setResourceForm({ ...resourceForm, displayName: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="description">描述</Label>
                  <Textarea
                    id="description"
                    value={resourceForm.description}
                    onChange={(e) => setResourceForm({ ...resourceForm, description: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="resourceType">资源类型 *</Label>
                    <Select
                      value={resourceForm.resourceType}
                      onValueChange={(value: 'api' | 'menu') =>
                        setResourceForm({ ...resourceForm, resourceType: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="api">API资源</SelectItem>
                        <SelectItem value="menu">菜单资源</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {resourceForm.resourceType === 'api' && (
                    <div>
                      <Label htmlFor="httpMethod">HTTP方法</Label>
                      <Select
                        value={resourceForm.httpMethod || undefined}
                        onValueChange={(value) => setResourceForm({ ...resourceForm, httpMethod: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="选择HTTP方法" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="GET">GET</SelectItem>
                          <SelectItem value="POST">POST</SelectItem>
                          <SelectItem value="PUT">PUT</SelectItem>
                          <SelectItem value="DELETE">DELETE</SelectItem>
                          <SelectItem value="PATCH">PATCH</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}                  
                </div>
                <div>
                  <Label htmlFor="resourcePath">资源路径 *</Label>
                  <Input
                    id="resourcePath"
                    className='flex-1'
                    value={resourceForm.resourcePath}
                    onChange={(e) => setResourceForm({ ...resourceForm, resourcePath: e.target.value })}
                    placeholder="/api/v1/users"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="priority">优先级</Label>
                  <Input
                    id="priority"
                    type="number"
                    value={(resourceForm.priority ?? 0).toString()}
                    onChange={(e) => setResourceForm({ ...resourceForm, priority: parseInt(e.target.value) || 0 })}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setIsCreateResourceDialogOpen(false)}>
                  取消
                </Button>
                <Button type="submit" disabled={resourceFormLoading}>
                  {resourceFormLoading ? '创建中...' : '创建'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* 编辑资源对话框 */}
        <Dialog open={isEditResourceDialogOpen} onOpenChange={setIsEditResourceDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>编辑资源</DialogTitle>
              <DialogDescription>更新资源信息</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleUpdateResource}>
              <div className="space-y-4 py-4">
                <div>
                  <Label>资源名称</Label>
                  <Input value={editingResource?.name || ''} disabled />
                </div>
                <div>
                  <Label htmlFor="edit-displayName">显示名称</Label>
                  <Input
                    id="edit-displayName"
                    value={resourceForm.displayName || ''}
                    onChange={(e) => setResourceForm({ ...resourceForm, displayName: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="edit-description">描述</Label>
                  <Textarea
                    id="edit-description"
                    value={resourceForm.description || ''}
                    onChange={(e) => setResourceForm({ ...resourceForm, description: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="edit-resourcePath">资源路径</Label>
                  <Input
                    id="edit-resourcePath"
                    value={resourceForm.resourcePath || ''}
                    onChange={(e) => setResourceForm({ ...resourceForm, resourcePath: e.target.value })}
                    required
                  />
                </div>
                {resourceForm.resourceType === 'api' && (
                  <div>
                    <Label htmlFor="edit-httpMethod">HTTP方法</Label>
                    <Select
                      value={resourceForm.httpMethod || undefined}
                      onValueChange={(value) => setResourceForm({ ...resourceForm, httpMethod: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择HTTP方法" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="GET">GET</SelectItem>
                        <SelectItem value="POST">POST</SelectItem>
                        <SelectItem value="PUT">PUT</SelectItem>
                        <SelectItem value="DELETE">DELETE</SelectItem>
                        <SelectItem value="PATCH">PATCH</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}
                <div>
                  <Label htmlFor="edit-priority">优先级</Label>
                  <Input
                    id="edit-priority"
                    type="number"
                    value={(resourceForm.priority ?? 0).toString()}
                    onChange={(e) => setResourceForm({ ...resourceForm, priority: parseInt(e.target.value) || 0 })}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setIsEditResourceDialogOpen(false)}>
                  取消
                </Button>
                <Button type="submit" disabled={resourceFormLoading}>
                  {resourceFormLoading ? '更新中...' : '更新'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* 删除确认对话框 */}
        <AlertDialog open={isDeleteResourceDialogOpen} onOpenChange={setIsDeleteResourceDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>确认删除</AlertDialogTitle>
              <AlertDialogDescription>
                确定要删除资源 "{deleteResourceTarget?.name}" 吗？此操作不可撤销。
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>取消</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDeleteResource}
                disabled={deleteResourceLoading}
                className="bg-red-600 hover:bg-red-700"
              >
                {deleteResourceLoading ? '删除中...' : '删除'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </AppLayout>
  );
}

