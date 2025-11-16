'use client';

import { useState, useEffect, useRef, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
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
import { Tenant } from '@/types/auth';
import toast from 'react-hot-toast';
import AppLayout from '@/components/layout/AppLayout';
import { EnhancedPagination } from '@/components/ui/pagination';

const normalizeTenant = (tenant: any): Tenant => {
  const id = tenant?.id ? String(tenant.id) : '';
  return {
    id,
    name: tenant?.name ?? '',
    displayName: tenant?.displayName ?? tenant?.display_name ?? tenant?.name ?? '',
    description: tenant?.description ?? null,
    tenantType: tenant?.tenantType ?? tenant?.tenant_type ?? 'standard',
    status: tenant?.status ?? 'active',
    isSystem: tenant?.isSystem ?? tenant?.is_system ?? false,
    isAdmin: tenant?.isAdmin ?? tenant?.is_admin ?? false,
    priority: typeof tenant?.priority === 'number' ? tenant.priority : Number(tenant?.priority ?? 0),
    encryptedPubKey: tenant?.encryptedPubKey ?? tenant?.encrypted_pub_key ?? null,
    contactName: tenant?.contactName ?? tenant?.contact_name ?? null,
    contactEmail: tenant?.contactEmail ?? tenant?.contact_email ?? null,
    contactPhone: tenant?.contactPhone ?? tenant?.contact_phone ?? null,
    createdAt: tenant?.createdAt ?? tenant?.created_at ?? '',
    updatedAt: tenant?.updatedAt ?? tenant?.updated_at ?? '',
  };
};

export default function TenantsPage() {
  const { user } = useAuthContext();
  const router = useRouter();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [tenantName, setTenantName] = useState('');
  const [tenantDisplayName, setTenantDisplayName] = useState('');
  const [tenantDescription, setTenantDescription] = useState('');
  const [tenantType, setTenantType] = useState<'system' | 'standard' | 'premium' | 'enterprise'>('standard');
  const [tenantStatus, setTenantStatus] = useState<'active' | 'inactive' | 'suspended' | 'pending'>('active');
  const [tenantIsSystem, setTenantIsSystem] = useState(false);
  const [tenantIsAdmin, setTenantIsAdmin] = useState(false);
  const [tenantPriority, setTenantPriority] = useState<number>(0);
  const [tenantContactName, setTenantContactName] = useState('');
  const [tenantContactEmail, setTenantContactEmail] = useState('');
  const [tenantContactPhone, setTenantContactPhone] = useState('');
  const [tenantEncryptedPubKey, setTenantEncryptedPubKey] = useState('');
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);
  const [searchText, setSearchText] = useState('');
  const [editingTenant, setEditingTenant] = useState<Tenant | null>(null);
  const [editForm, setEditForm] = useState({
    name: '',
    displayName: '',
    description: '',
    tenantType: 'standard' as 'system' | 'standard' | 'premium' | 'enterprise',
    status: 'active' as 'active' | 'inactive' | 'suspended' | 'pending',
    isSystem: false,
    isAdmin: false,
    priority: 0,
    encryptedPubKey: '',
    contactName: '',
    contactEmail: '',
    contactPhone: ''
  });
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Tenant | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const createNameRef = useRef(tenantName);

  useEffect(() => {
    createNameRef.current = tenantName;
  }, [tenantName]);

  function resetCreateForm() {
    setTenantName('');
    setTenantDisplayName('');
    setTenantDescription('');
    setTenantType('standard');
    setTenantStatus('active');
    setTenantIsSystem(false);
    setTenantIsAdmin(false);
    setTenantPriority(0);
    setTenantContactName('');
    setTenantContactEmail('');
    setTenantContactPhone('');
    setTenantEncryptedPubKey('');
    setFormError(null);
  }

  const handleCreateNameChange = (value: string) => {
    const previousName = createNameRef.current.trim();
    setTenantName(value);
    setTenantDisplayName((prev) => {
      const trimmedPrev = prev.trim();
      if (!trimmedPrev || trimmedPrev === previousName) {
        return value;
      }
      return prev;
    });
  };

  // 检查用户是否有管理员权限
  useEffect(() => {
    if (user && user.currentRole !== 'admin') {
      router.push('/unauthorized');
    }
  }, [user, router]);

  // 获取租户列表
  const fetchTenants = async (search?: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await permissionService.getTenants();
      let filtered = data.map(normalizeTenant);
      
      // 前端搜索
      if (search && search.trim()) {
        const searchLower = search.toLowerCase();
        filtered = filtered.filter((tenant) =>
          tenant.name.toLowerCase().includes(searchLower) ||
          (tenant.displayName && tenant.displayName.toLowerCase().includes(searchLower)) ||
          (tenant.description && tenant.description.toLowerCase().includes(searchLower))
        );
      }
      
      setTenants(filtered);
    } catch (err) {
      const message = handleApiError(err, '获取租户列表失败');
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  // 筛选租户
  const filterTenants = () => {
    setCurrentPage(1);
    fetchTenants(searchText.trim() || undefined);
  };

  // 重置筛选条件
  const resetFilters = () => {
    setSearchText('');
    setCurrentPage(1);
    fetchTenants();
  };

  useEffect(() => {
    fetchTenants();
  }, []);

  useEffect(() => {
    const totalPages = Math.max(1, Math.ceil(tenants.length / itemsPerPage));
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [tenants, currentPage, itemsPerPage]);

  // 创建租户
  const handleCreateTenant = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!tenantName.trim()) {
      setFormError('租户名称不能为空');
      return;
    }
    
    setFormLoading(true);
    setFormError(null);
    
    try {
      const nextDisplayName = tenantDisplayName.trim();
      await permissionService.createTenant({
        name: tenantName.trim(),
        displayName: nextDisplayName || undefined,
        description: tenantDescription.trim() || undefined,
        tenantType,
        status: tenantStatus,
        isSystem: tenantIsSystem,
        isAdmin: tenantIsAdmin,
        priority: tenantPriority,
        // 加密公钥：始终传递，即使是空字符串（用于清空）
        encryptedPubKey: tenantEncryptedPubKey.trim(),
        contactName: tenantContactName.trim() || undefined,
        contactEmail: tenantContactEmail.trim() || undefined,
        contactPhone: tenantContactPhone.trim() || undefined
      });
      toast.success('租户创建成功');
      
      resetCreateForm();
      setIsCreateDialogOpen(false);
      fetchTenants();
    } catch (err) {
      const message = handleApiError(err, '创建租户失败');
      setFormError(message);
    } finally {
      setFormLoading(false);
    }
  };

  const handleOpenEdit = (tenant: Tenant) => {
    setEditingTenant(tenant);
    setEditForm({
      name: tenant.name,
      displayName: tenant.displayName ?? tenant.name,
      description: tenant.description ?? '',
      tenantType: tenant.tenantType,
      status: tenant.status,
      isSystem: tenant.isSystem ?? false,
      isAdmin: tenant.isAdmin ?? false,
      priority: tenant.priority ?? 0,
      encryptedPubKey: tenant.encryptedPubKey ?? '',
      contactName: tenant.contactName ?? '',
      contactEmail: tenant.contactEmail ?? '',
      contactPhone: tenant.contactPhone ?? ''
    });
    setEditError(null);
    setIsEditDialogOpen(true);
  };

  const handleEditSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editingTenant) {
      return;
    }

    const nextName = editForm.name.trim();
    if (!nextName) {
      setEditError('租户名称不能为空');
      return;
    }
    const nextDisplayName = editForm.displayName.trim();

    setEditLoading(true);
    setEditError(null);

    try {
      const payload: any = {};

      if (!editingTenant.isSystem) {
        payload.name = nextName;
      }
      payload.displayName = nextDisplayName || undefined;
      payload.description = editForm.description.trim() || undefined;
      payload.tenantType = editForm.tenantType;
      payload.status = editForm.status;
      payload.isSystem = editForm.isSystem;
      payload.isAdmin = editForm.isAdmin;
      payload.priority = editForm.priority;
      // 加密公钥允许为空字符串来清空
      payload.encryptedPubKey = editForm.encryptedPubKey.trim();
      payload.contactName = editForm.contactName.trim() || undefined;
      payload.contactEmail = editForm.contactEmail.trim() || undefined;
      payload.contactPhone = editForm.contactPhone.trim() || undefined;

      await permissionService.updateTenant(editingTenant.id, payload);
      toast.success('租户更新成功');
      setIsEditDialogOpen(false);
      setEditingTenant(null);
      fetchTenants();
    } catch (err) {
      const message = handleApiError(err, '更新租户失败');
      setEditError(message);
    } finally {
      setEditLoading(false);
    }
  };

  const handleRequestDelete = (tenant: Tenant) => {
    setDeleteTarget(tenant);
    setIsDeleteDialogOpen(true);
  };

  const handleDeleteTenant = async () => {
    if (!deleteTarget) {
      return;
    }

    setDeleteLoading(true);
    try {
      await permissionService.deleteTenant(deleteTarget.id);
      toast.success('租户删除成功');
      setIsDeleteDialogOpen(false);
      setDeleteTarget(null);
      fetchTenants();
    } catch (err) {
      handleApiError(err, '删除租户失败');
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

  if (loading && tenants.length === 0) {
    return (
      <AppLayout requiredRole={user?.currentRole}>
        <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
        </div>
      </AppLayout>
    );
  }

  const getTenantStyle = (name: string) => {
    const styles: Record<string, string> = {
      system: 'bg-red-100 text-red-800',
      default: 'bg-blue-100 text-blue-800'
    };
    return styles[name] || 'bg-gray-100 text-gray-800';
  };
  
  // 分页逻辑
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentTenants = tenants.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(tenants.length / itemsPerPage);

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">租户管理</h1>
          <Button
            onClick={() => {
              setFormError(null);
              setIsCreateDialogOpen(true);
            }}
            className="bg-orange-500 hover:bg-orange-600"
          >
            创建租户
          </Button>
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
                    filterTenants();
                  }
                }}
                placeholder="搜索租户名称,显示名称,描述"
                className="flex-1"
              />
            </div>
            <div className="flex space-x-2 flex-shrink-0">
              <Button variant="outline" onClick={resetFilters}>
                重置
              </Button>
              <Button className="bg-orange-500 hover:bg-orange-600" onClick={filterTenants}>
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
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  租户名称
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
                  状态
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                  系统租户
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                  管理员租户
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                  优先级
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {currentTenants.map((tenant) => (
                <tr key={tenant.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {tenant.id}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                    <span className={`rounded-full ${getTenantStyle(tenant.name)} px-3 py-1 text-sm font-medium`}>
                      {tenant.name}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    <div className="flex items-center space-x-2">
                      <span>{tenant.displayName || '-'}</span>
                      {tenant.isSystem && (
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                          系统租户
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {tenant.description || '-'}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center text-sm">
                    <Badge variant="outline">
                      {tenant.tenantType === 'system' ? '系统' :
                       tenant.tenantType === 'standard' ? '标准' :
                       tenant.tenantType === 'premium' ? '高级' : '企业'}
                    </Badge>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center text-sm">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      tenant.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : tenant.status === 'inactive'
                        ? 'bg-gray-100 text-gray-800'
                        : tenant.status === 'suspended'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {tenant.status === 'active' ? '激活' :
                       tenant.status === 'inactive' ? '停用' :
                       tenant.status === 'suspended' ? '暂停' : '待激活'}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center text-sm">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      tenant.isSystem 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {tenant.isSystem ? '是' : '否'}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center text-sm">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      tenant.isAdmin 
                        ? 'bg-purple-100 text-purple-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {tenant.isAdmin ? '是' : '否'}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center text-sm font-medium text-gray-900">
                    {tenant.priority ?? 0}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                    <div className="flex justify-end space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleOpenEdit(tenant)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        编辑
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRequestDelete(tenant)}
                        className="text-red-600 hover:text-red-800"
                        disabled={tenant.isSystem}
                        title={tenant.isSystem ? '系统租户不可删除' : undefined}
                      >
                        删除
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}

              {tenants.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-6 py-4 text-center text-sm text-gray-500">
                    暂无租户数据
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {tenants.length > 0 && (
          <div className="mt-6">
            <EnhancedPagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={tenants.length}
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
        <DialogContent className="sm:max-w-2xl bg-white max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>创建租户</DialogTitle>
            <DialogDescription>
              创建一个新的租户，设置租户名称、显示名称、描述和其他属性
            </DialogDescription>
          </DialogHeader>
          {formError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-500">
              {formError}
            </div>
          )}
          <form onSubmit={handleCreateTenant} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="createTenantName">租户名称 *</Label>
                <Input
                  id="createTenantName"
                  value={tenantName}
                  onChange={(e) => handleCreateNameChange(e.target.value)}
                  disabled={formLoading}
                  placeholder="例如: tenant-001"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="createTenantDisplayName">显示名称</Label>
                <Input
                  id="createTenantDisplayName"
                  value={tenantDisplayName}
                  onChange={(e) => setTenantDisplayName(e.target.value)}
                  disabled={formLoading}
                  placeholder="用于界面展示的名称，默认与租户名称一致"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="createTenantDescription">租户描述</Label>
              <Textarea
                id="createTenantDescription"
                value={tenantDescription}
                onChange={(e) => setTenantDescription(e.target.value)}
                disabled={formLoading}
                rows={3}
                placeholder="可选: 租户的详细描述"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="createTenantType">租户类型</Label>
                <Select
                  value={tenantType}
                  onValueChange={(value: any) => setTenantType(value)}
                  disabled={formLoading}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="system">系统</SelectItem>
                    <SelectItem value="standard">标准</SelectItem>
                    <SelectItem value="premium">高级</SelectItem>
                    <SelectItem value="enterprise">企业</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="createTenantStatus">租户状态</Label>
                <Select
                  value={tenantStatus}
                  onValueChange={(value: any) => setTenantStatus(value)}
                  disabled={formLoading}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">激活</SelectItem>
                    <SelectItem value="inactive">停用</SelectItem>
                    <SelectItem value="suspended">暂停</SelectItem>
                    <SelectItem value="pending">待激活</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="createTenantContactName">联系人姓名</Label>
                <Input
                  id="createTenantContactName"
                  value={tenantContactName}
                  onChange={(e) => setTenantContactName(e.target.value)}
                  disabled={formLoading}
                  placeholder="联系人姓名"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="createTenantContactEmail">联系人邮箱</Label>
                <Input
                  id="createTenantContactEmail"
                  type="email"
                  value={tenantContactEmail}
                  onChange={(e) => setTenantContactEmail(e.target.value)}
                  disabled={formLoading}
                  placeholder="联系人邮箱"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="createTenantContactPhone">联系人电话</Label>
                <Input
                  id="createTenantContactPhone"
                  value={tenantContactPhone}
                  onChange={(e) => setTenantContactPhone(e.target.value)}
                  disabled={formLoading}
                  placeholder="联系人电话"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="createTenantIsSystem">是否系统租户</Label>
                <Switch
                  id="createTenantIsSystem"
                  checked={tenantIsSystem}
                  onCheckedChange={setTenantIsSystem}
                  disabled={formLoading}
                />
              </div>
              <p className="text-xs text-gray-500">系统租户通常由系统自动创建，请谨慎设置</p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="createTenantIsAdmin">是否管理员租户</Label>
                <Switch
                  id="createTenantIsAdmin"
                  checked={tenantIsAdmin}
                  onCheckedChange={setTenantIsAdmin}
                  disabled={formLoading}
                />
              </div>
              <p className="text-xs text-gray-500">管理员租户拥有系统管理权限</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="createTenantPriority">租户优先级</Label>
              <Input
                id="createTenantPriority"
                type="number"
                value={tenantPriority}
                onChange={(e) => setTenantPriority(Number(e.target.value) || 0)}
                disabled={formLoading}
                placeholder="数字越大优先级越高"
                min="0"
              />
              <p className="text-xs text-gray-500">用于租户排序和判断，数字越大优先级越高</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="createTenantEncryptedPubKey">加密公钥</Label>
              <Textarea
                id="createTenantEncryptedPubKey"
                value={tenantEncryptedPubKey}
                onChange={(e) => setTenantEncryptedPubKey(e.target.value)}
                disabled={formLoading}
                rows={4}
                placeholder="可选: 加密公钥（用于安全通信）"
              />
              <p className="text-xs text-gray-500">用于租户数据加密的公钥，通常由系统自动生成或手动配置</p>
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
                {formLoading ? '创建中...' : '创建租户'}
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
            setEditingTenant(null);
            setEditError(null);
            return;
          }

          if (!editingTenant) {
            setIsEditDialogOpen(false);
            return;
          }

          setIsEditDialogOpen(true);
        }}
      >
        <DialogContent className="sm:max-w-2xl bg-white max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>编辑租户</DialogTitle>
            <DialogDescription>
              修改租户的显示名称、描述和其他属性信息
            </DialogDescription>
          </DialogHeader>
          {editError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-500">
              {editError}
            </div>
          )}
          <form onSubmit={handleEditSubmit} className="space-y-4">
            <div>
              <Label htmlFor="editTenantName">租户名称 *</Label>
              <Input
                id="editTenantName"
                value={editForm.name}
                onChange={(e) => setEditForm((prev) => ({ ...prev, name: e.target.value }))}
                disabled={editLoading || editingTenant?.isSystem}
                placeholder="租户标识"
              />
              {editingTenant?.isSystem && (
                <p className="mt-1 text-xs text-gray-500">系统租户名称不可修改</p>
              )}
            </div>
            <div>
              <Label htmlFor="editTenantDisplayName">显示名称</Label>
              <Input
                id="editTenantDisplayName"
                value={editForm.displayName}
                onChange={(e) => setEditForm((prev) => ({ ...prev, displayName: e.target.value }))}
                disabled={editLoading}
                placeholder="用于界面展示的名称"
              />
            </div>
            <div>
              <Label htmlFor="editTenantDescription">租户描述</Label>
              <Textarea
                id="editTenantDescription"
                value={editForm.description}
                onChange={(e) => setEditForm((prev) => ({ ...prev, description: e.target.value }))}
                rows={3}
                disabled={editLoading}
                placeholder="可选: 租户的详细描述"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="editTenantType">租户类型</Label>
                <Select
                  value={editForm.tenantType}
                  onValueChange={(value: any) => setEditForm((prev) => ({ ...prev, tenantType: value }))}
                  disabled={editLoading}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="system">系统</SelectItem>
                    <SelectItem value="standard">标准</SelectItem>
                    <SelectItem value="premium">高级</SelectItem>
                    <SelectItem value="enterprise">企业</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="editTenantStatus">租户状态</Label>
                <Select
                  value={editForm.status}
                  onValueChange={(value: any) => setEditForm((prev) => ({ ...prev, status: value }))}
                  disabled={editLoading}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">激活</SelectItem>
                    <SelectItem value="inactive">停用</SelectItem>
                    <SelectItem value="suspended">暂停</SelectItem>
                    <SelectItem value="pending">待激活</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="editTenantContactName">联系人姓名</Label>
                <Input
                  id="editTenantContactName"
                  value={editForm.contactName}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, contactName: e.target.value }))}
                  disabled={editLoading}
                  placeholder="联系人姓名"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="editTenantContactEmail">联系人邮箱</Label>
                <Input
                  id="editTenantContactEmail"
                  type="email"
                  value={editForm.contactEmail}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, contactEmail: e.target.value }))}
                  disabled={editLoading}
                  placeholder="联系人邮箱"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="editTenantContactPhone">联系人电话</Label>
                <Input
                  id="editTenantContactPhone"
                  value={editForm.contactPhone}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, contactPhone: e.target.value }))}
                  disabled={editLoading}
                  placeholder="联系人电话"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="editTenantEncryptedPubKey">加密公钥</Label>
              <Textarea
                id="editTenantEncryptedPubKey"
                value={editForm.encryptedPubKey}
                onChange={(e) => setEditForm((prev) => ({ ...prev, encryptedPubKey: e.target.value }))}
                disabled={editLoading}
                rows={4}
                placeholder="可选: 加密公钥（用于安全通信）"
              />
              <p className="text-xs text-gray-500">用于租户数据加密的公钥，通常由系统自动生成或手动配置</p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="editTenantIsSystem">是否系统租户</Label>
                <Switch
                  id="editTenantIsSystem"
                  checked={editForm.isSystem}
                  onCheckedChange={(checked) => setEditForm((prev) => ({ ...prev, isSystem: checked }))}
                  disabled={editLoading || editingTenant?.isSystem}
                />
              </div>
              <p className="text-xs text-gray-500">
                {editingTenant?.isSystem ? '系统租户状态不可修改' : '系统租户通常由系统自动创建'}
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="editTenantIsAdmin">是否管理员租户</Label>
                <Switch
                  id="editTenantIsAdmin"
                  checked={editForm.isAdmin}
                  onCheckedChange={(checked) => setEditForm((prev) => ({ ...prev, isAdmin: checked }))}
                  disabled={editLoading}
                />
              </div>
              <p className="text-xs text-gray-500">管理员租户拥有系统管理权限</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="editTenantPriority">租户优先级</Label>
              <Input
                id="editTenantPriority"
                type="number"
                value={editForm.priority}
                onChange={(e) => setEditForm((prev) => ({ ...prev, priority: Number(e.target.value) || 0 }))}
                disabled={editLoading}
                placeholder="数字越大优先级越高"
                min="0"
              />
              <p className="text-xs text-gray-500">用于租户排序和判断，数字越大优先级越高</p>
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
                  setEditingTenant(null);
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
            <AlertDialogTitle>确认删除租户</AlertDialogTitle>
            <AlertDialogDescription>
              删除后无法恢复，确定要删除租户
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
              onClick={handleDeleteTenant}
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

