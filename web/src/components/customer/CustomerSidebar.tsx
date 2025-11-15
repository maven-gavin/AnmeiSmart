'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

// 导航项定义
const navItems = [
  {
    icon: (active: boolean) => (
      <svg className={`h-5 w-5 ${active ? 'text-orange-500' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
      </svg>
    ),
    label: '在线咨询',
    path: '/customer/chat'
  },
  {
    icon: (active: boolean) => (
      <svg className={`h-5 w-5 ${active ? 'text-orange-500' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
    label: '个人中心',
    path: '/customer/profile'
  }
];

export default function CustomerSidebar() {
  const pathname = usePathname();
  
  return (
    <div className="h-full w-64 border-r border-gray-200 bg-white">
      <div className="flex h-full flex-col">
        <div className="px-4 pt-5">
          <h2 className="mb-4 text-lg font-medium text-gray-800">客户服务</h2>
        </div>
        
        <nav className="mt-2 flex-1 space-y-1 px-2">
          {navItems.map((item) => {
            const isActive = pathname === item.path || pathname.startsWith(`${item.path}/`);
            
            return (
              <Link
                key={item.path}
                href={item.path}
                className={`group flex items-center rounded-md px-3 py-2 text-sm font-medium ${
                  isActive 
                    ? 'bg-orange-50 text-orange-700' 
                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                {item.icon(isActive)}
                <span className="ml-3">{item.label}</span>
              </Link>
            );
          })}
        </nav>
        
        <div className="border-t border-gray-200 p-4">
          <div className="flex items-center space-x-3 rounded-md bg-orange-50 p-3">
            <svg className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="text-xs font-medium text-orange-800">需要帮助?</p>
              <p className="text-xs text-orange-700">联系客服</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 