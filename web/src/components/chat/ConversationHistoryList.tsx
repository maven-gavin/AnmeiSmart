'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { cn } from '@/service/utils';
import { getConversations, updateConversationTitle } from '@/service/chatService';
import { Conversation } from '@/types/chat';
import { useAuthContext } from '@/contexts/AuthContext';

interface ConversationHistoryListProps {
  onConversationSelect?: (conversationId: string) => void;
  selectedConversationId?: string | null;
}

export default function ConversationHistoryList({ 
  onConversationSelect, 
  selectedConversationId 
}: ConversationHistoryListProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingTitleId, setEditingTitleId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const router = useRouter();
  const { user } = useAuthContext();
  const editInputRef = useRef<HTMLInputElement>(null);

  // 加载会话列表
  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await getConversations();
      // 按创建时间倒序排列，最新的在最上面
      const sortedConversations = data.sort((a, b) => 
        new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
      );
      setConversations(sortedConversations);
    } catch (err) {
      console.error('获取会话列表失败:', err);
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
      onConversationSelect(conversationId);
    } else {
      // 默认行为：更新URL
      router.push(`/customer/chat?conversationId=${conversationId}`);
    }
  };

  // 开始编辑标题
  const startEditTitle = (conversation: Conversation, e: React.MouseEvent) => {
    e.stopPropagation(); // 阻止选择会话
    setEditingTitleId(conversation.id);
    setEditingTitle(conversation.title || '');
    setTimeout(() => {
      editInputRef.current?.focus();
      editInputRef.current?.select();
    }, 0);
  };

  // 保存标题
  const saveTitle = async (conversationId: string) => {
    if (!editingTitle.trim()) {
      cancelEditTitle();
      return;
    }

    try {
      await updateConversationTitle(conversationId, editingTitle.trim());
      
      // 更新本地状态
      setConversations(prev => prev.map(conv => 
        conv.id === conversationId 
          ? { ...conv, title: editingTitle.trim() }
          : conv
      ));
      
      setEditingTitleId(null);
      setEditingTitle('');
    } catch (error) {
      console.error('更新会话标题失败:', error);
      // 可以添加错误提示
    }
  };

  // 取消编辑
  const cancelEditTitle = () => {
    setEditingTitleId(null);
    setEditingTitle('');
  };

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent, conversationId: string) => {
    if (e.key === 'Enter') {
      saveTitle(conversationId);
    } else if (e.key === 'Escape') {
      cancelEditTitle();
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
      return content.length > 20 ? content.substring(0, 20) + '...' : content;
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
                src={conversation.user.avatar}
                alt={conversation.user.name}
                className="h-8 w-8 rounded-full bg-gray-100"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.onerror = null;
                  const nameInitial = conversation.user.name.charAt(0);
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
                {editingTitleId === conversation.id ? (
                  <input
                    ref={editInputRef}
                    type="text"
                    value={editingTitle}
                    onChange={(e) => setEditingTitle(e.target.value)}
                    onBlur={() => saveTitle(conversation.id)}
                    onKeyDown={(e) => handleKeyDown(e, conversation.id)}
                    className="flex-1 text-sm font-medium bg-white border border-orange-300 rounded px-2 py-1 focus:outline-none focus:border-orange-500"
                    onClick={(e) => e.stopPropagation()}
                  />
                ) : (
                  <h4 
                    className="text-sm font-medium text-gray-800 truncate cursor-pointer hover:text-orange-600"
                    onClick={(e) => startEditTitle(conversation, e)}
                    title="点击编辑标题"
                  >
                    {getDisplayTitle(conversation)}
                  </h4>
                )}
                
                <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
                  {new Date(conversation.updatedAt).toLocaleDateString()}
                </span>
              </div>

              {/* 最后一条消息 */}
              {conversation.lastMessage && (
                <p className="text-xs text-gray-500 truncate">
                  {conversation.lastMessage.content}
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
          </div>
        ))}
      </div>
    </div>
  );
} 