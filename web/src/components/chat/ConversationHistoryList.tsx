'use client';

import { useState, useEffect, useRef } from 'react';
import { cn } from '@/service/utils';
import { getConversations} from '@/service/chatService';
import { Conversation } from '@/types/chat';
import { useAuthContext } from '@/contexts/AuthContext';

interface ConversationHistoryListProps {
  onConversationSelect?: (conversationId: string, customerId: string, tag: string) => void;
  selectedConversationId?: string | null;
}

export default function ConversationHistoryList({ 
  onConversationSelect, 
  selectedConversationId 
}: ConversationHistoryListProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuthContext();

  // 加载会话列表
  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await getConversations();
      setConversations(data);
    } catch {
      setError('获取会话列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      loadConversations();
    }
  }, [user]);

  // 处理会话选择
  const handleConversationSelect = (conversationId: string) => {
    if (onConversationSelect) {
      // 从conversations中获取对应的会话信息
      const conversation = conversations.find(conv => conv.id === conversationId);
      console.log('🔍 [handleConversationSelect] 会话选择处理开始');
      console.log('  - conversation:', conversation);
      if (conversation) {
        // 从会话中提取customerId和tag
        const customerId = conversation.owner_id; // 会话所有者作为customerId
        const tag = conversation.tag; // 会话标签
        console.log('customerId:', customerId);
        console.log('tag:', tag);
        onConversationSelect(conversationId, customerId, tag);
      }
    }
  };


  // 截取内容作为默认标题
  const getDisplayTitle = (conversation: Conversation): string => {
    if (conversation.title) {
      return conversation.title;
    }
    
    // 如果没有标题，使用最后一条消息的内容
    if (conversation.lastMessage?.content) {
      const content = conversation.lastMessage.content;
      // 处理不同类型的消息内容
      let textContent = '';
      if (typeof content === 'string') {
        textContent = content;
      } else if (content && typeof content === 'object' && 'text' in content) {
        textContent = content.text || '';
      } else {
        textContent = JSON.stringify(content);
      }
      return textContent.length > 20 ? textContent.substring(0, 20) + '...' : textContent;
    }
    
    return `会话 ${new Date(conversation.updatedAt).toLocaleDateString()}`;
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
        <span className="ml-2 text-sm text-gray-500">加载历史会话...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-gray-500">
        <p className="text-sm">{error}</p>
        <button
          onClick={loadConversations}
          className="mt-2 rounded-md bg-orange-500 px-3 py-1 text-xs text-white hover:bg-orange-600"
        >
          重试
        </button>
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-gray-500">
        <svg className="h-12 w-12 text-gray-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <p className="text-sm">暂无历史会话</p>
        <p className="text-xs text-gray-400 mt-1">开始新的对话吧</p>
      </div>
    );
  }

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
            {/* 用户头像 */}
            <div className="flex-shrink-0 mr-3">
              <img
                src={conversation.owner?.avatar || '/avatars/default.png'}
                alt={conversation.owner?.name || '用户'}
                className="h-8 w-8 rounded-full bg-gray-100"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.onerror = null;
                  const nameInitial = (conversation.owner?.name || 'U').charAt(0);
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

            {/* 会话信息 */}
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
              {conversation.lastMessage && (
                <p className="text-xs text-gray-500 truncate">
                  {(() => {
                    const content = conversation.lastMessage.content;
                    if (typeof content === 'string') {
                      return content;
                    } else if (content && typeof content === 'object' && 'text' in content) {
                      return content.text || '';
                    } else {
                      return JSON.stringify(content);
                    }
                  })()}
                </p>
              )}
            </div>

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
          </div>
        ))}
      </div>
    </div>
  );
} 