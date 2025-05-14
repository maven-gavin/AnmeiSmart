'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/apiClient';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';

interface Role {
  id: number;
  name: string;
  description: string | null;
}

export default function RolesPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [roleName, setRoleName] = useState('');
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
  const [allRoles, setAllRoles] = useState<Role[]>([]);

  // 检查用户是否有管理员权限
  useEffect(() => {
    if (user && !user.roles.includes('admin')) {
      router.push('/unauthorized');
    }
  }, [user, router]);

  // 获取角色列表
  const fetchRoles = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/users/roles/all');
      if (response.ok) {
        // 使用response.data如果存在，否则尝试解析JSON
        if (response.data) {
          setAllRoles(response.data);
          setRoles(response.data);
        } else if (!response.bodyUsed) { // 检查body是否已被使用
          try {
            const data = await response.json();
            setAllRoles(data);
            setRoles(data);
          } catch (jsonError) {
            console.error('解析角色数据失败', jsonError);
            throw new Error('解析角色数据失败');
          }
        } else {
          throw new Error('无法读取响应数据');
        }
      } else {
        throw new Error('获取角色列表失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取角色列表失败');
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
      filteredRoles = filteredRoles.filter(role => 
        role.id.toString().includes(searchId)
      );
    }
    
    if (searchName) {
      filteredRoles = filteredRoles.filter(role => 
        role.name.toLowerCase().includes(searchName.toLowerCase())
      );
    }
    
    if (searchDescription) {
      filteredRoles = filteredRoles.filter(role => 
        role.description && role.description.toLowerCase().includes(searchDescription.toLowerCase())
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

  // 创建角色
  const handleCreateRole = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!roleName.trim()) {
      setFormError('角色名称不能为空');
      return;
    }
    
    setFormLoading(true);
    setFormError(null);
    
    try {
      const response = await apiClient.post('/roles', {
        name: roleName.trim(),
        description: roleDescription.trim() || undefined
      });
      
      if (!response.ok) {
        // 使用response.data如果存在，否则尝试解析JSON
        if (response.data) {
          throw new Error(response.data.detail || '创建角色失败');
        } else {
          const data = await response.json();
          throw new Error(data.detail || '创建角色失败');
        }
      }
      
      // 重置表单并刷新列表
      setRoleName('');
      setRoleDescription('');
      setShowCreateForm(false);
      fetchRoles();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : '创建角色失败');
      console.error('创建角色错误', err);
    } finally {
      setFormLoading(false);
    }
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
      advisor: 'bg-blue-100 text-blue-800',
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
    <div className="container mx-auto px-4 py-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">角色管理</h1>
        <Button 
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-orange-500 hover:bg-orange-600"
        >
          {showCreateForm ? '取消' : '创建角色'}
        </Button>
      </div>

      {/* 添加组合查询区域 */}
      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
        <h2 className="mb-4 text-lg font-medium text-gray-800">组合查询</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div>
            <Label htmlFor="roleId" className="mb-2 block text-sm font-medium">角色ID</Label>
            <Input
              id="roleId"
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              placeholder="搜索角色ID"
              className="w-full"
            />
          </div>
          <div>
            <Label htmlFor="roleName" className="mb-2 block text-sm font-medium">角色名称</Label>
            <Input
              id="roleName"
              value={searchName}
              onChange={(e) => setSearchName(e.target.value)}
              placeholder="搜索角色名称"
              className="w-full"
            />
          </div>
          <div>
            <Label htmlFor="roleDescription" className="mb-2 block text-sm font-medium">角色描述</Label>
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

      {showCreateForm && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
          <h2 className="mb-4 text-lg font-medium text-gray-800">创建新角色</h2>
          
          {formError && (
            <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-500">
              {formError}
            </div>
          )}
          
          <form onSubmit={handleCreateRole} className="space-y-4">
            <div>
              <label htmlFor="createRoleName" className="mb-2 block text-sm font-medium text-gray-700">
                角色名称 *
              </label>
              <input
                id="createRoleName"
                type="text"
                value={roleName}
                onChange={(e) => setRoleName(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
                disabled={formLoading}
                placeholder="例如: editor, manager"
              />
            </div>
            
            <div>
              <label htmlFor="createRoleDescription" className="mb-2 block text-sm font-medium text-gray-700">
                角色描述
              </label>
              <textarea
                id="createRoleDescription"
                value={roleDescription}
                onChange={(e) => setRoleDescription(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
                disabled={formLoading}
                rows={3}
                placeholder="可选: 角色的详细描述"
              />
            </div>
            
            <div className="flex justify-end space-x-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowCreateForm(false);
                  setFormError(null);
                }}
                disabled={formLoading}
              >
                取消
              </Button>
              <Button
                type="submit"
                disabled={formLoading}
                className="bg-orange-500 hover:bg-orange-600"
              >
                {formLoading ? '创建中...' : '创建角色'}
              </Button>
            </div>
          </form>
        </div>
      )}

      <div className="overflow-hidden rounded-lg border border-gray-200 shadow">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                ID
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                角色名称
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                描述
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
                <td className="px-6 py-4 text-sm text-gray-500">
                  {role.description || '-'}
                </td>
              </tr>
            ))}
            
            {roles.length === 0 && (
              <tr>
                <td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">
                  暂无角色数据
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      
      {/* 分页组件 */}
      {roles.length > 0 && (
        <div className="mt-6 flex justify-between items-center">
          <Button
            onClick={() => router.push('/admin')}
            variant="outline"
            className="text-sm"
          >
            返回上一级
          </Button>
          
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
                variant={currentPage === i + 1 ? "default" : "outline"}
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
  );
} 