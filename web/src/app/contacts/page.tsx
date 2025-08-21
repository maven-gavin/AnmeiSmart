'use client';

import { useAuthContext } from '@/contexts/AuthContext';
import { useRoleGuard } from '@/hooks/useRoleGuard';
import AppLayout from '@/components/layout/AppLayout';
import { ContactBookManagementPanel } from '@/components/contacts/ContactBookManagementPanel';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function ContactsPage() {
  const { user } = useAuthContext();
  
  // 通讯录需要用户登录但不限制特定角色，所有角色都可以访问
  const { isAuthorized, error, loading } = useRoleGuard({
    requireAuth: true,
    requiredRole: undefined // 所有角色都可以访问通讯录
  });

  if (loading || isAuthorized === null) {
    return (
      <AppLayout requiredRole={user?.currentRole}>
        <div className="flex h-full items-center justify-center">
          <LoadingSpinner />
        </div>
      </AppLayout>
    );
  }

  if (!isAuthorized) {
    return (
      <AppLayout requiredRole={user?.currentRole}>
        <div className="flex h-full items-center justify-center">
          <div className="text-center">
            <p className="text-gray-600">{error || '无权访问'}</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="h-full bg-gray-50">
        <ContactBookManagementPanel />
      </div>
    </AppLayout>
  );
}
