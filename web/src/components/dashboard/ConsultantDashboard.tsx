'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import ConsultantNavigation from '@/components/ui/ConsultantNavigation';
import AppLayout from '../layout/AppLayout';
import { useAuthContext } from '@/contexts/AuthContext';
import { authService, roleOptions } from '@/service/authService';

export default function ConsultantDashboard() {
  const { user } = useAuthContext();
  const [roleDisplayName, setRoleDisplayName] = useState('顾问端');

  useEffect(() => {
    const fetchRoleInfo = async () => {
      if (user?.currentRole) {
        try {
          const roles = await authService.getRoleDetails();
          const currentRole = roles.find(r => r.name === user.currentRole);
          if (currentRole?.displayName) {
            setRoleDisplayName(currentRole.displayName);
          } else {
            // Fallback to static options
            const staticOption = roleOptions.find(r => r.id === user.currentRole);
            if (staticOption) {
              setRoleDisplayName(staticOption.name);
            }
          }
        } catch (error) {
          console.error('Failed to fetch role details:', error);
        }
      }
    };
    fetchRoleInfo();
  }, [user?.currentRole]);

  return (
    <AppLayout requiredRole={user?.currentRole}>
    <div className="container mx-auto p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-800">欢迎使用{roleDisplayName}</h1>
      
      <ConsultantNavigation />
      
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold">智能客服</h2>
          <p className="mb-4 text-gray-600">多模态智能沟通，AI自动回复与顾问介入支持</p>
          <p className="text-sm text-gray-500">
            通过AI赋能的客服系统，提高沟通效率，更好地了解客户需求。系统会自动回复常见问题，
            需要时您可以随时介入对话。所有客户沟通记录将被保存，便于后续分析和跟进。
          </p>
        </div>
      </div>
    </div>
    </AppLayout>
  );
} 