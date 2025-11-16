'use client';

import { useState, useEffect, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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
import { apiClient } from '@/service/apiClient';
import { handleApiError } from '@/service/apiClient';
import toast from 'react-hot-toast';
import AppLayout from '@/components/layout/AppLayout';
import { EnhancedPagination } from '@/components/ui/pagination';
import { 
  User, 
  Building, 
  Zap,
  Shield,
  Bot,
  RefreshCw
} from 'lucide-react';

type DigitalHumanItem = {
  id: string;
  name: string;
  avatar?: string;
  description?: string | null;
  type: 'personal' | 'business' | 'specialized' | 'system';
  status: 'active' | 'inactive' | 'maintenance';
  is_system_created: boolean;
  user: {
    id: string;
    username: string;
    email: string;
  };
  conversation_count: number;
  message_count: number;
  last_active_at?: string | null;
  agent_count?: number;
  created_at: string;
  updated_at: string;
};

const normalizeDigitalHuman = (dh: any): DigitalHumanItem => {
  return {
    id: dh?.id ? String(dh.id) : '',
    name: dh?.name ?? '',
    avatar: dh?.avatar ?? undefined,
    description: dh?.description ?? null,
    type: dh?.type ?? 'personal',
    status: dh?.status ?? 'inactive',
    is_system_created: dh?.is_system_created ?? dh?.isSystemCreated ?? false,
    user: dh?.user ?? {
      id: dh?.user_id ?? '',
      username: dh?.username ?? '',
      email: dh?.email ?? ''
    },
    conversation_count: dh?.conversation_count ?? dh?.conversationCount ?? 0,
    message_count: dh?.message_count ?? dh?.messageCount ?? 0,
    last_active_at: dh?.last_active_at ?? dh?.lastActiveAt ?? null,
    agent_count: dh?.agent_count ?? dh?.agentCount ?? 0,
    created_at: dh?.created_at ?? dh?.createdAt ?? '',
    updated_at: dh?.updated_at ?? dh?.updatedAt ?? ''
  };
};

export default function DigitalHumansPage() {
  const { user } = useAuthContext();
  const router = useRouter();
  const [digitalHumans, setDigitalHumans] = useState<DigitalHumanItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  
  // 搜索筛选状态
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  
  // 编辑状态
  const [editingDigitalHuman, setEditingDigitalHuman] = useState<DigitalHumanItem | null>(null);
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    status: 'active' as 'active' | 'inactive' | 'maintenance'
  });
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  
  // 删除状态
  const [deleteTarget, setDeleteTarget] = useState<DigitalHumanItem | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  // 检查用户是否有管理员权限
  useEffect(() => {
    if (user && user.currentRole !== 'admin') {
      router.push('/unauthorized');
    }
  }, [user, router]);

  // 获取数字人列表
  const fetchDigitalHumans = async (search?: string, status?: string, type?: string) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (status && status !== 'all') params.append('status', status);
      if (type && type !== 'all') params.append('type', type);
      
      const response = await apiClient.get(`/admin/digital-humans?${params.toString()}`);
      if (response.data?.success) {
        const normalized = Array.isArray(response.data.data) 
          ? response.data.data.map(normalizeDigitalHuman) 
          : [];
        setDigitalHumans(normalized);
      } else {
        throw new Error(response.data?.message || '获取数字人列表失败');
      }
    } catch (err) {
      const message = handleApiError(err, '获取数字人列表失败');
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  // 筛选数字人
  const filterDigitalHumans = () => {
    setCurrentPage(1);
    fetchDigitalHumans(
      searchText.trim() || undefined,
      statusFilter !== 'all' ? statusFilter : undefined,
      typeFilter !== 'all' ? typeFilter : undefined
    );
  };

  // 重置筛选条件
  const resetFilters = () => {
    setSearchText('');
    setStatusFilter('all');
    setTypeFilter('all');
    setCurrentPage(1);
    fetchDigitalHumans();
  };

  useEffect(() => {
    fetchDigitalHumans();
  }, []);

  useEffect(() => {
    const totalPages = Math.max(1, Math.ceil(digitalHumans.length / itemsPerPage));
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [digitalHumans, currentPage, itemsPerPage]);

  // 打开编辑对话框
  const handleOpenEdit = (dh: DigitalHumanItem) => {
    setEditingDigitalHuman(dh);
    setEditForm({
      name: dh.name,
      description: dh.description ?? '',
      status: dh.status
    });
    setEditError(null);
    setIsEditDialogOpen(true);
  };

  // 提交编辑
  const handleEditSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editingDigitalHuman) return;

    if (!editForm.name.trim()) {
      setEditError('数字人名称不能为空');
      return;
    }

    setEditLoading(true);
    setEditError(null);

    try {
      await apiClient.put(`/admin/digital-humans/${editingDigitalHuman.id}`, {
        name: editForm.name.trim(),
        description: editForm.description.trim() || undefined,
        status: editForm.status
      });
      
      toast.success('数字人更新成功');
      setIsEditDialogOpen(false);
      setEditingDigitalHuman(null);
      fetchDigitalHumans();
    } catch (err) {
      const message = handleApiError(err, '更新数字人失败');
      setEditError(message);
    } finally {
      setEditLoading(false);
    }
  };

  // 请求删除
  const handleRequestDelete = (dh: DigitalHumanItem) => {
    setDeleteTarget(dh);
    setIsDeleteDialogOpen(true);
  };

  // 删除数字人
  const handleDeleteDigitalHuman = async () => {
    if (!deleteTarget) return;

    setDeleteLoading(true);
    try {
      await apiClient.delete(`/admin/digital-humans/${deleteTarget.id}`);
      toast.success('数字人删除成功');
      setIsDeleteDialogOpen(false);
      setDeleteTarget(null);
      fetchDigitalHumans();
    } catch (err) {
      handleApiError(err, '删除数字人失败');
    } finally {
      setDeleteLoading(false);
    }
  };

  // 切换状态
  const handleToggleStatus = async (dh: DigitalHumanItem, newStatus: 'active' | 'inactive' | 'maintenance') => {
    try {
      await apiClient.put(`/admin/digital-humans/${dh.id}/status`, {
        status: newStatus
      });
      toast.success('状态更新成功');
      fetchDigitalHumans();
    } catch (err) {
      handleApiError(err, '更新状态失败');
    }
  };

  if (loading && digitalHumans.length === 0) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
      </div>
    );
  }

  // 类型样式映射
  const getTypeStyle = (type: string) => {
    const styles: Record<string, string> = {
      personal: 'bg-blue-100 text-blue-800',
      business: 'bg-purple-100 text-purple-800',
      specialized: 'bg-green-100 text-green-800',
      system: 'bg-orange-100 text-orange-800'
    };
    return styles[type] || 'bg-gray-100 text-gray-800';
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      personal: '个人助手',
      business: '商务助手',
      specialized: '专业助手',
      system: '系统助手'
    };
    return labels[type] || type;
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'personal':
        return <User className="h-4 w-4" />;
      case 'business':
        return <Building className="h-4 w-4" />;
      case 'specialized':
        return <Zap className="h-4 w-4" />;
      case 'system':
        return <Shield className="h-4 w-4" />;
      default:
        return <Bot className="h-4 w-4" />;
    }
  };

  // 分页逻辑
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentDigitalHumans = digitalHumans.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(digitalHumans.length / itemsPerPage);

  // 格式化日期
  const formatDate = (dateString?: string | null) => {
    if (!dateString) return '从未';
    try {
      return new Date(dateString).toLocaleString('zh-CN');
    } catch {
      return '无效日期';
    }
  };

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">数字人管理</h1>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchDigitalHumans()}
            className="flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>刷新</span>
          </Button>
        </div>

        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2 flex-1 min-w-[200px]">
              <Label htmlFor="search" className="w-24 flex-shrink-0">
                搜索:
              </Label>
              <Input
                id="search"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                placeholder="搜索数字人名称、描述"
                className="flex-1"
              />
            </div>
            <div className="flex items-center gap-2">
              <Label htmlFor="status" className="w-20 flex-shrink-0">
                状态:
              </Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger id="status" className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="active">活跃</SelectItem>
                  <SelectItem value="inactive">停用</SelectItem>
                  <SelectItem value="maintenance">维护中</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Label htmlFor="type" className="w-20 flex-shrink-0">
                类型:
              </Label>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger id="type" className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="personal">个人助手</SelectItem>
                  <SelectItem value="business">商务助手</SelectItem>
                  <SelectItem value="specialized">专业助手</SelectItem>
                  <SelectItem value="system">系统助手</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex space-x-2 flex-shrink-0">
              <Button variant="outline" onClick={resetFilters}>
                重置
              </Button>
              <Button className="bg-orange-500 hover:bg-orange-600" onClick={filterDigitalHumans}>
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
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  数字人信息
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  所属用户
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                  类型
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                  状态
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                  统计数据
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                  最后活跃
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {currentDigitalHumans.map((dh) => (
                <tr key={dh.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white font-semibold flex-shrink-0">
                        {dh.avatar ? (
                          <img
                            src={dh.avatar}
                            alt={dh.name}
                            className="w-full h-full rounded-full object-cover"
                          />
                        ) : (
                          dh.name.charAt(0).toUpperCase()
                        )}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium text-gray-900">{dh.name}</span>
                          {dh.is_system_created && (
                            <Shield className="h-4 w-4 text-blue-500" title="系统创建" />
                          )}
                        </div>
                        <p className="text-sm text-gray-500 truncate max-w-xs">
                          {dh.description || '-'}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <div className="text-gray-900">{dh.user.username}</div>
                    <div className="text-gray-500">{dh.user.email}</div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${getTypeStyle(dh.type)}`}>
                      {getTypeIcon(dh.type)}
                      {getTypeLabel(dh.type)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      dh.status === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : dh.status === 'maintenance'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {dh.status === 'active' ? '活跃' : dh.status === 'maintenance' ? '维护中' : '停用'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center text-sm text-gray-600">
                    <div className="space-y-1">
                      <div>会话: {dh.conversation_count}</div>
                      <div>消息: {dh.message_count}</div>
                      <div>智能体: {dh.agent_count || 0}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center text-sm text-gray-500">
                    {formatDate(dh.last_active_at)}
                  </td>
                  <td className="px-6 py-4 text-right text-sm">
                    <div className="flex justify-end space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleOpenEdit(dh)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        编辑
                      </Button>
                      {dh.status !== 'active' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleStatus(dh, 'active')}
                          className="text-green-600 hover:text-green-800"
                        >
                          激活
                        </Button>
                      )}
                      {dh.status !== 'inactive' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleStatus(dh, 'inactive')}
                          className="text-gray-600 hover:text-gray-800"
                        >
                          停用
                        </Button>
                      )}
                      {dh.status !== 'maintenance' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleStatus(dh, 'maintenance')}
                          className="text-yellow-600 hover:text-yellow-800"
                        >
                          维护
                        </Button>
                      )}
                      {!dh.is_system_created && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRequestDelete(dh)}
                          className="text-red-600 hover:text-red-800"
                        >
                          删除
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}

              {digitalHumans.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-sm text-gray-500">
                    暂无数字人数据
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {digitalHumans.length > 0 && (
          <div className="mt-6">
            <EnhancedPagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={digitalHumans.length}
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
      </div>

      {/* 编辑对话框 */}
      <Dialog
        open={isEditDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            if (editLoading) return;
            setIsEditDialogOpen(false);
            setEditingDigitalHuman(null);
            setEditError(null);
            return;
          }
          setIsEditDialogOpen(true);
        }}
      >
        <DialogContent className="sm:max-w-md bg-white">
          <DialogHeader>
            <DialogTitle>编辑数字人</DialogTitle>
            <DialogDescription>
              修改数字人的名称、描述和状态
            </DialogDescription>
          </DialogHeader>
          {editError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-500">
              {editError}
            </div>
          )}
          <form onSubmit={handleEditSubmit} className="space-y-4">
            <div>
              <Label htmlFor="editName">数字人名称 *</Label>
              <Input
                id="editName"
                value={editForm.name}
                onChange={(e) => setEditForm((prev) => ({ ...prev, name: e.target.value }))}
                disabled={editLoading}
                placeholder="数字人名称"
              />
            </div>
            <div>
              <Label htmlFor="editDescription">描述</Label>
              <Textarea
                id="editDescription"
                value={editForm.description}
                onChange={(e) => setEditForm((prev) => ({ ...prev, description: e.target.value }))}
                rows={3}
                disabled={editLoading}
                placeholder="可选: 数字人的详细描述"
              />
            </div>
            <div>
              <Label htmlFor="editStatus">状态</Label>
              <Select
                value={editForm.status}
                onValueChange={(value: 'active' | 'inactive' | 'maintenance') => 
                  setEditForm((prev) => ({ ...prev, status: value }))
                }
                disabled={editLoading}
              >
                <SelectTrigger id="editStatus">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">活跃</SelectItem>
                  <SelectItem value="inactive">停用</SelectItem>
                  <SelectItem value="maintenance">维护中</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  if (editLoading) return;
                  setIsEditDialogOpen(false);
                  setEditingDigitalHuman(null);
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

      {/* 删除确认对话框 */}
      <AlertDialog
        open={isDeleteDialogOpen}
        onOpenChange={(open) => {
          if (open) {
            setIsDeleteDialogOpen(true);
          } else {
            if (deleteLoading) return;
            setIsDeleteDialogOpen(false);
            setDeleteTarget(null);
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除数字人</AlertDialogTitle>
            <AlertDialogDescription>
              删除后无法恢复，确定要删除数字人
              <span className="font-semibold text-gray-900">
                {deleteTarget?.name}
              </span>
              吗？
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel 
              onClick={() => {
                if (deleteLoading) return;
                setIsDeleteDialogOpen(false);
                setDeleteTarget(null);
              }}
              disabled={deleteLoading}
            >
              取消
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteDigitalHuman}
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
