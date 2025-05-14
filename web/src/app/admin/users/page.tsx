'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { UserRole } from '@/types/auth';
import UserCreateModal from '@/components/admin/UserCreateModal';
import UserEditModal from '@/components/admin/UserEditModal';
import { apiClient } from '@/service/apiClient';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';

interface User {
  id: number;
  username: string;
  email: string;
  phone?: string;
  roles: string[];
  is_active: boolean;
  created_at: string;
}

export default function UsersPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  // 添加分页状态管理
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(5);
  
  // 添加搜索筛选状态
  const [searchUsername, setSearchUsername] = useState('');
  const [searchEmail, setSearchEmail] = useState('');
  const [searchPhone, setSearchPhone] = useState('');
  const [searchRole, setSearchRole] = useState('all');
  const [searchStatus, setSearchStatus] = useState('all');
  const [allUsers, setAllUsers] = useState<User[]>([]);

  // 检查用户是否有管理员权限
  useEffect(() => {
    if (user && !user.roles.includes('admin')) {
      router.push('/unauthorized');
    }
  }, [user, router]);

  // 获取用户列表
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/users');
      if (response.ok) {
        // 使用response.data如果存在，否则尝试解析JSON
        if (response.data) {
          setAllUsers(response.data);
          setUsers(response.data);
        } else if (!response.bodyUsed) { // 检查body是否已被使用
          try {
            const data = await response.json();
            setAllUsers(data);
            setUsers(data);
          } catch (jsonError) {
            console.error('解析用户数据失败', jsonError);
            throw new Error('解析用户数据失败');
          }
        } else {
          throw new Error('无法读取响应数据');
        }
      } else {
        throw new Error('获取用户列表失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取用户列表失败');
      console.error('获取用户列表错误', err);
    } finally {
      setLoading(false);
    }
  };

  // 筛选用户
  const filterUsers = () => {
    setCurrentPage(1); // 重置到第一页
    let filteredUsers = [...allUsers];
    
    if (searchUsername) {
      filteredUsers = filteredUsers.filter(user => 
        user.username.toLowerCase().includes(searchUsername.toLowerCase())
      );
    }
    
    if (searchEmail) {
      filteredUsers = filteredUsers.filter(user => 
        user.email.toLowerCase().includes(searchEmail.toLowerCase())
      );
    }
    
    if (searchPhone) {
      filteredUsers = filteredUsers.filter(user => 
        user.phone && user.phone.includes(searchPhone)
      );
    }
    
    if (searchRole && searchRole !== 'all') {
      filteredUsers = filteredUsers.filter(user => 
        user.roles.includes(searchRole)
      );
    }
    
    if (searchStatus !== 'all') {
      const isActive = searchStatus === 'active';
      filteredUsers = filteredUsers.filter(user => user.is_active === isActive);
    }
    
    setUsers(filteredUsers);
  };

  // 重置筛选条件
  const resetFilters = () => {
    setSearchUsername('');
    setSearchEmail('');
    setSearchPhone('');
    setSearchRole('all');
    setSearchStatus('all');
    setUsers(allUsers);
    setCurrentPage(1);
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // 处理用户创建
  const handleUserCreated = () => {
    setShowCreateModal(false);
    fetchUsers();
  };

  // 处理用户更新
  const handleUserUpdated = () => {
    setShowEditModal(false);
    setSelectedUser(null);
    fetchUsers();
  };

  // 处理编辑用户
  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setShowEditModal(true);
  };

  // 格式化日期
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  // 渲染角色标签
  const renderRoleBadge = (role: string) => {
    const colors: Record<string, string> = {
      admin: 'bg-red-100 text-red-800',
      advisor: 'bg-blue-100 text-blue-800',
      doctor: 'bg-green-100 text-green-800',
      customer: 'bg-purple-100 text-purple-800',
      operator: 'bg-yellow-100 text-yellow-800'
    };

    const roleNames: Record<string, string> = {
      admin: '管理员',
      advisor: '顾问',
      doctor: '医生',
      customer: '顾客',
      operator: '运营'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs ${colors[role] || 'bg-gray-100 text-gray-800'}`}>
        {roleNames[role] || role}
      </span>
    );
  };

  // 分页逻辑
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentUsers = users.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(users.length / itemsPerPage);

  // 页码变更
  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  if (loading && users.length === 0) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">用户管理</h1>
        <Button 
          onClick={() => setShowCreateModal(true)}
          className="bg-orange-500 hover:bg-orange-600"
        >
          创建用户
        </Button>
      </div>

      {/* 添加组合查询区域 */}
      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
        <h2 className="mb-4 text-lg font-medium text-gray-800">组合查询</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
          <div>
            <Label htmlFor="username" className="mb-2 block text-sm font-medium">用户名</Label>
            <Input
              id="username"
              value={searchUsername}
              onChange={(e) => setSearchUsername(e.target.value)}
              placeholder="搜索用户名"
              className="w-full"
            />
          </div>
          <div>
            <Label htmlFor="email" className="mb-2 block text-sm font-medium">邮箱</Label>
            <Input
              id="email"
              value={searchEmail}
              onChange={(e) => setSearchEmail(e.target.value)}
              placeholder="搜索邮箱"
              className="w-full"
            />
          </div>
          <div>
            <Label htmlFor="phone" className="mb-2 block text-sm font-medium">手机</Label>
            <Input
              id="phone"
              value={searchPhone}
              onChange={(e) => setSearchPhone(e.target.value)}
              placeholder="搜索手机号"
              className="w-full"
            />
          </div>
          <div>
            <Label htmlFor="role" className="mb-2 block text-sm font-medium">角色</Label>
            <Select value={searchRole} onValueChange={setSearchRole}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="选择角色" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部角色</SelectItem>
                <SelectItem value="admin">管理员</SelectItem>
                <SelectItem value="advisor">顾问</SelectItem>
                <SelectItem value="doctor">医生</SelectItem>
                <SelectItem value="customer">顾客</SelectItem>
                <SelectItem value="operator">运营</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="status" className="mb-2 block text-sm font-medium">状态</Label>
            <Select value={searchStatus} onValueChange={setSearchStatus}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="active">活跃</SelectItem>
                <SelectItem value="inactive">禁用</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="mt-4 flex justify-end space-x-2">
          <Button variant="outline" onClick={resetFilters}>
            重置
          </Button>
          <Button className="bg-orange-500 hover:bg-orange-600" onClick={filterUsers}>
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
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                ID
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                用户名
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                邮箱
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                手机
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                角色
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                状态
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                创建时间
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {currentUsers.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  {user.id}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                  {user.username}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  {user.email}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  {user.phone || '-'}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  <div className="flex flex-wrap gap-1">
                    {user.roles.map((role) => (
                      <div key={role}>{renderRoleBadge(role)}</div>
                    ))}
                  </div>
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm">
                  <span className={`px-2 py-1 rounded-full text-xs ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {user.is_active ? '活跃' : '禁用'}
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  {formatDate(user.created_at)}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEditUser(user)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    编辑
                  </Button>
                </td>
              </tr>
            ))}
            
            {users.length === 0 && (
              <tr>
                <td colSpan={8} className="px-6 py-4 text-center text-sm text-gray-500">
                  暂无用户数据
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      
      {/* 分页组件 */}
      {users.length > 0 && (
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

      {/* 创建用户模态框 */}
      {showCreateModal && (
        <UserCreateModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onUserCreated={handleUserCreated}
        />
      )}

      {/* 编辑用户模态框 */}
      {showEditModal && selectedUser && (
        <UserEditModal
          isOpen={showEditModal}
          onClose={() => {
            setShowEditModal(false);
            setSelectedUser(null);
          }}
          user={selectedUser}
          onUserUpdated={handleUserUpdated}
        />
      )}
    </div>
  );
} 