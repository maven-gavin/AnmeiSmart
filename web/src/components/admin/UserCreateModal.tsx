'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { UserRole } from '@/types/auth';
import { userService } from '@/service/userService';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import toast from 'react-hot-toast';

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
  const [roles, setRoles] = useState<UserRole[]>([]);
  const [loading, setLoading] = useState(false);
  
  const availableRoles: { id: UserRole; name: string }[] = [
    { id: 'admin', name: '管理员' },
    { id: 'consultant', name: '顾问' },
    { id: 'doctor', name: '医生' },
    { id: 'customer', name: '客户' },
    { id: 'operator', name: '运营' }
  ];

  const handleRoleToggle = (roleId: UserRole) => {
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
      toast.error('用户名不能为空');
      return false;
    }
    if (!email.trim()) {
      toast.error('邮箱不能为空');
      return false;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
      toast.error('邮箱格式不正确');
      return false;
    }
    if (!password.trim()) {
      toast.error('密码不能为空');
      return false;
    }
    if (password.length < 8) {
      toast.error('密码长度不能少于8位');
      return false;
    }
    if (roles.length === 0) {
      toast.error('至少选择一个角色');
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
    
    try {
      // 创建用户
      await userService.createUser({
        username,
        email,
        password,
        phone: phone || undefined,
        roles
      });
      
      onUserCreated();
    } catch (err: any) {
      toast.error(err.message || '创建用户失败');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl animate-in fade-in zoom-in duration-200">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800">创建新用户</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            ✕
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="create-username">用户名 *</Label>
            <Input
              id="create-username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="create-email">邮箱 *</Label>
            <Input
              id="create-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="create-password">密码 *</Label>
            <Input
              id="create-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
            <p className="text-xs text-gray-500">密码至少8位</p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="create-phone">手机号</Label>
            <Input
              id="create-phone"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              disabled={loading}
            />
          </div>
          
          <div className="space-y-2">
            <Label>角色 *</Label>
            <div className="flex flex-wrap gap-2">
              {availableRoles.map((role) => (
                <Badge
                  key={role.id}
                  variant={roles.includes(role.id) ? "default" : "outline"}
                  className={`cursor-pointer hover:opacity-80 ${
                    roles.includes(role.id) ? 'bg-orange-500 hover:bg-orange-600' : ''
                  }`}
                  onClick={() => handleRoleToggle(role.id)}
                >
                  {role.name}
                </Badge>
              ))}
            </div>
          </div>
          
          <div className="flex justify-end space-x-3 pt-4 border-t">
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
