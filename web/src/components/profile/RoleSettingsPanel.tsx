'use client';

import { useState, useEffect } from 'react';
import { profileService, type UserDefaultRole, type UserDefaultRoleUpdate } from '@/service/profileService';
import { authService } from '@/service/authService';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export function RoleSettingsPanel() {
  const [defaultRole, setDefaultRole] = useState<UserDefaultRole | null>(null);
  const [availableRoles, setAvailableRoles] = useState<string[]>([]);
  const [currentRoles, setCurrentRoles] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // 表单状态
  const [selectedRole, setSelectedRole] = useState<string>('');

  // 角色中文映射
  const roleNameMap: Record<string, string> = {
    'customer': '客户',
    'admin': '管理员',
    'operator': '运营人员'
  };

  // 角色描述映射
  const roleDescriptionMap: Record<string, string> = {
    'customer': '客户角色 - 查看方案、管理个人信息',
    'admin': '管理员角色 - 系统管理、用户管理、全局设置',
    'operator': '运营人员角色 - 内容管理、数据分析、客户服务'
  };

  // 获取用户角色和默认角色设置
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 并行获取数据
      const [rolesResponse, defaultRoleResponse] = await Promise.all([
        authService.getRoles(),
        profileService.getMyDefaultRole()
      ]);

      setCurrentRoles(rolesResponse);
      setAvailableRoles(rolesResponse);
      setDefaultRole(defaultRoleResponse);

      // 设置选中的角色
      if (defaultRoleResponse?.default_role) {
        setSelectedRole(defaultRoleResponse.default_role);
      } else if (rolesResponse.length > 0) {
        // 如果没有设置默认角色，默认选择第一个角色
        setSelectedRole(rolesResponse[0]);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '获取角色信息失败';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时获取数据
  useEffect(() => {
    fetchData();
  }, []);

  // 保存默认角色设置
  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      if (!selectedRole) {
        throw new Error('请选择默认角色');
      }

      // 检查角色是否在可用角色列表中
      if (!availableRoles.includes(selectedRole)) {
        throw new Error('选择的角色无效');
      }

      // 检查是否有变化
      if (defaultRole?.default_role === selectedRole) {
        setSuccessMessage('默认角色设置无变化');
        return;
      }

      // 更新默认角色
      const updateData: UserDefaultRoleUpdate = {
        default_role: selectedRole
      };

      const updatedRole = await profileService.setMyDefaultRole(updateData);
      setDefaultRole(updatedRole);
      setSuccessMessage('默认角色设置成功');

      // 3秒后清除成功消息
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '设置默认角色失败';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  // 重置设置
  const handleReset = () => {
    if (defaultRole?.default_role) {
      setSelectedRole(defaultRole.default_role);
    } else if (availableRoles.length > 0) {
      setSelectedRole(availableRoles[0]);
    }
    setError(null);
    setSuccessMessage(null);
  };

  // 清除默认角色设置
  const handleClearDefaultRole = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      // 这里可以调用API删除默认角色设置
      // 暂时通过设置为空字符串来实现
      const updateData: UserDefaultRoleUpdate = {
        default_role: ''
      };

      await profileService.setMyDefaultRole(updateData);
      setDefaultRole(null);
      setSelectedRole(availableRoles.length > 0 ? availableRoles[0] : '');
      setSuccessMessage('已清除默认角色设置');

      // 3秒后清除成功消息
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '清除默认角色失败';
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
            <CardTitle>角色设置</CardTitle>
            <CardDescription>
              管理您的角色权限和登录默认角色设置
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
              disabled={saving || !selectedRole}
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

        {/* 当前角色信息 */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">当前拥有的角色</h3>
          
          {currentRoles.length === 0 ? (
            <div className="text-center py-4 text-gray-500">
              您当前没有分配任何角色
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {currentRoles.map((role) => (
                <Badge 
                  key={role} 
                  variant={role === defaultRole?.default_role ? "default" : "secondary"}
                  className="text-sm px-3 py-1"
                >
                  {roleNameMap[role] || role}
                  {role === defaultRole?.default_role && (
                    <span className="ml-1 text-xs">(默认)</span>
                  )}
                </Badge>
              ))}
            </div>
          )}
        </div>

        {/* 默认角色设置 */}
        {availableRoles.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">默认登录角色</h3>
              {defaultRole && (
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={handleClearDefaultRole}
                  disabled={saving}
                  className="text-red-600 hover:text-red-700"
                >
                  清除设置
                </Button>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="defaultRole">选择默认角色 *</Label>
              <Select 
                value={selectedRole} 
                onValueChange={setSelectedRole}
                disabled={saving}
              >
                <SelectTrigger id="defaultRole" className="w-full">
                  <SelectValue placeholder="请选择默认角色" />
                </SelectTrigger>
                <SelectContent>
                  {availableRoles.map((role) => (
                    <SelectItem key={role} value={role}>
                      <div className="flex items-center justify-between w-full">
                        <span>{roleNameMap[role] || role}</span>
                        {role === defaultRole?.default_role && (
                          <Badge variant="outline" className="ml-2 text-xs">当前</Badge>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedRole && (
                <p className="text-sm text-gray-500 mt-1">
                  {roleDescriptionMap[selectedRole] || '角色描述'}
                </p>
              )}
            </div>
          </div>
        )}

        {/* 设置说明 */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-800 mb-2">设置说明</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• 默认角色将在您首次登录时自动生效</li>
            <li>• 您可以随时在右上角角色选择器中切换其他角色</li>
            <li>• 如果不设置默认角色，系统会提示您选择登录角色</li>
            <li>• 只能选择您当前拥有的角色作为默认角色</li>
            <li>• 管理员可以为您分配或移除角色权限</li>
          </ul>
        </div>

        {/* 当前状态 */}
        {defaultRole && (
          <div className="border-t pt-6">
            <h4 className="mb-4 text-sm font-medium text-gray-700">当前设置状态</h4>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-500">默认角色</p>
                <p className="text-sm font-medium">
                  {roleNameMap[defaultRole.default_role] || defaultRole.default_role}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-500">设置时间</p>
                <p className="text-sm text-gray-600">
                  {defaultRole.created_at ? new Date(defaultRole.created_at).toLocaleString('zh-CN') : '未知'}
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 