import { Suspense } from 'react';
import AdvisorClientPage from '@/app/advisor/AdvisorClientPage';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export const metadata = {
  title: '顾问端 - 安美智享',
  description: '医美顾问管理系统',
};

export default function AdvisorPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <AdvisorClientPage />
    </Suspense>
  );
} 