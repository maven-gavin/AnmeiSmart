'use client';

import { Suspense } from 'react';
import SimulationPageClient from '@/app/simulation/SimulationPageClient';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import AppLayout from '@/components/layout/AppLayout';
import { useAuthContext } from '@/contexts/AuthContext';

export default function SimulationPage() {
  const { user } = useAuthContext();
  return (
    <AppLayout requiredRole={user?.currentRole}>
    <Suspense fallback={<LoadingSpinner />}>
      <SimulationPageClient />
    </Suspense>
    </AppLayout>
  );
} 