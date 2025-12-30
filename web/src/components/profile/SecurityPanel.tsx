'use client';

import { useState } from 'react';
import { profileService } from '@/service/profileService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface PasswordFormData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export function SecurityPanel() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [passwordData, setPasswordData] = useState<PasswordFormData>({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const resetPasswordForm = () => {
    setPasswordData({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    });
    setError(null);
    setSuccessMessage(null);
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      setSuccessMessage(null);

      if (!passwordData.currentPassword.trim()) {
        throw new Error('请输入当前密码');
      }
      if (passwordData.newPassword.length < 8) {
        throw new Error('新密码长度至少8位');
      }
      if (passwordData.newPassword !== passwordData.confirmPassword) {
        throw new Error('新密码和确认密码不一致');
      }
      if (passwordData.currentPassword === passwordData.newPassword) {
        throw new Error('新密码不能与当前密码相同');
      }

      await profileService.changePassword({
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword,
        confirm_password: passwordData.confirmPassword
      });

      resetPasswordForm();
      setSuccessMessage('密码修改成功');
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '密码修改失败';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>密码管理</CardTitle>
            <CardDescription>
              定期更改密码可以保护您的账户安全
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button 
              type="button"
              variant="outline" 
              onClick={resetPasswordForm}
              disabled={loading}
            >
              重置
            </Button>
            <Button 
              type="submit"
              disabled={loading}
              form="password-form"
            >
              {loading ? '修改中...' : '修改密码'}
            </Button>
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

        <form id="password-form" onSubmit={handleChangePassword} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="currentPassword">当前密码 *</Label>
            <Input
              id="currentPassword"
              name="currentPassword"
              type="password"
              value={passwordData.currentPassword}
              onChange={handlePasswordChange}
              placeholder="请输入当前密码"
              disabled={loading}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="newPassword">新密码 *</Label>
            <Input
              id="newPassword"
              name="newPassword"
              type="password"
              value={passwordData.newPassword}
              onChange={handlePasswordChange}
              placeholder="请输入新密码（至少8位）"
              disabled={loading}
              required
              minLength={8}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">确认新密码 *</Label>
            <Input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              value={passwordData.confirmPassword}
              onChange={handlePasswordChange}
              placeholder="请再次输入新密码"
              disabled={loading}
              required
              minLength={8}
            />
          </div>
        </form>
      </CardContent>
    </Card>
  );
} 