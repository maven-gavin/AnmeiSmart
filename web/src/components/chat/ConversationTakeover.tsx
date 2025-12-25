'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  setTakeoverStatus,
  getTakeoverStatus,
} from '@/service/chatService';
import { User, Zap, UserCheck } from 'lucide-react';

type TakeoverStatus = 'full_takeover' | 'semi_takeover' | 'no_takeover';

interface ConversationTakeoverProps {
  conversationId?: string | null;
  className?: string;
}

const STATUS_CONFIG: Record<TakeoverStatus, { label: string; icon: React.ReactNode; description: string }> = {
  full_takeover: {
    label: '人工发送',
    icon: <User className="h-4 w-4" />,
    description: '人工完全接管会话',
  },
  semi_takeover: {
    label: '人工审核',
    icon: <UserCheck className="h-4 w-4" />,
    description: 'AI起草回复，人工审核',
  },
  no_takeover: {
    label: '自动发送',
    icon: <Zap className="h-4 w-4" />,
    description: 'AI完全接管会话',
  },
};

export default function ConversationTakeover({ 
  conversationId, 
  className = "flex-shrink-0" 
}: ConversationTakeoverProps) {
  const [currentStatus, setCurrentStatus] = useState<TakeoverStatus>('no_takeover');
  const [isLoading, setIsLoading] = useState(false);

  // 切换会话时，从数据库获取接管状态
  useEffect(() => {
    const fetchTakeoverStatus = async () => {
      if (!conversationId) {
        setCurrentStatus('no_takeover');
        return;
      }

      try {
        console.log('ConversationTakeover: 获取会话接管状态', conversationId);
        const status = await getTakeoverStatus(conversationId);
        console.log('ConversationTakeover: 当前接管状态', status);
        setCurrentStatus(status);
      } catch (error) {
        console.error('获取接管状态失败:', error);
        setCurrentStatus('no_takeover');
      }
    };

    fetchTakeoverStatus();
  }, [conversationId]);

  // 切换接管状态
  const handleStatusChange = useCallback(async (newStatus: TakeoverStatus) => {
    if (!conversationId || isLoading || newStatus === currentStatus) return;

    try {
      setIsLoading(true);
      console.log('ConversationTakeover: 切换接管状态', { 
        conversationId, 
        oldStatus: currentStatus,
        newStatus 
      });

      const success = await setTakeoverStatus(conversationId, newStatus);

      if (success) {
        // 更新本地状态
        setCurrentStatus(newStatus);
        
        console.log('ConversationTakeover: 状态切换成功', { 
          oldStatus: currentStatus, 
          newStatus 
        });
      } else {
        console.error('ConversationTakeover: 状态切换失败');
      }
    } catch (error) {
      console.error('切换接管模式失败:', error);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, currentStatus, isLoading]);

  const currentConfig = STATUS_CONFIG[currentStatus];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button 
          className={`${className} rounded-md p-1.5 transition-colors ${
            currentStatus === 'full_takeover'
              ? 'text-orange-500 hover:bg-orange-50' 
              : currentStatus === 'semi_takeover'
              ? 'text-orange-400 hover:bg-orange-50'
              : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
          } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          disabled={isLoading || !conversationId}
          title={currentConfig.description}
        >
          {currentConfig.icon}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56 bg-white dark:bg-gray-800 shadow-lg border border-gray-200">
        <DropdownMenuLabel className="px-3 py-2 text-sm font-semibold text-gray-700">
          接管状态
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {Object.entries(STATUS_CONFIG).map(([status, config]) => {
          const isSelected = status === currentStatus;
          return (
            <DropdownMenuItem
              key={status}
              onClick={() => handleStatusChange(status as TakeoverStatus)}
              disabled={isLoading || isSelected}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors ${
                isSelected 
                  ? 'bg-orange-50 text-orange-700 cursor-default' 
                  : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
              } ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <span className={`flex-shrink-0 ${
                isSelected ? 'text-orange-500' : 'text-gray-500'
              }`}>
                {config.icon}
              </span>
              <div className="flex flex-col flex-1 min-w-0">
                <span className={`text-sm ${
                  isSelected ? 'font-semibold text-orange-700' : 'font-medium text-gray-900'
                }`}>
                  {config.label}
                </span>
                <span className={`text-xs mt-0.5 ${
                  isSelected ? 'text-orange-600' : 'text-gray-500'
                }`}>
                  {config.description}
                </span>
              </div>
              {isSelected && (
                <span className="flex-shrink-0 w-2 h-2 rounded-full bg-orange-500"></span>
              )}
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}