'use client';

import { ReactNode } from 'react';
import RoleLayout from './RoleLayout';
import DynamicSidebar from './DynamicSidebar';
import { UserRole } from '@/types/auth';

interface AppLayoutProps {
  children: ReactNode;
  requiredRole?: UserRole;
}

export default function AppLayout({ children, requiredRole }: AppLayoutProps) {
  return (
    <RoleLayout requiredRole={requiredRole}>
      <div className="flex h-full w-full overflow-hidden">
        <DynamicSidebar />
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </div>
    </RoleLayout>
  );
} 