'use client';

import { useEffect, useState } from 'react';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { userService } from '@/service/userService';
import type { User } from '@/types/auth';

interface EmployeeSummaryProps {
  userId: string;
}

const ROLE_LABELS: Record<string, string> = {
  admin: '管理员',
  doctor: '医生',
  operator: '运营人员',
  customer: '客户',
};

export default function EmployeeSummary({ userId }: EmployeeSummaryProps) {
  const [userInfo, setUserInfo] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) return;

    let cancelled = false;

    const loadUser = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await userService.getUser(userId);
        if (!cancelled) {
          setUserInfo(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : '获取员工信息失败');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadUser();

    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="am-card p-4">
        <div className="text-sm text-red-600">{error}</div>
      </div>
    );
  }

  if (!userInfo) {
    return (
      <div className="am-card p-4">
        <div className="text-sm text-gray-500">未找到员工信息</div>
      </div>
    );
  }

  const roles = (userInfo.roles || [])
    .map((role) => ROLE_LABELS[role] || role)
    .join(' / ');

  return (
    <div className="space-y-4">
      <div className="am-card p-4">
        <div className="text-sm font-medium text-gray-900">员工简要信息</div>
        <div className="mt-3 space-y-2 text-sm text-gray-700">
          <div className="flex justify-between">
            <span className="text-gray-500">姓名</span>
            <span>{userInfo.username || '未设置'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">邮箱</span>
            <span>{userInfo.email || '未设置'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">手机号</span>
            <span>{userInfo.phone || '未设置'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">角色</span>
            <span>{roles || '未设置'}</span>
          </div>
          {userInfo.tenantName && (
            <div className="flex justify-between">
              <span className="text-gray-500">所属租户</span>
              <span>{userInfo.tenantName}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
