'use client';

import { MessageCircle, Star, MoreHorizontal, Edit, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/service/utils';
import type { Friendship } from '@/types/contacts';

interface ContactListProps {
  friends: Friendship[];
  viewMode: 'list' | 'card';
  loading: boolean;
  pagination: {
    page: number;
    size: number;
    total: number;
    pages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
  onPageChange: (page: number) => void;
  onFriendAction: (action: string, friendId: string) => void;
}

export function ContactList({
  friends,
  viewMode,
  loading,
  pagination,
  onPageChange,
  onFriendAction
}: ContactListProps) {
  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }

  if (friends.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <MessageCircle className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">暂无好友</h3>
          <p className="text-gray-500 mb-4">开始添加好友，建立您的专业网络</p>
          <Button onClick={() => onFriendAction('add', '')}>
            添加好友
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* 好友列表 */}
      <div className="flex-1 overflow-auto p-4">
        <div className={cn(
          viewMode === 'card' 
            ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
            : "space-y-2"
        )}>
          {friends.map((friendship) => (
            <FriendCard
              key={friendship.id}
              friendship={friendship}
              viewMode={viewMode}
              onAction={onFriendAction}
            />
          ))}
        </div>
      </div>
      
      {/* 分页控制 */}
      {pagination.pages > 1 && (
        <div className="border-t border-gray-200 px-4 py-3 bg-white">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              显示 {(pagination.page - 1) * pagination.size + 1} - {Math.min(pagination.page * pagination.size, pagination.total)} 
              ，共 {pagination.total} 个好友
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(pagination.page - 1)}
                disabled={!pagination.hasPrev}
              >
                上一页
              </Button>
              
              <span className="text-sm text-gray-600">
                {pagination.page} / {pagination.pages}
              </span>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(pagination.page + 1)}
                disabled={!pagination.hasNext}
              >
                下一页
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// 好友卡片组件
interface FriendCardProps {
  friendship: Friendship;
  viewMode: 'list' | 'card';
  onAction: (action: string, friendId: string) => void;
}

function FriendCard({ friendship, viewMode, onAction }: FriendCardProps) {
  const friend = friendship.friend;
  
  if (!friend) {
    return null;
  }

  return (
    <div className={cn(
      "bg-white border border-gray-200 hover:shadow-md transition-all duration-200",
      viewMode === 'card' ? "rounded-lg p-4" : "border-l-0 border-r-0 border-t-0 p-3",
      friendship.is_pinned && "ring-2 ring-blue-100 bg-blue-50"
    )}>
      <div className="flex items-center justify-between">
        {/* 好友信息 */}
        <div className="flex items-center space-x-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
              {friend.avatar ? (
                <img
                  src={friend.avatar}
                  alt={friend.username}
                  className="w-10 h-10 rounded-full object-cover"
                />
              ) : (
                <span className="text-sm font-medium text-gray-600">
                  {friend.username.charAt(0).toUpperCase()}
                </span>
              )}
            </div>
            
            {/* 在线状态指示器 - TODO: 从WebSocket获取 */}
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white bg-green-500"></div>
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-medium text-gray-900 truncate">
                {friendship.nickname || friend.username}
              </h3>
              
              {/* 状态指示器 */}
              <div className="flex items-center space-x-1">
                {friendship.is_starred && (
                  <Star className="w-4 h-4 text-yellow-500 fill-current" />
                )}
                {friendship.is_pinned && (
                  <div className="w-4 h-4 text-blue-500">📌</div>
                )}
                {friendship.is_muted && (
                  <div className="w-4 h-4 text-gray-400">🔇</div>
                )}
              </div>
            </div>
            
            <p className="text-xs text-gray-500 truncate">
              {friend.roles?.join('、') || '用户'}
            </p>
            
            {friendship.remark && (
              <p className="text-xs text-gray-400 truncate mt-1">
                {friendship.remark}
              </p>
            )}
          </div>
        </div>
        
        {/* 标签和操作 */}
        <div className="flex items-center space-x-3">
          {/* 标签显示 */}
          <div className="flex flex-wrap gap-1 max-w-32">
            {friendship.tags.slice(0, 2).map(tag => (
              <Badge 
                key={tag.id} 
                variant="secondary" 
                style={{ 
                  backgroundColor: tag.color + '20', 
                  color: tag.color,
                  borderColor: tag.color + '40'
                }}
                className="text-xs border"
              >
                {tag.name}
              </Badge>
            ))}
            {friendship.tags.length > 2 && (
              <Badge variant="outline" className="text-xs">
                +{friendship.tags.length - 2}
              </Badge>
            )}
          </div>
          
          {/* 快速操作 */}
          <div className="flex items-center space-x-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onAction('chat', friend.id)}
              className="h-8 w-8 p-0"
            >
              <MessageCircle className="w-4 h-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onAction('toggle_star', friend.id)}
              className={cn(
                "h-8 w-8 p-0",
                friendship.is_starred && "text-yellow-500"
              )}
            >
              <Star className={cn(
                "w-4 h-4",
                friendship.is_starred && "fill-current"
              )} />
            </Button>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                >
                  <MoreHorizontal className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-40 bg-white">
                <DropdownMenuItem 
                  onClick={() => onAction('edit', friend.id)}
                  className="cursor-pointer"
                >
                  <Edit className="mr-2 h-4 w-4" />
                  <span>编辑</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={() => onAction('remove', friend.id)}
                  className="cursor-pointer text-red-600 focus:text-red-600 focus:bg-red-50"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  <span>删除</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </div>
  );
}



