'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { UserRole } from '@/types/auth';
import { apiClient } from '@/lib/apiClient';

interface UserCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUserCreated: () => void;
}

export default function UserCreateModal({ isOpen, onClose, onUserCreated }: UserCreateModalProps) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [roles, setRoles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const availableRoles: { id: string; name: string }[] = [
    { id: 'admin', name: '管理员' },
    { id: 'advisor', name: '顾问' },
    { id: 'doctor', name: '医生' },
    { id: 'customer', name: '顾客' },
    { id: 'operator', name: '运营' }
  ];

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
    if (!password.trim()) {
      setError('密码不能为空');
      return false;
    }
    if (password.length < 8) {
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
    
    try {
      const response = await apiClient.post('/users', {
        username,
        email,
        password,
        phone: phone || undefined,
        roles
      });
      
      if (!response.ok) {
        // 使用response.data如果存在，否则尝试解析JSON
        if (response.data) {
          throw new Error(response.data.detail || '创建用户失败');
        } else if (!response.bodyUsed) {
          try {
            const data = await response.json();
            throw new Error(data.detail || '创建用户失败');
          } catch (jsonError) {
            console.error('解析错误响应失败', jsonError);
            throw new Error('创建用户失败');
          }
        } else {
          throw new Error('创建用户失败');
        }
      }
      
      onUserCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建用户失败');
      console.error('创建用户错误', err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800">创建新用户</h2>
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
            <label htmlFor="username" className="mb-2 block text-sm font-medium text-gray-700">
              用户名 *
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
              disabled={loading}
            />
          </div>
          
          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-medium text-gray-700">
              邮箱 *
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
              disabled={loading}
            />
          </div>
          
          <div>
            <label htmlFor="password" className="mb-2 block text-sm font-medium text-gray-700">
              密码 *
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
              disabled={loading}
            />
            <p className="mt-1 text-xs text-gray-500">密码至少8位</p>
          </div>
          
          <div>
            <label htmlFor="phone" className="mb-2 block text-sm font-medium text-gray-700">
              手机号
            </label>
            <input
              id="phone"
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
              {loading ? '创建中...' : '创建用户'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
} 