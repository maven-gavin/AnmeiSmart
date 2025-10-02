import { useState } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Plus, MessageSquare, Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

export interface AgentConversation {
  id: string;
  title: string;
  agentId: string;
  lastMessageAt: Date;
  messageCount: number;
}

interface ConversationHistoryPanelProps {
  agentName: string;
  conversations: AgentConversation[];
  selectedConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onCreateNewChat: () => void;
  isLoading?: boolean;
}

export function ConversationHistoryPanel({
  agentName,
  conversations,
  selectedConversationId,
  onSelectConversation,
  onCreateNewChat,
  isLoading = false,
}: ConversationHistoryPanelProps) {
  return (
    <div className="flex h-full w-80 flex-col border-r border-gray-200 bg-white">
      {/* Header with Agent Name */}
      <div className="border-b border-gray-200 p-4">
        <div className="mb-3 flex items-center space-x-2">
          <MessageSquare className="h-5 w-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">{agentName}</h2>
        </div>

        {/* Start New Chat Button */}
        <Button
          onClick={onCreateNewChat}
          className="w-full bg-blue-600 hover:bg-blue-700"
          size="sm"
        >
          <Plus className="mr-2 h-4 w-4" />
          Start New chat
        </Button>
      </div>

      {/* Conversation List */}
      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="flex items-center justify-center p-8">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent" />
              <p className="mt-2 text-sm text-gray-500">加载中...</p>
            </div>
          </div>
        ) : conversations.length > 0 ? (
          <div className="space-y-1 p-2">
            {conversations.map((conversation) => {
              const isSelected = selectedConversationId === conversation.id;
              
              return (
                <button
                  key={conversation.id}
                  onClick={() => onSelectConversation(conversation.id)}
                  className={cn(
                    'w-full rounded-lg p-3 text-left transition-colors',
                    isSelected
                      ? 'bg-blue-50 border border-blue-200'
                      : 'hover:bg-gray-50 border border-transparent'
                  )}
                >
                  <div className="mb-1 line-clamp-2 text-sm font-medium text-gray-900">
                    {conversation.title}
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    <Calendar className="h-3 w-3" />
                    <span>
                      {(() => {
                        try {
                          return formatDistanceToNow(conversation.lastMessageAt, {
                            addSuffix: true,
                            locale: zhCN,
                          });
                        } catch (error) {
                          console.warn('日期格式化失败:', conversation.lastMessageAt, error);
                          return '刚刚';
                        }
                      })()}
                    </span>
                    <span>·</span>
                    <span>{conversation.messageCount} 条消息</span>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <MessageSquare className="mb-3 h-12 w-12 text-gray-300" />
            <p className="mb-1 text-sm font-medium text-gray-900">
              暂无对话记录
            </p>
            <p className="text-xs text-gray-500">
              点击"Start New chat"开始新对话
            </p>
          </div>
        )}
      </ScrollArea>
    </div>
  );
}

