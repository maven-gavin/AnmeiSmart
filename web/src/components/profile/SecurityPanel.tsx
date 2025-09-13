'use client';

import { useState, useEffect } from 'react';
import { profileService, type LoginHistory } from '@/service/profileService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

interface PasswordFormData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export function SecurityPanel() {
  const [loading, setLoading] = useState(false);
  const [loginHistory, setLoginHistory] = useState<LoginHistory[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // 密码修改表单状态
  const [passwordData, setPasswordData] = useState<PasswordFormData>({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  // 获取登录历史
  const fetchLoginHistory = async () => {
    try {
      setHistoryLoading(true);
      const history = await profileService.getMyLoginHistory(20);
      setLoginHistory(history);
    } catch (err) {
      console.error('获取登录历史失败:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  // 组件挂载时获取登录历史
  useEffect(() => {
    fetchLoginHistory();
  }, []);

  // 处理密码输入变化
  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // 重置密码表单
  const resetPasswordForm = () => {
    setPasswordData({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    });
  };

  // 修改密码
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      setSuccessMessage(null);

      // 前端验证
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

      // 调用API修改密码
      await profileService.changePassword({
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword,
        confirm_password: passwordData.confirmPassword
      });

      // 成功后重置表单和显示成功消息
      resetPasswordForm();
      setSuccessMessage('密码修改成功');

      // 3秒后清除成功消息
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '密码修改失败';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 格式化登录时间
  const formatLoginTime = (timeString: string) => {
    return new Date(timeString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 获取设备信息
  const getDeviceInfo = (userAgent?: string) => {
    if (!userAgent) return '未知设备';
    
    // 简单的设备检测
    if (userAgent.includes('Mobile')) return '移动设备';
    if (userAgent.includes('Windows')) return 'Windows';
    if (userAgent.includes('Mac')) return 'macOS';
    if (userAgent.includes('Linux')) return 'Linux';
    return '桌面设备';
  };

  return (
    <div className="space-y-6">
      <Tabs defaultValue="password" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="password">密码管理</TabsTrigger>
          <TabsTrigger value="history">登录历史</TabsTrigger>
        </TabsList>

        {/* 密码管理标签页 */}
        <TabsContent value="password">
          <Card>
            <CardHeader>
              <CardTitle>修改密码</CardTitle>
              <CardDescription>
                定期更改密码可以保护您的账户安全
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              {/* 错误和成功消息 */}
              {error && (
                <Alert variant="destructive" className="mb-4">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {successMessage && (
                <Alert className="mb-4">
                  <AlertDescription>{successMessage}</AlertDescription>
                </Alert>
              )}

              <form onSubmit={handleChangePassword} className="space-y-4">
                {/* 当前密码 */}
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

                {/* 新密码 */}
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

                {/* 确认新密码 */}
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

                {/* 提交按钮 */}
                <div className="flex gap-2 pt-4">
                  <Button 
                    type="submit" 
                    disabled={loading}
                    className="w-full"
                  >
                    {loading ? '修改中...' : '修改密码'}
                  </Button>
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={resetPasswordForm}
                    disabled={loading}
                  >
                    重置
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 登录历史标签页 */}
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>登录历史</CardTitle>
                  <CardDescription>
                    查看您最近的登录记录，如发现异常请及时修改密码
                  </CardDescription>
                </div>
                <Button 
                  variant="outline" 
                  onClick={fetchLoginHistory}
                  disabled={historyLoading}
                >
                  刷新
                </Button>
              </div>
            </CardHeader>
            
            <CardContent>
              {historyLoading ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner />
                </div>
              ) : loginHistory.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  暂无登录历史记录
                </div>
              ) : (
                <div className="space-y-3">
                  {loginHistory.map((record, index) => (
                    <div 
                      key={`${record.id}-${record.login_time}-${index}`} 
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center space-x-4">
                        <div className={`w-2 h-2 rounded-full ${index === 0 ? 'bg-green-500' : 'bg-gray-300'}`} />
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-medium">
                              {formatLoginTime(record.login_time)}
                            </span>
                            {index === 0 && (
                              <span className="text-xs bg-green-100 text-green-600 px-2 py-1 rounded">
                                当前会话
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-gray-500 mt-1">
                            <span>{getDeviceInfo(record.user_agent)}</span>
                            {record.ip_address && (
                              <span className="ml-2">• IP: {record.ip_address}</span>
                            )}
                            {record.login_role && (
                              <span className="ml-2">• 角色: {record.login_role}</span>
                            )}
                            {record.location && (
                              <span className="ml-2">• {record.location}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 