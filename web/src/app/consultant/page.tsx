import { Suspense } from 'react';
import ConsultantClientPage from '@/app/consultant/ConsultantClientPage';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export const metadata = {
  title: '顾问端 - 安美智享',
  description: '医美顾问管理系统',
};

export default function ConsultantPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <ConsultantClientPage />
    </Suspense>
  );
} 