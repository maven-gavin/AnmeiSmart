'use client';

import { Suspense } from 'react';
import LoginForm from '@/components/auth/LoginForm';

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-orange-100 via-orange-200 to-yellow-100 p-4">
      <Suspense fallback={<div>加载中...</div>}>
        <div className="w-full max-w-md">
          <LoginForm />
        </div>
      </Suspense>
    </div>
  );
} 