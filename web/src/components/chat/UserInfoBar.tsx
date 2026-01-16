'use client';

import { useEffect, useState } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import { profileService, type BasicUserInfo } from '@/service/profileService';

export default function UserInfoBar() {
  const { user: currentUser } = useAuthContext();
  const [basicInfo, setBasicInfo] = useState<BasicUserInfo | null>(null);
  
  // 确定要显示的标签
  const tags: string[] = [];
  
  // 根据用户角色设置标签
  if (currentUser?.currentRole === 'operator') {
    tags.push('运营', '客户服务');
  } else if (currentUser?.currentRole === 'customer') {
    tags.push(currentUser.id === '101' ? 'VIP客户' : '回头客');
  }

  // 以 /auth/me 的“基本信息”为准渲染头像与名称，确保与个人中心一致
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const info = await profileService.getMyBasicInfo();
        if (!cancelled) setBasicInfo(info);
      } catch {
        // 静默失败：回退到 AuthContext 的缓存信息
        if (!cancelled) setBasicInfo(null);
      }
    };
    if (currentUser) load();
    return () => {
      cancelled = true;
    };
  }, [currentUser?.id]);

  const displayName = basicInfo?.username || currentUser?.name || '';
  const displayAvatar = basicInfo?.avatar || currentUser?.avatar || '/avatars/default.png';

  return (
    <div className="flex items-center space-x-3">
      <img
        src={displayAvatar}
        alt={displayName}
        className="h-10 w-10 rounded-full"
      />
      <div>
        <h3 className="font-medium">{displayName}</h3>
        {tags.length > 0 && (
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