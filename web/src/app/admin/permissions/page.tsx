'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PermissionGuard, IsAdmin } from '@/components/PermissionGuard';
import { permissionService } from '@/service/permissionService';
import { Permission, Role, Tenant } from '@/types/auth';
import { toast } from 'react-hot-toast';

export default function PermissionsPage() {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTenant, setSelectedTenant] = useState<string>('');

  // 权限表单状态
  const [permissionForm, setPermissionForm] = useState({
    name: '',
    displayName: '',
    description: '',
    permissionType: 'action' as const,
    scope: 'tenant' as const,
    resource: '',
    action: '',
    tenantId: ''
  });

  // 角色表单状态
  const [roleForm, setRoleForm] = useState({
    name: '',
    displayName: '',
    description: '',
    tenantId: ''
  });

  useEffect(() => {
    loadData();
  }, [selectedTenant]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [permissionsData, rolesData, tenantsData] = await Promise.all([
        permissionService.getPermissions(selectedTenant || undefined),
        permissionService.getRoles(selectedTenant || undefined),
        permissionService.getTenants()
      ]);
      
      setPermissions(permissionsData);
      setRoles(rolesData);
      setTenants(tenantsData);
    } catch (error) {
      console.error('加载数据失败:', error);
      toast.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePermission = async () => {
    try {
      await permissionService.createPermission({
        ...permissionForm,
        tenantId: permissionForm.tenantId || undefined
      });
      toast.success('权限创建成功');
      setPermissionForm({
        name: '',
        displayName: '',
        description: '',
        permissionType: 'action',
        scope: 'tenant',
        resource: '',
        action: '',
        tenantId: ''
      });
      loadData();
    } catch (error) {
      console.error('创建权限失败:', error);
      toast.error('创建权限失败');
    }
  };

  const handleCreateRole = async () => {
    try {
      await permissionService.createRole({
        ...roleForm,
        tenantId: roleForm.tenantId || undefined
      });
      toast.success('角色创建成功');
      setRoleForm({
        name: '',
        displayName: '',
        description: '',
        tenantId: ''
      });
      loadData();
    } catch (error) {
      console.error('创建角色失败:', error);
      toast.error('创建角色失败');
    }
  };

  const handleDeletePermission = async (permissionId: string) => {
    if (!confirm('确定要删除这个权限吗？')) return;
    
    try {
      await permissionService.deletePermission(permissionId);
      toast.success('权限删除成功');
      loadData();
    } catch (error) {
      console.error('删除权限失败:', error);
      toast.error('删除权限失败');
    }
  };

  const handleDeleteRole = async (roleId: string) => {
    if (!confirm('确定要删除这个角色吗？')) return;
    
    try {
      await permissionService.deleteRole(roleId);
      toast.success('角色删除成功');
      loadData();
    } catch (error) {
      console.error('删除角色失败:', error);
      toast.error('删除角色失败');
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">加载中...</div>;
  }

  return (
    <IsAdmin fallback={<div className="text-center text-red-500">需要管理员权限</div>}>
      <div className="container mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">权限管理</h1>
          <p className="text-gray-600">管理系统权限、角色和租户</p>
        </div>

        <div className="mb-6">
          <Label htmlFor="tenant-select">选择租户</Label>
          <Select value={selectedTenant} onValueChange={setSelectedTenant}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="选择租户" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">全部租户</SelectItem>
              {tenants.map((tenant) => (
                <SelectItem key={tenant.id} value={tenant.id}>
                  {tenant.displayName || tenant.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Tabs defaultValue="permissions" className="space-y-6">
          <TabsList>
            <TabsTrigger value="permissions">权限管理</TabsTrigger>
            <TabsTrigger value="roles">角色管理</TabsTrigger>
            <TabsTrigger value="tenants">租户管理</TabsTrigger>
          </TabsList>

          <TabsContent value="permissions" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>创建权限</CardTitle>
                <CardDescription>创建新的权限配置</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="permission-name">权限名称</Label>
                    <Input
                      id="permission-name"
                      value={permissionForm.name}
                      onChange={(e) => setPermissionForm({ ...permissionForm, name: e.target.value })}
                      placeholder="例如: user:create"
                    />
                  </div>
                  <div>
                    <Label htmlFor="permission-display-name">显示名称</Label>
                    <Input
                      id="permission-display-name"
                      value={permissionForm.displayName}
                      onChange={(e) => setPermissionForm({ ...permissionForm, displayName: e.target.value })}
                      placeholder="例如: 创建用户"
                    />
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="permission-description">描述</Label>
                  <Textarea
                    id="permission-description"
                    value={permissionForm.description}
                    onChange={(e) => setPermissionForm({ ...permissionForm, description: e.target.value })}
                    placeholder="权限描述"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="permission-type">权限类型</Label>
                    <Select
                      value={permissionForm.permissionType}
                      onValueChange={(value: any) => setPermissionForm({ ...permissionForm, permissionType: value })}
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
                  <div>
                    <Label htmlFor="permission-scope">权限范围</Label>
                    <Select
                      value={permissionForm.scope}
                      onValueChange={(value: any) => setPermissionForm({ ...permissionForm, scope: value })}
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
                  <div>
                    <Label htmlFor="permission-resource">资源</Label>
                    <Input
                      id="permission-resource"
                      value={permissionForm.resource}
                      onChange={(e) => setPermissionForm({ ...permissionForm, resource: e.target.value })}
                      placeholder="例如: user"
                    />
                  </div>
                  <div>
                    <Label htmlFor="permission-action">动作</Label>
                    <Input
                      id="permission-action"
                      value={permissionForm.action}
                      onChange={(e) => setPermissionForm({ ...permissionForm, action: e.target.value })}
                      placeholder="例如: create"
                    />
                  </div>
                </div>

                <Button onClick={handleCreatePermission} className="w-full">
                  创建权限
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>权限列表</CardTitle>
                <CardDescription>当前系统中的所有权限</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {permissions.map((permission) => (
                    <div key={permission.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{permission.displayName || permission.name}</h3>
                          <Badge variant={permission.isSystem ? "default" : "secondary"}>
                            {permission.isSystem ? "系统" : "自定义"}
                          </Badge>
                          <Badge variant={permission.isAdmin ? "destructive" : "outline"}>
                            {permission.isAdmin ? "管理员" : "普通"}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600">{permission.description}</p>
                        <div className="flex gap-2 mt-2">
                          <Badge variant="outline">{permission.permissionType}</Badge>
                          <Badge variant="outline">{permission.scope}</Badge>
                          {permission.resource && <Badge variant="outline">{permission.resource}</Badge>}
                          {permission.action && <Badge variant="outline">{permission.action}</Badge>}
                        </div>
                      </div>
                      {!permission.isSystem && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDeletePermission(permission.id)}
                        >
                          删除
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="roles" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>创建角色</CardTitle>
                <CardDescription>创建新的角色配置</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="role-name">角色名称</Label>
                    <Input
                      id="role-name"
                      value={roleForm.name}
                      onChange={(e) => setRoleForm({ ...roleForm, name: e.target.value })}
                      placeholder="例如: editor"
                    />
                  </div>
                  <div>
                    <Label htmlFor="role-display-name">显示名称</Label>
                    <Input
                      id="role-display-name"
                      value={roleForm.displayName}
                      onChange={(e) => setRoleForm({ ...roleForm, displayName: e.target.value })}
                      placeholder="例如: 编辑者"
                    />
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="role-description">描述</Label>
                  <Textarea
                    id="role-description"
                    value={roleForm.description}
                    onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })}
                    placeholder="角色描述"
                  />
                </div>

                <Button onClick={handleCreateRole} className="w-full">
                  创建角色
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>角色列表</CardTitle>
                <CardDescription>当前系统中的所有角色</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {roles.map((role) => (
                    <div key={role.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{role.displayName || role.name}</h3>
                          <Badge variant={role.isSystem ? "default" : "secondary"}>
                            {role.isSystem ? "系统" : "自定义"}
                          </Badge>
                          <Badge variant={role.isAdmin ? "destructive" : "outline"}>
                            {role.isAdmin ? "管理员" : "普通"}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600">{role.description}</p>
                      </div>
                      {!role.isSystem && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDeleteRole(role.id)}
                        >
                          删除
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="tenants" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>租户列表</CardTitle>
                <CardDescription>当前系统中的所有租户</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {tenants.map((tenant) => (
                    <div key={tenant.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{tenant.displayName || tenant.name}</h3>
                          <Badge variant={tenant.isSystem ? "default" : "secondary"}>
                            {tenant.isSystem ? "系统" : "业务"}
                          </Badge>
                          <Badge variant={tenant.status === 'active' ? "default" : "secondary"}>
                            {tenant.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600">{tenant.description}</p>
                        <div className="flex gap-2 mt-2">
                          <Badge variant="outline">{tenant.tenantType}</Badge>
                          {tenant.contactName && <Badge variant="outline">{tenant.contactName}</Badge>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </IsAdmin>
  );
}
