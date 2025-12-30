'use client';

import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { UserRole, AuthUser, Role } from '@/types/auth';
import { useAuthContext } from '@/contexts/AuthContext';
import { authService, roleOptions } from '@/service/authService';

interface RoleSelectorProps {
  onRoleSelect?: (role: UserRole) => void;
  className?: string;
}

export default function RoleSelector({ onRoleSelect, className = '' }: RoleSelectorProps) {
  const router = useRouter();
  const { user, switchRole, loading: authLoading } = useAuthContext();
  const [selectedRole, setSelectedRole] = useState<UserRole | undefined>(undefined);
  const [roleDetails, setRoleDetails] = useState<Role[]>([]);
  const [loading, setLoading] = useState<UserRole | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isClient, setIsClient] = useState(false);
  
  // 在客户端挂载后获取用户信息和角色详情
  useEffect(() => {
    setIsClient(true);
    if (user) {
      setSelectedRole(user.currentRole);
      // 获取动态角色详情
      authService.getRoleDetails().then(roles => {
        if (roles && roles.length > 0) {
          setRoleDetails(roles);
        }
      });
    }
  }, [user]);

  // 获取角色显示信息
  const getRoleDisplayInfo = (roleId: string) => {
    const dynamicRole = roleDetails.find(r => r.name === roleId);
    const staticOption = roleOptions.find(r => r.id === roleId);
    
    return {
      name: dynamicRole?.displayName || staticOption?.name || roleId,
      description: dynamicRole?.description || '暂无描述',
      path: staticOption?.path || '/tasks'
    };
  };

  // 过滤出当前用户拥有的角色
  const availableRoles = isClient && user?.roles 
    ? user.roles.map(roleId => ({ id: roleId, ...getRoleDisplayInfo(roleId) }))
    : [];

  const handleRoleSelect = async (role: UserRole) => {
    try {
      console.log('切换角色', role);
      setLoading(role);
      setError(null);
      setSelectedRole(role);
      
      // 切换用户角色
      if (user) {
        await switchRole(role);
      }
      
      // 调用回调
      if (onRoleSelect) {
        onRoleSelect(role);
      }
      
      // 导航到任务管理
      router.push('/tasks');
    } catch (error) {
      console.error('角色切换失败', error);
      setError('角色切换失败，请重试');
    } finally {
      setLoading(null);
    }
  };

  // 始终返回一致的结构，避免水合错误
  return (
    <div className={`p-4 ${className}`}>
      <h3 className="mb-4 text-lg font-medium text-gray-800">选择角色</h3>
      
      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-500">
          {error}
        </div>
      )}
      
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {isClient && availableRoles.map((role) => (
          <button
            key={role.id}
            onClick={() => !loading && handleRoleSelect(role.id)}
            disabled={loading !== null || authLoading}
            className={`flex items-center rounded-lg border p-4 transition-all hover:border-orange-500 hover:bg-orange-50 ${
              selectedRole === role.id 
                ? 'border-orange-500 bg-orange-50' 
                : 'border-gray-200'
            } ${(loading !== null || authLoading) && 'cursor-wait opacity-70'}`}
          >
            <div 
              className={`mr-3 flex h-12 w-12 items-center justify-center rounded-full ${
                selectedRole === role.id 
                  ? 'bg-orange-500 text-white' 
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              {loading === role.id ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
              ) : (
                <span className="text-lg">
                  {role.id === 'consultant' ? '顾' : 
                   role.id === 'doctor' ? '医' : 
                   role.id === 'operator' ? '运' : '客'}
                </span>
              )}
            </div>
            <div className="text-left">
              <p className="font-medium text-gray-800">{role.name}</p>
              <p className="text-sm text-gray-500">
                {role.description}
              </p>
            </div>
          </button>
        ))}
        
        {!isClient && (
          <div className="flex items-center rounded-lg border border-gray-200 p-4">
            <div className="mr-3 flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
              <span className="text-gray-400">...</span>
            </div>
            <div className="text-left">
              <p className="font-medium text-gray-400">加载中...</p>
              <p className="text-sm text-gray-300">请稍候</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 