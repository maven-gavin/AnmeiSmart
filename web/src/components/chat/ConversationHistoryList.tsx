'use client';

import { cn } from '@/service/utils';
import { Conversation } from '@/types/chat';
import { getDisplayTitle, formatMessageContent } from '@/utils/conversationUtils';

interface ConversationHistoryListProps {
  conversations: Conversation[];
  isLoading: boolean;
  selectedConversationId?: string | null;
  onConversationSelect?: (conversationId: string) => void;
}

export default function ConversationHistoryList({ 
  conversations,
  isLoading,
  selectedConversationId,
  onConversationSelect
}: ConversationHistoryListProps) {
  // 处理会话选择
  const handleConversationSelect = (conversationId: string) => {
    onConversationSelect?.(conversationId);
  };

  // 渲染头像组件
  const renderAvatar = (conversation: Conversation) => {
    const { owner } = conversation;
    const nameInitial = (owner?.name || 'U').charAt(0);
    
    return (
      <div className="flex-shrink-0 mr-3">
        <img
          src={owner?.avatar || '/avatars/default.png'}
          alt={owner?.name || '用户'}
          className="h-8 w-8 rounded-full bg-gray-100"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.onerror = null;
            target.style.display = 'flex';
            target.style.alignItems = 'center';
            target.style.justifyContent = 'center';
            target.style.backgroundColor = '#FF9800';
            target.style.color = '#FFFFFF';
            target.style.fontSize = '12px';
            target.style.fontWeight = 'bold';
            target.src = 'data:image/svg+xml;charset=UTF-8,' + 
              encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"></svg>');
            setTimeout(() => {
              (target.parentNode as HTMLElement).innerHTML = 
                `<div class="h-8 w-8 rounded-full flex items-center justify-center text-white text-xs font-bold" style="background-color: #FF9800">${nameInitial}</div>`;
            }, 0);
          }}
        />
      </div>
    );
  };

  // 渲染会话信息
  const renderConversationInfo = (conversation: Conversation) => {
    const lastMessageContent = conversation.lastMessage 
      ? formatMessageContent(conversation.lastMessage.content)
      : '';

    return (
      <div className="flex-1 min-w-0">
        {/* 标题行 */}
        <div className="flex items-center justify-between mb-1">
          <h4 className="text-sm font-medium text-gray-800 truncate cursor-pointer hover:text-orange-600">
            {getDisplayTitle(conversation)}
          </h4>
          <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
            {new Date(conversation.updatedAt).toLocaleDateString()}
          </span>
        </div>

        {/* 最后一条消息 */}
        {lastMessageContent && (
          <p className="text-xs text-gray-500 truncate">
            {lastMessageContent}
          </p>
        )}
      </div>
    );
  };

  // 渲染标签
  const renderTags = (conversation: Conversation) => (
    <>
      {/* 未读消息数 */}
      {conversation.unreadCount > 0 && (
        <div className="flex-shrink-0 ml-2">
          <span className="inline-flex items-center justify-center h-5 w-5 text-xs font-medium text-white bg-red-500 rounded-full">
            {conversation.unreadCount}
          </span>
        </div>
      )}
      
      {/* 咨询标签 */}
      {conversation.tag === 'consultation' && (
        <div className="flex-shrink-0 ml-2">
          <span className="inline-flex items-center justify-center h-5 w-5 text-xs font-medium text-white bg-red-500 rounded-full">
            {conversation.tag}
          </span>
        </div>
      )}
    </>
  );

  // 渲染加载状态
  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
        <span className="ml-2 text-sm text-gray-500">加载历史会话...</span>
      </div>
    );
  }

  // 渲染空状态
  if (conversations.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-gray-500">
        <svg className="h-12 w-12 text-gray-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <p className="text-sm">暂无历史会话</p>
      </div>
    );
  }

  // 渲染会话列表
  return (
    <div className="h-full flex flex-col">
      {/* 标题 */}
      <div className="p-3 border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-700">消息</h3>
      </div>

      {/* 会话列表 */}
      <div className="flex-1 overflow-y-auto">
        {conversations.map(conversation => (
          <div
            key={conversation.id}
            onClick={() => handleConversationSelect(conversation.id)}
            className={cn(
              'flex items-center p-3 border-b border-gray-100 cursor-pointer transition-colors',
              selectedConversationId === conversation.id 
                ? 'bg-orange-50 border-orange-200' 
                : 'hover:bg-gray-50'
            )}
          >
            {renderAvatar(conversation)}
            {renderConversationInfo(conversation)}
            {renderTags(conversation)}
          </div>
        ))}
      </div>
    </div>
  );
} 