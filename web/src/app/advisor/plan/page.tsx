import { Suspense } from 'react';
import PlanPageClient from './PlanPageClient';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export const metadata = {
  title: '个性化方案推荐 - 安美智享',
  description: '医美顾问个性化方案推荐系统',
};

export default function PlanPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <PlanPageClient />
    </Suspense>
  );
} 