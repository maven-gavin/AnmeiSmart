'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { cn } from '@/service/utils';

interface NavItemProps {
  href: string;
  icon: React.ReactNode;
  label: string;
  isActive: boolean;
}

const NavItem = ({ href, icon, label, isActive }: NavItemProps) => (
  <Link
    href={href}
    className={cn(
      "flex h-32 flex-col items-center justify-center gap-2 rounded-lg border border-gray-100 bg-white p-4 shadow-sm transition-all hover:border-orange-200 hover:bg-orange-50",
      isActive && "border-orange-500 bg-orange-50"
    )}
  >
    <div className={cn(
      "flex h-12 w-12 items-center justify-center rounded-full bg-orange-100",
      isActive && "bg-orange-200"
    )}>
      {icon}
    </div>
    <span className="text-sm font-medium">{label}</span>
  </Link>
);

export default function AdvisorNavigation() {
  const pathname = usePathname();

  return (
    <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
      <NavItem
        href="/advisor/chat"
        icon={
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        }
        label="智能客服"
        isActive={pathname.includes('/advisor/chat')}
      />
      <NavItem
        href="/advisor/simulation"
        icon={
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        }
        label="术前模拟"
        isActive={pathname.includes('/advisor/simulation')}
      />
      <NavItem
        href="/advisor/plan"
        icon={
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        }
        label="方案推荐"
        isActive={pathname.includes('/advisor/plan')}
      />
    </div>
  );
} 