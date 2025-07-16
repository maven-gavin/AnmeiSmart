'use client';

import { useState, useEffect } from 'react';
import { profileService, type BasicUserInfo } from '@/service/profileService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export function BasicInfoPanel() {
  const [userInfo, setUserInfo] = useState<BasicUserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // 编辑表单状态
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    phone: '',
    avatar: ''
  });

  // 获取用户基本信息
  const fetchUserInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      const info = await profileService.getMyBasicInfo();
      setUserInfo(info);
      
      // 更新表单数据
      setFormData({
        username: info.username || '',
        email: info.email || '',
        phone: info.phone || '',
        avatar: info.avatar || ''
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '获取用户信息失败';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时获取数据
  useEffect(() => {
    fetchUserInfo();
  }, []);

  // 处理表单输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // 取消编辑
  const handleCancelEdit = () => {
    setEditing(false);
    setError(null);
    setSuccessMessage(null);
    
    // 重置表单数据
    if (userInfo) {
      setFormData({
        username: userInfo.username || '',
        email: userInfo.email || '',
        phone: userInfo.phone || '',
        avatar: userInfo.avatar || ''
      });
    }
  };

  // 保存用户信息
  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      // 验证表单
      if (!formData.username.trim()) {
        throw new Error('用户名不能为空');
      }
      if (!formData.email.trim()) {
        throw new Error('邮箱不能为空');
      }

      // 只发送有变化的字段
      const updateData: Partial<BasicUserInfo> = {};
      if (formData.username !== userInfo?.username) updateData.username = formData.username;
      if (formData.email !== userInfo?.email) updateData.email = formData.email;
      if (formData.phone !== userInfo?.phone) updateData.phone = formData.phone;
      if (formData.avatar !== userInfo?.avatar) updateData.avatar = formData.avatar;

      if (Object.keys(updateData).length === 0) {
        setEditing(false);
        setSuccessMessage('信息无变化');
        return;
      }

      // 更新用户信息
      const updatedInfo = await profileService.updateMyBasicInfo(updateData);
      setUserInfo(updatedInfo);
      setEditing(false);
      setSuccessMessage('用户信息更新成功');

      // 3秒后清除成功消息
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '更新用户信息失败';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>基本信息</CardTitle>
            <CardDescription>
              管理您的基本账户信息
            </CardDescription>
          </div>
          <div className="flex gap-2">
            {editing ? (
              <>
                <Button 
                  variant="outline" 
                  onClick={handleCancelEdit}
                  disabled={saving}
                >
                  取消
                </Button>
                <Button 
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? '保存中...' : '保存'}
                </Button>
              </>
            ) : (
              <Button onClick={() => setEditing(true)}>
                编辑
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* 错误消息 */}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* 成功消息 */}
        {successMessage && (
          <Alert>
            <AlertDescription>{successMessage}</AlertDescription>
          </Alert>
        )}

        {/* 用户头像 */}
        <div className="flex items-center space-x-4">
          <div className="h-16 w-16 overflow-hidden rounded-full bg-gray-200">
            <img
              src={userInfo?.avatar || '/avatars/default.png'}
              alt="用户头像"
              className="h-full w-full object-cover"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = '/avatars/default.png';
              }}
            />
          </div>
          <div>
            <h3 className="text-lg font-medium">{userInfo?.username}</h3>
            <p className="text-sm text-gray-500">
              {userInfo?.roles.join(', ') || '无角色'}
            </p>
          </div>
        </div>

        {/* 基本信息表单 */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* 用户名 */}
          <div className="space-y-2">
            <Label htmlFor="username">用户名 *</Label>
            {editing ? (
              <Input
                id="username"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                placeholder="请输入用户名"
                disabled={saving}
              />
            ) : (
              <p className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm">
                {userInfo?.username || '未设置'}
              </p>
            )}
          </div>

          {/* 邮箱 */}
          <div className="space-y-2">
            <Label htmlFor="email">邮箱 *</Label>
            {editing ? (
              <Input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="请输入邮箱"
                disabled={saving}
              />
            ) : (
              <p className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm">
                {userInfo?.email || '未设置'}
              </p>
            )}
          </div>

          {/* 手机号 */}
          <div className="space-y-2">
            <Label htmlFor="phone">手机号</Label>
            {editing ? (
              <Input
                id="phone"
                name="phone"
                type="tel"
                value={formData.phone}
                onChange={handleInputChange}
                placeholder="请输入手机号"
                disabled={saving}
              />
            ) : (
              <p className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm">
                {userInfo?.phone || '未设置'}
              </p>
            )}
          </div>

          {/* 头像URL */}
          <div className="space-y-2">
            <Label htmlFor="avatar">头像URL</Label>
            {editing ? (
              <Input
                id="avatar"
                name="avatar"
                type="url"
                value={formData.avatar}
                onChange={handleInputChange}
                placeholder="请输入头像URL"
                disabled={saving}
              />
            ) : (
              <p className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm">
                {userInfo?.avatar || '使用默认头像'}
              </p>
            )}
          </div>
        </div>

        {/* 账户状态信息 */}
        <div className="border-t pt-6">
          <h4 className="mb-4 text-sm font-medium text-gray-700">账户状态</h4>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-500">账户状态</p>
              <p className={`text-sm ${userInfo?.is_active ? 'text-green-600' : 'text-red-600'}`}>
                {userInfo?.is_active ? '激活' : '未激活'}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-500">当前角色</p>
              <p className="text-sm text-gray-900">
                {userInfo?.active_role || '未设置'}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-500">创建时间</p>
              <p className="text-sm text-gray-900">
                {userInfo?.created_at 
                  ? new Date(userInfo.created_at).toLocaleDateString('zh-CN')
                  : '未知'
                }
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 