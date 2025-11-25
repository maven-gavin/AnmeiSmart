'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { usePermission } from '@/hooks/usePermission';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
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
import { resourceService, Resource } from '@/service/resourceService';
import toast from 'react-hot-toast';
import AppLayout from '@/components/layout/AppLayout';
import { EnhancedPagination } from '@/components/ui/pagination';
import ResourceCreateModal from '@/components/admin/ResourceCreateModal';
import ResourceEditModal from '@/components/admin/ResourceEditModal';

export default function ResourcesPage() {
  const { user } = useAuthContext();
  const { isAdmin } = usePermission();
  const router = useRouter();
  const [resources, setResources] = useState<Resource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resourceTypeFilter, setResourceTypeFilter] = useState<'all' | 'api' | 'menu'>('all');

  // 资源表单状态
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedResource, setSelectedResource] = useState<Resource | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [deleteResourceTarget, setDeleteResourceTarget] = useState<Resource | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
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

  // 处理资源创建
  const handleResourceCreated = () => {
    setShowCreateModal(false);
    loadResources();
  };

  // 处理资源更新
  const handleResourceUpdated = () => {
    setShowEditModal(false);
    setSelectedResource(null);
    loadResources();
  };

  // 处理编辑资源
  const handleEditResource = (resource: Resource) => {
    setSelectedResource(resource);
    setShowEditModal(true);
  };

  // 处理删除资源
  const handleDeleteResource = (resource: Resource) => {
    setDeleteResourceTarget(resource);
    setIsDeleteDialogOpen(true);
  };

  // 确认删除资源
  const handleConfirmDelete = async () => {
    if (!deleteResourceTarget) return;
    
    setDeleteLoading(true);
    try {
      await resourceService.deleteResource(deleteResourceTarget.id);
      toast.success('删除资源成功');
      setIsDeleteDialogOpen(false);
      setDeleteResourceTarget(null);
      // 如果当前页删除后没有数据了，且不是第一页，则跳转到上一页
      if (resources.length === 1 && currentPage > 1) {
        setCurrentPage(currentPage - 1);
      } else {
        loadResources();
      }
    } catch (err: any) {
      toast.error(err.message || '删除资源失败');
    } finally {
      setDeleteLoading(false);
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
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">资源管理</h1>
          <div className="flex gap-2">
            <Button
              onClick={handleSyncMenus}
              disabled={syncLoading}
              variant="outline"
            >
              {syncLoading ? '同步中...' : '同步菜单资源'}
            </Button>
            <Button 
              onClick={() => setShowCreateModal(true)}
              className="bg-orange-500 hover:bg-orange-600"
            >
              创建资源
            </Button>
          </div>
        </div>

        {/* 搜索区域 */}
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Label htmlFor="search" className="mb-2 block text-sm font-medium">关键词搜索</Label>
              <Input
                id="search"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    loadResources();
                  }
                }}
                placeholder="搜索资源名称、显示名称或路径..."
                className="w-full max-w-md"
              />
            </div>
            <div className="flex items-end gap-2 pb-1">
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
              <Button variant="outline" onClick={() => {
                setSearchText('');
                setResourceTypeFilter('all');
                setCurrentPage(1);
                loadResources();
              }}>
                重置
              </Button>
              <Button className="bg-orange-500 hover:bg-orange-600" onClick={loadResources}>
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

        <div className="overflow-hidden rounded-lg border border-gray-200 shadow">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  资源名称
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  显示名称
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  类型
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  路径
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  HTTP方法
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  状态
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center">
                    <div className="flex justify-center">
                      <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
                    </div>
                  </td>
                </tr>
              ) : filteredResources.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-4 text-center text-sm text-gray-500">
                    暂无资源数据
                  </td>
                </tr>
              ) : (
                filteredResources.map((resource) => (
                  <tr key={resource.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm">
                      <div className="font-medium text-gray-900">{resource.name}</div>
                      {resource.description && (
                        <div className="mt-1 text-xs text-gray-500">{resource.description}</div>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {resource.displayName || '-'}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      <Badge variant={resource.resourceType === 'api' ? 'default' : 'secondary'}>
                        {resource.resourceType === 'api' ? 'API' : '菜单'}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {resource.resourcePath}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {resource.httpMethod ? (
                        <Badge variant="outline">{resource.httpMethod}</Badge>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      <div className="flex flex-wrap gap-1">
                        <span className={`px-2 py-1 rounded-full text-xs ${resource.isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {resource.isActive ? '启用' : '禁用'}
                        </span>
                        {resource.isSystem && (
                          <span className="px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-800">
                            系统
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditResource(resource)}
                          disabled={resource.isSystem}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          编辑
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteResource(resource)}
                          disabled={resource.isSystem}
                          className="text-red-600 hover:text-red-800"
                        >
                          删除
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* 分页组件 */}
        {filteredResources.length > 0 && (
          <div className="mt-6">
            <EnhancedPagination
              currentPage={currentPage}
              totalPages={Math.ceil(total / itemsPerPage)}
              totalItems={total}
              itemsPerPage={itemsPerPage}
              itemsPerPageOptions={[5, 10, 20, 50, 100]}
              onPageChange={setCurrentPage}
              onItemsPerPageChange={(newLimit) => {
                setItemsPerPage(newLimit);
                setCurrentPage(1);
              }}
              showPageInput={true}
            />
          </div>
        )}

        {/* 创建资源模态框 */}
        {showCreateModal && (
          <ResourceCreateModal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            onResourceCreated={handleResourceCreated}
          />
        )}

        {/* 编辑资源模态框 */}
        {showEditModal && selectedResource && (
          <ResourceEditModal
            isOpen={showEditModal}
            onClose={() => {
              setShowEditModal(false);
              setSelectedResource(null);
            }}
            resource={selectedResource}
            onResourceUpdated={handleResourceUpdated}
          />
        )}

        {/* 删除确认对话框 */}
        <AlertDialog
          open={isDeleteDialogOpen}
          onOpenChange={(open) => {
            if (open) {
              setIsDeleteDialogOpen(true);
            } else {
              if (deleteLoading) return;
              setIsDeleteDialogOpen(false);
              setDeleteResourceTarget(null);
            }
          }}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>确认删除资源</AlertDialogTitle>
              <AlertDialogDescription>
                删除后无法恢复，确定要删除资源
                <span className="font-semibold text-gray-900">
                  {deleteResourceTarget?.name}
                </span>
                吗？
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel 
                onClick={() => {
                  if (deleteLoading) return;
                  setIsDeleteDialogOpen(false);
                  setDeleteResourceTarget(null);
                }}
                disabled={deleteLoading}
              >
                取消
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={handleConfirmDelete}
                className="bg-red-600 hover:bg-red-700"
                disabled={deleteLoading}
              >
                {deleteLoading ? '删除中...' : '确认删除'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </AppLayout>
  );
}

