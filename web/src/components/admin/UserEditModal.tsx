'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/service/apiClient';

interface User {
  id: number;
  username: string;
  email: string;
  phone?: string;
  roles: string[];
  is_active: boolean;
}

interface UserEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: User;
  onUserUpdated: () => void;
}

export default function UserEditModal({ isOpen, onClose, user, onUserUpdated }: UserEditModalProps) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [roles, setRoles] = useState<string[]>([]);
  const [isActive, setIsActive] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const availableRoles: { id: string; name: string }[] = [
    { id: 'admin', name: '管理员' },
    { id: 'consultant', name: '顾问' },
    { id: 'doctor', name: '医生' },
    { id: 'customer', name: '客户' },
    { id: 'operator', name: '运营' }
  ];

  // 初始化表单数据
  useEffect(() => {
    if (user) {
      // 确保始终传递受控组件可接受的值，避免从 defined 变为 undefined
      setUsername(user.username ?? '');
      setEmail(user.email ?? '');
      setPhone(user.phone ?? '');
      setRoles(user.roles ?? []);
      setIsActive(user.is_active ?? true);
    }
  }, [user]);

  const handleRoleToggle = (roleId: string) => {
    setRoles(prevRoles => {
      if (prevRoles.includes(roleId)) {
        return prevRoles.filter(r => r !== roleId);
      } else {
        return [...prevRoles, roleId];
      }
    });
  };

  const validateForm = () => {
    if (!username.trim()) {
      setError('用户名不能为空');
      return false;
    }
    if (!email.trim()) {
      setError('邮箱不能为空');
      return false;
    }
    // 简单验证邮箱格式
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError('邮箱格式不正确');
      return false;
    }
    if (password && password.length < 8) {
      setError('密码长度不能少于8位');
      return false;
    }
    if (roles.length === 0) {
      setError('至少选择一个角色');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    setError(null);
    
    // 构建更新数据对象，仅包含已更改的字段
    const updateData: Record<string, any> = {};
    if (username !== user.username) updateData.username = username;
    if (email !== user.email) updateData.email = email;
    if (password) updateData.password = password;
    if (phone !== user.phone) updateData.phone = phone || undefined;
    if (JSON.stringify(roles) !== JSON.stringify(user.roles)) updateData.roles = roles;
    if (isActive !== user.is_active) updateData.is_active = isActive;
    
    try {
      const response = await apiClient.put(`/users/${user.id}`, updateData);

      console.log(response);

      if (response.status !== 200) {
        // 使用response.data如果存在，否则尝试解析JSON
        if (response.data && typeof response.data === 'object' && 'detail' in response.data) {
          throw new Error((response.data as any).detail || '更新用户失败');
        } else {
          throw new Error('更新用户失败');
        }
      }
      
      onUserUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新用户失败');
      console.error('更新用户错误', err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800">编辑用户</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-500">
              {error}
            </div>
          )}
          
          <div>
            <label htmlFor="edit-username" className="mb-2 block text-sm font-medium text-gray-700">
              用户名 *
            </label>
            <input
              id="edit-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
              disabled={loading}
            />
          </div>
          
          <div>
            <label htmlFor="edit-email" className="mb-2 block text-sm font-medium text-gray-700">
              邮箱 *
            </label>
            <input
              id="edit-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
              disabled={loading}
            />
          </div>
          
          <div>
            <label htmlFor="edit-password" className="mb-2 block text-sm font-medium text-gray-700">
              密码
            </label>
            <input
              id="edit-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
              disabled={loading}
              placeholder="留空表示不修改密码"
            />
            <p className="mt-1 text-xs text-gray-500">如需修改密码，请输入新密码（至少8位）</p>
          </div>
          
          <div>
            <label htmlFor="edit-phone" className="mb-2 block text-sm font-medium text-gray-700">
              手机号
            </label>
            <input
              id="edit-phone"
              type="text"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
              disabled={loading}
            />
          </div>
          
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              角色 *
            </label>
            <div className="flex flex-wrap gap-2">
              {availableRoles.map((role) => (
                <div
                  key={role.id}
                  onClick={() => handleRoleToggle(role.id)}
                  className={`cursor-pointer rounded-full px-3 py-1 text-sm ${
                    roles.includes(role.id)
                      ? 'bg-orange-100 text-orange-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {role.name}
                </div>
              ))}
            </div>
          </div>
          
          <div>
            <label className="relative inline-flex cursor-pointer items-center">
              <input
                type="checkbox"
                className="peer sr-only"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                disabled={loading}
              />
              <div className="peer h-6 w-11 rounded-full bg-gray-200 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-orange-500 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none"></div>
              <span className="ml-3 text-sm font-medium text-gray-700">
                {isActive ? '账户已启用' : '账户已禁用'}
              </span>
            </label>
          </div>
          
          <div className="flex justify-end space-x-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
            >
              取消
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="bg-orange-500 hover:bg-orange-600"
            >
              {loading ? '更新中...' : '更新用户'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
} 