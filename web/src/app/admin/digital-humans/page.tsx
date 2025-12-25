'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { InfoTooltip } from '@/components/ui/info-tooltip';
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
import { apiClient, ApiClientError } from '@/service/apiClient';
import toast from 'react-hot-toast';
import AppLayout from '@/components/layout/AppLayout';
import { EnhancedPagination } from '@/components/ui/pagination';
import { userService } from '@/service/userService';
import type { User as AppUser } from '@/types/auth';
import type { DigitalHuman, CreateDigitalHumanRequest, UpdateDigitalHumanRequest } from '@/types/digital-human';
import DigitalHumanForm from '@/components/profile/DigitalHumanForm';
import { UserCombobox } from '@/components/ui/user-combobox';
import { 
  User, 
  Building, 
  Zap,
  Shield,
  Bot,
  RefreshCw,
  Info
} from 'lucide-react';
import { AvatarCircle } from '@/components/ui/AvatarCircle';

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

const parseFastApiDetailMessage = (detail: unknown): string | null => {
  if (!Array.isArray(detail) || detail.length === 0) return null;
  const first = detail[0] as any;
  const msg = typeof first?.msg === 'string' ? first.msg : null;
  return msg;
};

const getReadableErrorMessage = async (err: unknown, fallback: string): Promise<string> => {
  if (err instanceof ApiClientError) {
    return err.message || fallback;
  }

  if (err instanceof Response) {
    try {
      const data = await err.json();
      if (typeof data?.message === 'string' && data.message) return data.message;
      const detailMsg = parseFastApiDetailMessage((data as any)?.detail);
      if (detailMsg) return detailMsg;
    } catch {
      // ignore
    }
    return fallback;
  }

  if (err instanceof Error && err.message) return err.message;
  return fallback;
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

  // 用户列表（用于管理员分配/更改所属用户）
  const [users, setUsers] = useState<AppUser[]>([]);
  const [userLoading, setUserLoading] = useState(false);
  
  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);
  
  // 搜索筛选状态
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  
  // 编辑状态（复用个人中心数字人设定表单）
  const [editingDigitalHumanId, setEditingDigitalHumanId] = useState<string | null>(null);
  const [editingDigitalHumanDetail, setEditingDigitalHumanDetail] = useState<DigitalHuman | null>(null);
  const [editDetailLoading, setEditDetailLoading] = useState(false);
  const [editUserId, setEditUserId] = useState('');
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

  // 创建状态（复用个人中心数字人设定表单）
  const [createUserId, setCreateUserId] = useState('');
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  
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

      // apiClient 内部会将后端 ApiResponse<T> 解包为 T（见其他 hooks 的用法）
      const query = params.toString();
      const url = query ? `/admin/digital-humans/?${query}` : '/admin/digital-humans/';
      const response = await apiClient.get<any[]>(url);

      const list = Array.isArray(response.data) ? response.data : [];
      const normalized = list.map(normalizeDigitalHuman);
      setDigitalHumans(normalized);
    } catch (err) {
      const message = await getReadableErrorMessage(err, '获取数字人列表失败');
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

  const fetchUsers = async (search?: string) => {
    setUserLoading(true);
    try {
      const result = await userService.getUsers({
        skip: 0,
        limit: 100,
        search: search?.trim() || undefined,
      });
      setUsers(result.users);
    } catch (err) {
      const message = err instanceof Error ? err.message : '获取用户列表失败';
      toast.error(message);
    } finally {
      setUserLoading(false);
    }
  };

  useEffect(() => {
    const totalPages = Math.max(1, Math.ceil(digitalHumans.length / itemsPerPage));
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [digitalHumans, currentPage, itemsPerPage]);

  // 打开编辑对话框（复用个人中心数字人设定表单）
  const handleOpenEdit = async (dh: DigitalHumanItem) => {
    setEditError(null);
    setEditingDigitalHumanId(dh.id);
    setEditUserId(dh.user?.id ?? '');
    setEditingDigitalHumanDetail(null);
    setIsEditDialogOpen(true);

    if (users.length === 0) {
      void fetchUsers();
    }

    setEditDetailLoading(true);
    try {
      const resp = await apiClient.get<DigitalHuman>(
        `/admin/digital-humans/${dh.id}`,
        {},
        { silent: true },
      );
      setEditingDigitalHumanDetail(resp.data);
    } catch (err) {
      const message = await getReadableErrorMessage(err, '获取数字人详情失败');
      setEditError(message);
      toast.error(message);
    } finally {
      setEditDetailLoading(false);
    }
  };

  const handleOpenCreate = () => {
    setCreateError(null);
    setCreateUserId('');
    setIsCreateDialogOpen(true);
    if (users.length === 0) {
      void fetchUsers();
    }
  };

  const handleAdminCreate = async (data: CreateDigitalHumanRequest | UpdateDigitalHumanRequest) => {
    if (!createUserId) {
      throw new Error('请选择所属用户');
    }
    setCreateLoading(true);
    setCreateError(null);
    try {
      await apiClient.post(
        `/admin/digital-humans/`,
        {
          user_id: createUserId,
          ...data,
        },
        { silent: true },
      );
      setIsCreateDialogOpen(false);
      setCreateUserId('');
      await fetchDigitalHumans();
    } catch (err) {
      const message = await getReadableErrorMessage(err, '创建数字人失败');
      setCreateError(message);
      throw new Error(message);
    } finally {
      setCreateLoading(false);
    }
  };

  const handleAdminUpdate = async (data: CreateDigitalHumanRequest | UpdateDigitalHumanRequest) => {
    if (!editingDigitalHumanId) return;
    if (!editUserId) {
      throw new Error('请选择所属用户');
    }
    setEditLoading(true);
    setEditError(null);
    try {
      const payload: Record<string, unknown> = {
        user_id: editUserId,
        ...data,
      };
      // 后端管理员更新接口当前不支持修改 type，避免误导
      delete payload.type;

      await apiClient.put(
        `/admin/digital-humans/${editingDigitalHumanId}`,
        payload,
        { silent: true },
      );

      // 保存成功后回拉一次详情并回填，避免再次打开编辑看到旧头像
      const refreshed = await apiClient.get<DigitalHuman>(
        `/admin/digital-humans/${editingDigitalHumanId}`,
        {},
        { silent: true },
      );
      setEditingDigitalHumanDetail(refreshed.data);

      await fetchDigitalHumans();
    } catch (err) {
      const message = await getReadableErrorMessage(err, '更新数字人失败');
      setEditError(message);
      throw new Error(message);
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
      await apiClient.delete(`/admin/digital-humans/${deleteTarget.id}`, {}, { silent: true });
      toast.success('数字人删除成功');
      setIsDeleteDialogOpen(false);
      setDeleteTarget(null);
      fetchDigitalHumans();
    } catch (err) {
      const message = await getReadableErrorMessage(err, '删除数字人失败');
      toast.error(message);
    } finally {
      setDeleteLoading(false);
    }
  };

  // 切换状态
  const handleToggleStatus = async (dh: DigitalHumanItem, newStatus: 'active' | 'inactive' | 'maintenance') => {
    try {
      await apiClient.put(
        `/admin/digital-humans/${dh.id}/status`,
        { status: newStatus },
        { silent: true },
      );
      toast.success('状态更新成功');
      fetchDigitalHumans();
    } catch (err) {
      const message = await getReadableErrorMessage(err, '更新状态失败');
      toast.error(message);
    }
  };

  if (loading && digitalHumans.length === 0) {
    return (
      <AppLayout requiredRole={user?.currentRole}>
        <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
        </div>
      </AppLayout>
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
          <div className="flex items-center gap-2">
            <Button
              className="bg-orange-500 hover:bg-orange-600"
              size="sm"
              onClick={handleOpenCreate}
            >
              + 创建数字人
            </Button>
          </div>
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
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    filterDigitalHumans();
                  }
                }}
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
                      <AvatarCircle
                        name={dh.name}
                        avatar={dh.avatar}
                        sizeClassName="w-10 h-10"
                        className="flex-shrink-0"
                      />
                      <div className="min-w-0">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium text-gray-900">{dh.name}</span>
                          {dh.is_system_created && (
                            <span title="系统创建">
                              <Shield className="h-4 w-4 text-blue-500" />
                            </span>
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
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRequestDelete(dh)}
                        className="text-red-600 hover:text-red-800"
                      >
                        删除
                      </Button>
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

      {/* 编辑抽屉 */}
      <Sheet
        open={isEditDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            if (editLoading) return;
            setIsEditDialogOpen(false);
            setEditingDigitalHumanId(null);
            setEditingDigitalHumanDetail(null);
            setEditError(null);
            return;
          }
          setIsEditDialogOpen(true);
        }}
      >
        <SheetContent side="right" className="w-[94vw] sm:w-[960px] lg:w-[1100px] max-h-screen overflow-y-auto">
          <SheetHeader>
            <div className="flex items-center gap-2">
              <SheetTitle>编辑数字人</SheetTitle>
              <InfoTooltip content="修改数字人的名称、描述、状态及所属用户" />
            </div>
          </SheetHeader>
          {editError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-500">
              {editError}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <Label htmlFor="editUser">所属用户 *</Label>
              <UserCombobox
                value={editUserId}
                onValueChange={setEditUserId}
                users={users}
                onSearch={fetchUsers}
                isLoading={userLoading}
                disabled={editLoading}
                placeholder="选择所属用户..."
                searchPlaceholder="搜索用户名或邮箱..."
                emptyText="未找到匹配的用户"
                className="mt-2"
              />
            </div>

            {editDetailLoading && (
              <div className="flex items-center justify-center py-10">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500" />
              </div>
            )}

            {!editDetailLoading && editingDigitalHumanDetail && (
              <DigitalHumanForm
                digitalHuman={editingDigitalHumanDetail}
                onSubmit={handleAdminUpdate}
                onCancel={() => {
                  if (editLoading) return;
                  setIsEditDialogOpen(false);
                  setEditingDigitalHumanId(null);
                  setEditingDigitalHumanDetail(null);
                  setEditError(null);
                }}
              />
            )}

            {!editDetailLoading && !editingDigitalHumanDetail && (
              <div className="py-10 text-center text-sm text-gray-500">
                未加载到数字人详情
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>

      {/* 创建抽屉 */}
      <Sheet
        open={isCreateDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            if (createLoading) return;
            setIsCreateDialogOpen(false);
            setCreateError(null);
            setCreateUserId('');
            return;
          }
          setIsCreateDialogOpen(true);
        }}
      >
        <SheetContent side="right" className="w-[94vw] sm:w-[960px] lg:w-[1100px] max-h-screen overflow-y-auto">
          <SheetHeader>
            <div className="flex items-center gap-2">
              <SheetTitle>创建数字人</SheetTitle>
              <InfoTooltip content="管理员可创建系统助手类型数字人，并分配所属用户" />
            </div>
          </SheetHeader>
          {createError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-500">
              {createError}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <Label htmlFor="createUser">所属用户 *</Label>
              <UserCombobox
                value={createUserId}
                onValueChange={setCreateUserId}
                users={users}
                onSearch={fetchUsers}
                isLoading={userLoading}
                disabled={createLoading}
                placeholder="选择所属用户..."
                searchPlaceholder="搜索用户名或邮箱..."
                emptyText="未找到匹配的用户"
                className="mt-2"
              />
            </div>

            <DigitalHumanForm
              allowSystemType={true}
              onSubmit={handleAdminCreate}
              onCancel={() => {
                if (createLoading) return;
                setIsCreateDialogOpen(false);
                setCreateError(null);
                setCreateUserId('');
              }}
            />
          </div>
        </SheetContent>
      </Sheet>

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
