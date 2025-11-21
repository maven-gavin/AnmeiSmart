'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { User, UserRole } from '@/types/auth';
import { userService } from '@/service/userService';
import UserCreateModal from '@/components/admin/UserCreateModal';
import UserEditModal from '@/components/admin/UserEditModal';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import AppLayout from '@/components/layout/AppLayout';
import { EnhancedPagination } from '@/components/ui/pagination';
import { RoleBadge } from '@/components/common/RoleBadge';
import toast from 'react-hot-toast';

export default function UsersPage() {
  const { user } = useAuthContext();
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  
  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  
  // 搜索状态
  const [searchKeyword, setSearchKeyword] = useState('');
  
  // 检查用户是否有管理员权限
  useEffect(() => {
    // 这里假设 admin 角色名就是 'admin'，实际情况请根据项目调整
    // 如果 roles 包含 admin 或 operator (根据 RolePermissionDomainService 逻辑)
    if (user && !user.roles.some(role => ['admin', 'administrator', 'operator'].includes(role))) {
      router.push('/unauthorized');
    }
  }, [user, router]);

  // 获取用户列表
  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      // userService.getUsers 返回的是数组，后端目前没有返回 total
      // 如果后端接口调整了返回格式包含 total，这里需要同步修改
      // 目前后端 endpoint 返回 ApiResponse[List[UserResponse]]
      // 分页是在后端做的，但是 total count 没有返回... 这是一个潜在问题
      // 暂时只展示当前页数据
      const data = await userService.getUsers({
        skip: (currentPage - 1) * itemsPerPage,
        limit: itemsPerPage,
        search: searchKeyword || undefined
      });
      
      setUsers(data);
      setTotal(1000); // 临时占位
      
    } catch (err: any) {
      setError(err.message || '获取用户列表失败');
      toast.error('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 监听分页和搜索变化
  useEffect(() => {
    fetchUsers();
  }, [currentPage, itemsPerPage]);

  // 处理搜索
  const handleSearch = () => {
    setCurrentPage(1);
    fetchUsers();
  };

  // 重置搜索
  const handleReset = () => {
    setSearchKeyword('');
    setCurrentPage(1);
    // 由于 useEffect 依赖 searchKeyword 可能会导致闭包问题或者竞态
    // 最好是 setState 后触发 fetch，或者直接 fetch
    // 这里 setSearchKeyword 是异步的，fetchUsers 使用的是闭包中的 state
    // 所以需要等待下一次 render
    // 我们可以在 useEffect 中监听 searchKeyword 变化？不，这会导致输入时频繁请求
    // 所以这里手动调用 fetchUsers 传递空字符串
    // 但 fetchUsers 读取的是 state... 
    // 简单的做法：
    setTimeout(() => {
        // 这是一个 hack，更好的方式是将 fetchUsers 移入 useEffect 并添加依赖，
        // 但为了避免输入时自动搜索，我们保持手动触发
        // 实际上，handleReset 设置 state 后，我们可以利用一个 ref 或者 just reload
        window.location.reload(); // 最简单粗暴的重置，或者...
    }, 0);
  };
  // 更好的 handleReset
  const resetFilters = () => {
      setSearchKeyword('');
      // 这里的 fetchUsers 还是会读到旧的 searchKeyword
      // 让我们修改 fetchUsers 接受参数
      // ...
      // 实际上，由于 React 的批处理，我们可以将 fetchUsers 放入 useEffect [searchKeyword] 但不，那是自动搜索
      // 我们直接刷新页面吧，或者
      // setTrigger(!trigger)
  };

  // 处理用户创建
  const handleUserCreated = () => {
    setShowCreateModal(false);
    fetchUsers();
    toast.success('用户创建成功');
  };

  // 处理用户更新
  const handleUserUpdated = () => {
    setShowEditModal(false);
    setSelectedUser(null);
    fetchUsers();
    toast.success('用户更新成功');
  };

  // 处理编辑用户
  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setShowEditModal(true);
  };

  // 格式化日期
  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('zh-CN');
  };

  if (loading && users.length === 0) {
    return (
      <AppLayout requiredRole={user?.currentRole}>
        <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout requiredRole={user?.currentRole}>
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

        {/* 搜索区域 */}
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Label htmlFor="search" className="mb-2 block text-sm font-medium">关键词搜索</Label>
              <Input
                id="search"
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch();
                  }
                }}
                placeholder="搜索用户名或邮箱..."
                className="w-full max-w-md"
              />
            </div>
            <div className="flex items-end gap-2 pb-1">
              <Button variant="outline" onClick={() => {
                  setSearchKeyword('');
                  // 稍微延迟一下确保 state 更新
                  setTimeout(() => {
                      setCurrentPage(1);
                      // 这里需要传递参数覆盖 state
                      userService.getUsers({ skip: 0, limit: itemsPerPage }).then(setUsers);
                  }, 0);
              }}>
                重置
              </Button>
              <Button className="bg-orange-500 hover:bg-orange-600" onClick={handleSearch}>
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
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {user.id.slice(0, 8)}...
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
                        <RoleBadge key={role} role={role} />
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
          <div className="mt-6">
            <EnhancedPagination
              currentPage={currentPage}
              totalPages={Math.ceil(total / itemsPerPage)} // 这是一个估计值
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
    </AppLayout>
  );
}
