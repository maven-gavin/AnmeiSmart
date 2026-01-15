'use client';

import React from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import {
  MoreHorizontal,
  Search,
  Star,
  User,
  Settings,
  Users,
} from 'lucide-react';

interface ChatActionsMenuProps {
  conversationId: string;
  hasCustomerProfile?: boolean;
  onSearchToggle: () => void;
  onParticipantsToggle: () => void;
  onImportantMessagesToggle: () => void;
  onCustomerProfileToggle: () => void;
  onConversationSettings: () => void;
}

export function ChatActionsMenu({
  conversationId,
  hasCustomerProfile = false,
  onSearchToggle,
  onParticipantsToggle,
  onImportantMessagesToggle,
  onCustomerProfileToggle,
  onConversationSettings
}: ChatActionsMenuProps) {
  return (
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
      <DropdownMenuContent align="end" className="w-56 bg-white">
        {/* 查找聊天内容 */}
        <DropdownMenuItem onClick={onSearchToggle} className="cursor-pointer">
          <Search className="mr-2 h-4 w-4" />
          <span>查找聊天内容</span>
        </DropdownMenuItem>

        {/* 参与者 */}
        <DropdownMenuItem onClick={onParticipantsToggle} className="cursor-pointer">
          <Users className="mr-2 h-4 w-4" />
          <span>参与者</span>
        </DropdownMenuItem>
        
        {/* 重点消息 */}
        <DropdownMenuItem onClick={onImportantMessagesToggle} className="cursor-pointer">
          <Star className="mr-2 h-4 w-4" />
          <span>重点消息</span>
        </DropdownMenuItem>
        
        <DropdownMenuSeparator />
        
        {/* 对方信息 */}
        {hasCustomerProfile && (
          <DropdownMenuItem onClick={onCustomerProfileToggle} className="cursor-pointer">
            <User className="mr-2 h-4 w-4" />
            <span>对方信息</span>
          </DropdownMenuItem>
        )}
        
        {/* 会话设置 */}
        <DropdownMenuItem onClick={onConversationSettings} className="cursor-pointer">
          <Settings className="mr-2 h-4 w-4" />
          <span>会话设置</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
