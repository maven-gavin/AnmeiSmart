'use client';

import { useState, useEffect } from 'react';
import { profileService, type UserPreferences, type UserPreferencesUpdate } from '@/service/profileService';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export function PreferencesPanel() {
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // 表单状态
  const [formData, setFormData] = useState({
    notification_enabled: true,
    email_notification: true,
    push_notification: true
  });

  // 获取用户偏好设置
  const fetchPreferences = async () => {
    try {
      setLoading(true);
      setError(null);
      const prefs = await profileService.getMyPreferences();
      setPreferences(prefs);
      
      // 更新表单数据
      setFormData({
        notification_enabled: prefs.notification_enabled,
        email_notification: prefs.email_notification,
        push_notification: prefs.push_notification
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '获取偏好设置失败';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时获取数据
  useEffect(() => {
    fetchPreferences();
  }, []);

  // 处理开关变化
  const handleSwitchChange = (field: keyof typeof formData, value: boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // 保存偏好设置
  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      // 检查是否有变化
      if (preferences &&
          formData.notification_enabled === preferences.notification_enabled &&
          formData.email_notification === preferences.email_notification &&
          formData.push_notification === preferences.push_notification) {
        setSuccessMessage('偏好设置无变化');
        return;
      }

      // 准备更新数据
      const updateData: UserPreferencesUpdate = {
        notification_enabled: formData.notification_enabled,
        email_notification: formData.email_notification,
        push_notification: formData.push_notification
      };

      // 更新偏好设置
      const updatedPrefs = await profileService.updateMyPreferences(updateData);
      setPreferences(updatedPrefs);
      setSuccessMessage('偏好设置更新成功');

      // 3秒后清除成功消息
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '更新偏好设置失败';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  // 重置设置
  const handleReset = () => {
    if (preferences) {
      setFormData({
        notification_enabled: preferences.notification_enabled,
        email_notification: preferences.email_notification,
        push_notification: preferences.push_notification
      });
    }
    setError(null);
    setSuccessMessage(null);
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
            <CardTitle>偏好设置</CardTitle>
            <CardDescription>
              自定义您的通知偏好和系统设置
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={handleReset}
              disabled={saving}
            >
              重置
            </Button>
            <Button 
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? '保存中...' : '保存设置'}
            </Button>
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

        {/* 通知设置 */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">通知设置</h3>
          
          {/* 总开关 */}
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="space-y-1">
              <Label htmlFor="notification_enabled" className="text-base font-medium">
                启用通知
              </Label>
              <p className="text-sm text-gray-500">
                接收系统通知和重要提醒
              </p>
            </div>
            <Switch
              id="notification_enabled"
              checked={formData.notification_enabled}
              onCheckedChange={(checked: boolean) => handleSwitchChange('notification_enabled', checked)}
              disabled={saving}
            />
          </div>

          {/* 邮件通知 */}
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="space-y-1">
              <Label htmlFor="email_notification" className="text-base font-medium">
                邮件通知
              </Label>
              <p className="text-sm text-gray-500">
                通过邮件接收重要通知和提醒
              </p>
            </div>
            <Switch
              id="email_notification"
              checked={formData.email_notification && formData.notification_enabled}
              onCheckedChange={(checked: boolean) => handleSwitchChange('email_notification', checked)}
              disabled={saving || !formData.notification_enabled}
            />
          </div>

          {/* 推送通知 */}
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="space-y-1">
              <Label htmlFor="push_notification" className="text-base font-medium">
                推送通知
              </Label>
              <p className="text-sm text-gray-500">
                在浏览器中显示即时通知
              </p>
            </div>
            <Switch
              id="push_notification"
              checked={formData.push_notification && formData.notification_enabled}
              onCheckedChange={(checked: boolean) => handleSwitchChange('push_notification', checked)}
              disabled={saving || !formData.notification_enabled}
            />
          </div>
        </div>

        {/* 当前设置状态 */}
        {preferences && (
          <div className="border-t pt-6">
            <h4 className="mb-4 text-sm font-medium text-gray-700">当前设置状态</h4>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-500">通知总开关</p>
                <p className={`text-sm ${preferences.notification_enabled ? 'text-green-600' : 'text-gray-400'}`}>
                  {preferences.notification_enabled ? '已启用' : '已关闭'}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-500">邮件通知</p>
                <p className={`text-sm ${preferences.email_notification && preferences.notification_enabled ? 'text-green-600' : 'text-gray-400'}`}>
                  {preferences.email_notification && preferences.notification_enabled ? '已启用' : '已关闭'}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-500">推送通知</p>
                <p className={`text-sm ${preferences.push_notification && preferences.notification_enabled ? 'text-green-600' : 'text-gray-400'}`}>
                  {preferences.push_notification && preferences.notification_enabled ? '已启用' : '已关闭'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 说明信息 */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-800 mb-2">温馨提示</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• 关闭通知总开关将停止所有类型的通知</li>
            <li>• 邮件通知包括重要系统消息和安全提醒</li>
            <li>• 推送通知需要浏览器支持，首次使用时会请求权限</li>
            <li>• 设置保存后立即生效，无需重新登录</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
} 