import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '登录 - 安美智享',
  description: '安美智享智能服务平台登录',
};

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
} 