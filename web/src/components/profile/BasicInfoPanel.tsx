'use client';

import { useState, useEffect } from 'react';
import { profileService, type BasicUserInfo } from '@/service/profileService';
import { authService } from '@/service/authService';
import { apiClient } from '@/service/apiClient';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Upload } from 'lucide-react';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { normalizeAvatarUrl } from '@/utils/avatarUrl';
import toast from 'react-hot-toast';

export function BasicInfoPanel() {
  const [userInfo, setUserInfo] = useState<BasicUserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    phone: '',
    avatar: '',
    active_role: ''
  });

  const fetchUserInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      const info = await profileService.getMyBasicInfo();
      setUserInfo(info);
      
      setFormData({
        username: info.username || '',
        email: info.email || '',
        phone: info.phone || '',
        avatar: info.avatar || '',
        active_role: info.active_role || (info.roles && info.roles.length > 0 ? info.roles[0] : '')
      });

      if (info.avatar) {
        setAvatarPreview(normalizeAvatarUrl(info.avatar) ?? null);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '获取用户信息失败';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserInfo();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAvatarChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        toast.error('请选择图片文件');
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        toast.error('头像文件大小不能超过 5MB');
        return;
      }

      setAvatarFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setAvatarPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleCancelEdit = () => {
    setEditing(false);
    setError(null);
    setSuccessMessage(null);
    setAvatarFile(null);
    
    if (userInfo) {
      setFormData({
        username: userInfo.username || '',
        email: userInfo.email || '',
        phone: userInfo.phone || '',
        avatar: userInfo.avatar || '',
        active_role: userInfo.active_role || (userInfo.roles && userInfo.roles.length > 0 ? userInfo.roles[0] : '')
      });

      if (userInfo.avatar) {
        setAvatarPreview(normalizeAvatarUrl(userInfo.avatar) ?? null);
      } else {
        setAvatarPreview(null);
      }
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      if (!formData.username.trim()) {
        throw new Error('用户名不能为空');
      }
      if (!formData.email.trim()) {
        throw new Error('邮箱不能为空');
      }

      const updateData: Partial<BasicUserInfo> = {};
      if (formData.username !== userInfo?.username) updateData.username = formData.username;
      if (formData.email !== userInfo?.email) updateData.email = formData.email;
      if (formData.phone !== userInfo?.phone) updateData.phone = formData.phone;

      if (avatarFile) {
        const formDataUpload = new FormData();
        formDataUpload.append('file', avatarFile);

        const { data: result } = await apiClient.upload<any>('/files/upload-avatar', formDataUpload);
        if (!result?.success) {
          throw new Error(result?.message || '头像上传失败');
        }

        const avatarUrl = result?.file_info?.file_url as string | undefined;
        if (!avatarUrl) {
          throw new Error('服务器返回的头像地址为空');
        }

        updateData.avatar = avatarUrl;
      }

      const currentActiveRole = userInfo?.active_role || (userInfo?.roles && userInfo.roles.length > 0 ? userInfo.roles[0] : '');
      const roleChanged = formData.active_role && formData.active_role !== currentActiveRole;

      if (Object.keys(updateData).length === 0 && !roleChanged) {
        setEditing(false);
        setSuccessMessage('信息无变化');
        return;
      }

      if (Object.keys(updateData).length > 0) {
        const updatedInfo = await profileService.updateMyBasicInfo(updateData);
        setUserInfo(updatedInfo);
        if (updatedInfo.avatar) {
          setAvatarPreview(normalizeAvatarUrl(updatedInfo.avatar) ?? null);
        }
        setAvatarFile(null);
      }

      if (roleChanged && formData.active_role) {
        try {
          const frontendRole = formData.active_role === 'administrator' ? 'admin' : formData.active_role as any;
          await authService.switchRole(frontendRole);
          const refreshedInfo = await profileService.getMyBasicInfo();
          setUserInfo(refreshedInfo);
        } catch (roleError) {
          throw new Error(`切换角色失败: ${roleError instanceof Error ? roleError.message : '未知错误'}`);
        }
      }

      setEditing(false);
      setSuccessMessage('用户信息更新成功');
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
                  type="button"
                  variant="outline" 
                  onClick={handleCancelEdit}
                  disabled={saving}
                >
                  取消
                </Button>
                <Button 
                  type="button"
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? '保存中...' : '保存'}
                </Button>
              </>
            ) : (
              <Button 
                type="button"
                onClick={() => setEditing(true)}
                variant="ghost"
                size="sm"
              >
                编辑
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {successMessage && (
          <Alert>
            <AlertDescription>{successMessage}</AlertDescription>
          </Alert>
        )}

        <div className="flex items-center space-x-4">
          <div className="flex flex-col items-center space-y-3">
            <Avatar className="w-16 h-16 shadow-sm">
              <AvatarImage src={avatarPreview || normalizeAvatarUrl(userInfo?.avatar) || undefined} />
              <AvatarFallback className="text-lg bg-gradient-to-br from-orange-400 to-orange-600 text-white">
                {userInfo?.username?.charAt(0)?.toUpperCase() || '?'}
              </AvatarFallback>
            </Avatar>
            {editing && (
              <div className="flex items-center space-x-2">
                <Label htmlFor="avatar-upload" className="cursor-pointer">
                  <div className="flex items-center space-x-2 px-3 py-1.5 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 text-xs text-gray-700 transition-colors">
                    <Upload className="h-3.5 w-3.5" />
                    <span>上传头像</span>
                  </div>
                </Label>
                <Input
                  id="avatar-upload"
                  type="file"
                  accept="image/*"
                  onChange={handleAvatarChange}
                  className="hidden"
                />
              </div>
            )}
          </div>
          <div>
            <h3 className="text-lg font-medium">{userInfo?.username}</h3>
            <p className="text-sm text-gray-500">
              {userInfo?.roles.join(', ') || '无角色'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
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

        </div>

        <div className="border-t pt-6">
          <h4 className="mb-4 text-sm font-medium text-gray-700">账户状态</h4>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-500">账户状态</p>
              <p className={`text-sm font-medium ${
                userInfo?.is_active === true 
                  ? 'text-green-600' 
                  : userInfo?.is_active === false
                  ? 'text-red-600'
                  : 'text-gray-500'
              }`}>
                {userInfo?.is_active === true 
                  ? '已激活' 
                  : userInfo?.is_active === false
                  ? '未激活'
                  : '未知'
                }
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-500">当前角色</p>
              {editing ? (
                <Select
                  value={formData.active_role}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, active_role: value }))}
                  disabled={saving}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="选择角色" />
                  </SelectTrigger>
                  <SelectContent>
                    {userInfo?.roles && userInfo.roles.length > 0 ? (
                      userInfo.roles.map((role) => (
                        <SelectItem key={role} value={role}>
                          {role}
                        </SelectItem>
                      ))
                    ) : (
                      <SelectItem value="" disabled>无可用角色</SelectItem>
                    )}
                  </SelectContent>
                </Select>
              ) : (
                <p className="text-sm font-medium text-gray-900">
                  {userInfo?.active_role || (userInfo?.roles && userInfo.roles.length > 0 ? userInfo.roles[0] : '未设置')}
                </p>
              )}
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-500">创建时间</p>
              <p className="text-sm font-medium text-gray-900">
                {userInfo?.created_at 
                  ? new Date(userInfo.created_at).toLocaleString('zh-CN', {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit'
                    })
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