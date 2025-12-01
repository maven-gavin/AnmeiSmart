'use client';

import { useState, useEffect } from 'react';
import { cn } from '@/service/utils';
import type { ContactTag, ContactGroup } from '@/types/contacts';

interface ContactSidebarProps {
  selectedView: string;
  onViewChange: (view: string) => void;
  tags: ContactTag[];
  groups: ContactGroup[];
  friendsCount: number;
  loading: boolean;
}

// Hook for getting friend request count
function useFriendRequestCount() {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    const loadRequestCount = async () => {
      try {
        const { getFriendRequests } = await import('@/service/contacts/api');
        const result = await getFriendRequests('received', 'pending');
        setCount(result.total);
      } catch (error) {
        console.error('获取好友请求数量失败:', error);
      }
    };
    
    loadRequestCount();
    
    // 每30秒刷新一次
    const interval = setInterval(loadRequestCount, 30000);
    return () => clearInterval(interval);
  }, []);
  
  return count;
}

// Hook for getting view counts (starred, recent)
function useViewCounts() {
  const [starredCount, setStarredCount] = useState(0);
  const [recentCount, setRecentCount] = useState(0);
  
  useEffect(() => {
    const loadViewCounts = async () => {
      try {
        const { getFriends } = await import('@/service/contacts/api');
        
        // 获取星标好友数量
        const starredResult = await getFriends({ view: 'starred', page: 1, size: 1 });
        setStarredCount(starredResult.total);
        
        // 获取最近联系数量
        const recentResult = await getFriends({ view: 'recent', page: 1, size: 1 });
        setRecentCount(recentResult.total);
      } catch (error) {
        console.error('获取视图数量失败:', error);
      }
    };
    
    loadViewCounts();
    
    // 每30秒刷新一次
    const interval = setInterval(loadViewCounts, 30000);
    return () => clearInterval(interval);
  }, []);
  
  return { starredCount, recentCount };
}

export function ContactSidebar({
  selectedView,
  onViewChange,
  tags,
  groups,
  friendsCount,
  loading
}: ContactSidebarProps) {
  const pendingRequestCount = useFriendRequestCount();
  const { starredCount, recentCount } = useViewCounts();
  
  const quickViews = [
    { id: 'all', label: '全部好友', count: friendsCount },
    { id: 'starred', label: '星标好友', count: starredCount },
    { id: 'recent', label: '最近联系', count: recentCount },
    { id: 'pending', label: '待处理请求', count: pendingRequestCount }
  ];

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">通讯录</h2>
        
        {/* 快速视图 */}
        <div className="space-y-1 mb-6">
          {quickViews.map((view) => (
            <button
              key={view.id}
              onClick={() => onViewChange(view.id)}
              className={cn(
                "w-full flex items-center justify-between px-3 py-2 text-sm rounded-md transition-colors",
                selectedView === view.id
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <span>{view.label}</span>
              <span className={cn(
                "text-xs px-2 py-1 rounded-full",
                selectedView === view.id
                  ? "bg-blue-100 text-blue-700"
                  : "bg-gray-100 text-gray-500"
              )}>
                {loading ? '...' : view.count}
              </span>
            </button>
          ))}
        </div>
        
        {/* 自定义分组 */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-700 mb-2">自定义分组</h3>
          <div className="space-y-1">
            {groups.map((group) => (
              <button
                key={group.id}
                onClick={() => onViewChange(`group:${group.id}`)}
                className={cn(
                  "w-full flex items-center justify-between px-3 py-2 text-sm rounded-md transition-colors",
                  selectedView === `group:${group.id}`
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                )}
              >
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: group.color_theme }}
                  />
                  <span className="truncate">{group.name}</span>
                </div>
                <span className={cn(
                  "text-xs px-2 py-1 rounded-full",
                  selectedView === `group:${group.id}`
                    ? "bg-blue-100 text-blue-700"
                    : "bg-gray-100 text-gray-500"
                )}>
                  {group.member_count}
                </span>
              </button>
            ))}
            
            <button
              onClick={() => {/* TODO: 打开创建分组弹窗 */}}
              className="w-full flex items-center px-3 py-2 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
            >
              <span className="mr-2">+</span>
              创建分组
            </button>
          </div>
        </div>
        
        {/* 标签筛选 */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-700 mb-2">标签筛选</h3>
          <div className="space-y-1">
            {tags.slice(0, 8).map((tag) => (
              <button
                key={tag.id}
                onClick={() => onViewChange(`tag:${tag.id}`)}
                className={cn(
                  "w-full flex items-center justify-between px-3 py-2 text-sm rounded-md transition-colors",
                  selectedView === `tag:${tag.id}`
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                )}
              >
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: tag.color }}
                  />
                  <span className="truncate">{tag.name}</span>
                </div>
                <span className={cn(
                  "text-xs px-2 py-1 rounded-full",
                  selectedView === `tag:${tag.id}`
                    ? "bg-blue-100 text-blue-700"
                    : "bg-gray-100 text-gray-500"
                )}>
                  {tag.usage_count}
                </span>
              </button>
            ))}
            
            {tags.length > 8 && (
              <button
                onClick={() => {/* TODO: 显示所有标签 */}}
                className="w-full flex items-center px-3 py-2 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
              >
                查看更多标签...
              </button>
            )}
          </div>
        </div>
        
        {/* 设置选项 */}
        <div className="space-y-1">
          <button
            onClick={() => onViewChange('tag_management')}
            className={cn(
              "w-full flex items-center px-3 py-2 text-sm rounded-md transition-colors",
              selectedView === 'tag_management'
                ? "bg-blue-50 text-blue-700"
                : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            )}
          >
            <span className="mr-2">🏷️</span>
            标签管理
          </button>
          
        </div>
      </div>
    </div>
  );
}



