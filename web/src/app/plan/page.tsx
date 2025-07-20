'use client';

import { useAuthContext } from '@/contexts/AuthContext';
import AppLayout from '@/components/layout/AppLayout';
import PlanPageClient from './PlanPageClient';


export default function PlanPage() {
  const { user } = useAuthContext();
  return (
    <AppLayout requiredRole={user?.currentRole}>
      <PlanPageClient />
    </AppLayout>
  );
} 