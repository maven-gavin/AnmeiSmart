import { Suspense } from 'react';
import SimulationPageClient from '@/app/advisor/simulation/SimulationPageClient';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export const metadata = {
  title: '术前模拟 - 安美智享',
  description: '医美顾问术前效果模拟系统',
};

export default function SimulationPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <SimulationPageClient />
    </Suspense>
  );
} 