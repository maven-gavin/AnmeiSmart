'use client';

import { useState, useEffect } from 'react';
import { authService } from '@/service/authService';
import { type AuthUser } from '@/types/auth';

export default function UserInfoBar() {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isClient, setIsClient] = useState(false);
  
  // 在客户端挂载后设置用户信息
  useEffect(() => {
    setIsClient(true);
    const user = authService.getCurrentUser();
    if (user) {
      setCurrentUser(user);
    }
  }, []);
  
  
  // 确定要显示的标签
  let tags: string[] = [];
  
  // 只在客户端根据用户角色设置标签
  if (isClient) {
    if (currentUser?.currentRole === 'operator') {
      tags = ['运营', '客户服务'];
    } else if (currentUser?.currentRole === 'customer') {
      tags = currentUser.id === '101' ? ['VIP客户'] : ['回头客'];
    } else if (currentUser?.currentRole === 'operator') {
      tags = ['运营', '数据分析'];
    }
  }

  return (
    <div className="flex items-center space-x-3">
      <img
        src={currentUser?.avatar || '/avatars/default.png'}
        alt={currentUser?.name || ''}
        className="h-10 w-10 rounded-full"
      />
      <div>
        <h3 className="font-medium">{currentUser?.name || ''}</h3>
        {isClient && tags.length > 0 && (
          <div className="flex space-x-2">
            {tags.map(tag => (
              <span
                key={tag}
                className="rounded-full bg-orange-100 px-2 py-0.5 text-xs text-orange-700"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 