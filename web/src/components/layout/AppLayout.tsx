'use client';

import { ReactNode } from 'react';
import RoleLayout from './RoleLayout';
import DynamicSidebar from './DynamicSidebar';
import { MobileBottomNav } from '@/components/layout/MobileBottomNav';
import { UserRole } from '@/types/auth';

interface AppLayoutProps {
  children: ReactNode;
  requiredRole?: UserRole;
}

export default function AppLayout({ children, requiredRole }: AppLayoutProps) {
  return (
    <RoleLayout requiredRole={requiredRole}>
      <div className="flex h-full w-full overflow-hidden">
        <div className="hidden md:block">
          <DynamicSidebar />
        </div>
        <div className="flex-1 overflow-hidden pb-16 md:pb-0">
          {children}
        </div>
        <MobileBottomNav />
      </div>
    </RoleLayout>
  );
} 