'use client';

import LoginForm from '@/components/auth/LoginForm';

export default function LoginClient() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-orange-100 via-orange-200 to-yellow-100 p-4">
      <LoginForm />
    </div>
  );
} 