'use client';

import { ReactNode } from 'react';
import RoleLayout from '@/components/layout/RoleLayout';
import CustomerSidebar from '@/components/customer/CustomerSidebar';

export default function CustomerLayout({ children }: { children: ReactNode }) {
  return (
    <RoleLayout requiredRole="customer">
      <div className="flex h-full w-full overflow-hidden">
        <CustomerSidebar />
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </div>
    </RoleLayout>
  );
} 