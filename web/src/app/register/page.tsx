import { Metadata } from 'next';
import RegisterForm from '@/components/auth/RegisterForm';

export const metadata: Metadata = {
  title: '用户注册 - 安美智享',
  description: '注册您的安美智享账号，享受专业的医美智能服务',
};

export default function RegisterPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center p-4">
      <RegisterForm />
    </div>
  );
} 