'use client';

import { Search, X, Tag, Users, UserPlus, ChevronLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import type { ContactTag, ContactGroup } from '@/types/contacts';

interface ContactToolbarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedTags: string[];
  onTagsChange: (tags: string[]) => void;
  selectedGroups: string[];
  onGroupsChange: (groups: string[]) => void;
  sortBy: 'name' | 'recent' | 'added' | 'interaction';
  sortOrder: 'asc' | 'desc';
  onSortChange: (field: 'name' | 'recent' | 'added' | 'interaction') => void;
  onAddFriend: () => void;
  tags: ContactTag[];
  groups: ContactGroup[];
  onToggleSidebar?: () => void;
}

export function ContactToolbar({
  searchQuery,
  onSearchChange,
  selectedTags,
  onTagsChange,
  selectedGroups,
  onGroupsChange,
  sortBy,
  sortOrder,
  onSortChange,
  onAddFriend,
  tags,
  groups,
  onToggleSidebar
}: ContactToolbarProps) {
  return (
    <div className="bg-white border-b border-gray-200 p-4 space-y-4">
      {/* 第一行：搜索和主要操作 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 flex-1">
          {/* 移动端：显示侧边栏按钮（淡黄色） */}
          {onToggleSidebar && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggleSidebar}
              className="md:hidden text-yellow-400 hover:text-yellow-500 hover:bg-yellow-50/50 p-2"
            >
              <ChevronLeft className="h-5 w-5" />
            </Button>
          )}
          
          {/* 搜索框 */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="搜索好友姓名、昵称、备注..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10"
            />
            {searchQuery && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onSearchChange('')}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
              >
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
        
        {/* 右侧操作 */}
        <div className="flex items-center space-x-2">
          {/* 添加好友 */}
          <Button onClick={onAddFriend}>
            <UserPlus className="w-4 h-4 mr-2" />
            添加好友
          </Button>
        </div>
      </div>
      
      {/* 第二行：激活的筛选器显示 */}
      {(selectedTags.length > 0 || selectedGroups.length > 0 || searchQuery) && (
        <div className="flex items-center space-x-2 flex-wrap">
          <span className="text-sm text-gray-500">筛选条件：</span>
          
          {searchQuery && (
            <Badge variant="secondary" className="flex items-center space-x-1">
              <Search className="w-3 h-3" />
              <span>"{searchQuery}"</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onSearchChange('')}
                className="h-4 w-4 p-0 ml-1"
              >
                <X className="w-3 h-3" />
              </Button>
            </Badge>
          )}
          
          {/* TODO: 添加标签和分组的Badge显示 */}
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              onSearchChange('');
              onTagsChange([]);
              onGroupsChange([]);
            }}
            className="text-gray-500 hover:text-gray-700"
          >
            清除所有筛选
          </Button>
        </div>
      )}
    </div>
  );
}



