'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { Conversation, type Message } from '@/types/chat'
import ChatMessage from '@/components/chat/message/ChatMessage'
import { SearchBar } from '@/components/chat/SearchBar'
import MessageInput from '@/components/chat/MessageInput'
import { saveMessage } from '@/service/chatService'
import { useAuthContext } from '@/contexts/AuthContext'
import { MoreHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useSearch } from '@/hooks/useSearch'
import { useConversationTitleEditor } from '@/hooks/useConversationTitleEditor'
// 工具函数
import { getDisplayTitle, groupMessagesByDate } from '@/utils/conversationUtils'

interface ChatWindowProps {
  conversation: Conversation;
  messages: Message[];
  importantMessages: Message[];
  showImportantOnly: boolean;
  loadingMessages: boolean;
  onAction: (action: string, conversationId: string) => void;
  onToggleShowImportantOnly: () => void;
  onToggleMessageImportant: (messageId: string, currentStatus?: boolean) => Promise<void>;
  onLoadMessages: (forceRefresh?: boolean) => Promise<void>;
}

export default function ChatWindow({ 
  conversation, 
  messages, 
  importantMessages,
  showImportantOnly,
  loadingMessages,
  onAction, 
  onToggleShowImportantOnly,
  onToggleMessageImportant,
  onLoadMessages
}: ChatWindowProps) {
  const { user } = useAuthContext();

  // 聊天容器引用
  const chatContainerRef = useRef<HTMLDivElement>(null)

  // 使用标题编辑hook
  const {
    editingTitleId,
    editingTitle,
    editInputRef,
    setEditingTitle,
    startEditTitle,
    saveTitle,
    handleKeyDown
  } = useConversationTitleEditor();

  const {
    showSearch,
    setShowSearch,
    searchTerm,
    searchResults,
    selectedMessageId,
    searchChatMessages,
    goToNextSearchResult,
    goToPreviousSearchResult,
    closeSearch,
    clearSearch
  } = useSearch(messages)

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [])

  // 新消息自动滚动
  useEffect(() => {
    scrollToBottom()
  }, [showImportantOnly ? importantMessages : messages, scrollToBottom])

  // 处理发送消息
  const handleSendMessage = useCallback(async (message: Message) => {
    if (!user) {
      //DODO： Toast 告知用户未登陆，然后系统跳转到登陆页面
    }

    try {
      message.conversationId = conversation.id;
      
      // 立即添加到本地状态以提供即时反馈
      // 这里需要通知父组件添加消息
      setTimeout(scrollToBottom, 100);
      
      // 异步保存到后端
      try {
        const savedMessage = await saveMessage(message);
        message.status = 'sent';
        message.id = savedMessage.id;
      } catch (saveError) {
        message.status = 'failed';
        message.error = saveError instanceof Error ? saveError.message : '发送失败';
        //DODO： Toast 告知用户发送失败
      }
    } catch (error) {
      message.status = 'failed';
      message.error = error instanceof Error ? error.message : '发送失败';
      //DODO： Toast 告知用户发送失败
    }
  }, [conversation.id, user, scrollToBottom])

  // 消息操作回调函数
  const handleToggleImportant = useCallback(async (messageId: string) => {
    try {
      const message = messages.find(msg => msg.id === messageId);
      if (message) {
        await onToggleMessageImportant(messageId, message.is_important || false);
      }
    } catch (error) {
      //DODO： Toast 告知用户标记重点消息失败
    }
  }, [messages, onToggleMessageImportant]);

  const handleReaction = useCallback(async (messageId: string, emoji: string) => {
    //DODO： Toast 告知用户添加响应
  }, []);

  const handleReply = useCallback((message: Message) => {
    //DODO： Toast 告知用户回复消息
  }, []);

  const handleDelete = useCallback(async (messageId: string) => {
    //DODO： Toast 告知用户删除消息
  }, []);

  const handleRetry = useCallback(async (message: Message) => {
    try {
      message.status = 'pending';
      message.error = undefined;
      
      const savedMessage = await saveMessage(message);
      message.status = 'sent';
      message.id = savedMessage.id;
    } catch (error) {
      message.status = 'failed';
      message.error = error instanceof Error ? error.message : '重试发送失败';
      //DODO： Toast 告知用户重试发送失败
    }
  }, []);

  const handleCardAction = useCallback((action: string, data: any) => {
    console.log('卡片操作:', action, data);
  }, []);

  // 按日期分组消息
  const messageGroups = useMemo(() => {
    const displayMessages = showImportantOnly ? importantMessages : messages;
    return groupMessagesByDate(displayMessages);
  }, [showImportantOnly, importantMessages, messages]);

  // 渲染标题编辑区域
  const renderTitleSection = () => (
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
    </div>
  );

  // 渲染重点消息切换按钮
  const renderImportantToggle = () => (
    <button
      className={`rounded-full px-3 py-1 text-xs font-medium flex items-center space-x-1 transition-colors ${
        showImportantOnly 
        ? 'bg-orange-100 text-orange-700 border border-orange-300' 
        : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
      }`}
      onClick={onToggleShowImportantOnly}
    >
      <svg 
        className={`h-4 w-4 ${showImportantOnly ? 'text-orange-500' : 'text-gray-500'}`} 
        fill="currentColor" 
        viewBox="0 0 20 20"
      >
        <path 
          fillRule="evenodd" 
          d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" 
          clipRule="evenodd" 
        />
      </svg>
      <span>
        {showImportantOnly ? '查看全部消息' : '仅显示重点标记'}
        {importantMessages.length > 0 && ` (${importantMessages.length})`}
      </span>
    </button>
  );

  // 渲染消息列表
  const renderMessageList = () => (
    <>
      {messageGroups.map((group) => (
        <div key={group.date} className="space-y-4">
          {/* 日期分隔符 */}
          <div className="flex items-center justify-center my-4">
            <div className="h-px flex-grow bg-gray-200" />
            <div className="mx-4 text-xs text-gray-500">{group.date}</div>
            <div className="h-px flex-grow bg-gray-200" />
          </div>
          
          {/* 消息列表 */}
          {group.messages.map(msg => (
            <ChatMessage
              key={msg.localId || msg.id}
              message={msg}
              isSelected={selectedMessageId === msg.id}
              searchTerm={showSearch ? searchTerm : ''}
              onToggleImportant={handleToggleImportant}
              onReaction={handleReaction}
              onReply={handleReply}
              onDelete={handleDelete}
              onRetry={handleRetry}
              onCardAction={handleCardAction}
            />
          ))}
        </div>
      ))}
    </>
  );

  // 渲染空状态
  const renderEmptyState = () => {
    if (showImportantOnly && importantMessages.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-32 text-gray-500">
          <svg className="h-12 w-12 mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
          <p className="text-sm">暂无标记的重点消息</p>
          <button 
            className="mt-2 text-sm text-orange-500 hover:underline"
            onClick={onToggleShowImportantOnly}
          >
            返回全部消息
          </button>
        </div>
      );
    }

    if (!showImportantOnly && messages.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
          <svg className="h-16 w-16 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-700 mb-2">开始对话</h3>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="flex h-full flex-col">
      {/* 搜索栏 */}
      {showSearch && (
        <SearchBar
          searchTerm={searchTerm}
          searchResults={searchResults}
          selectedMessageId={selectedMessageId}
          onSearchChange={searchChatMessages}
          onClearSearch={clearSearch}
          onNextResult={goToNextSearchResult}
          onPreviousResult={goToPreviousSearchResult}
          onClose={closeSearch}
        />
      )}

      {/* 消息列表顶部按钮 */}
      <div className="border-b border-gray-200 bg-white p-2 shadow-sm flex justify-between">
        {renderTitleSection()}
        {renderImportantToggle()}
        {/* TODO： 更多按钮：1、开关查找聊天内容 2、开关重点消息 3、咨询会话有开关客户资料 4、开关会话设置（添加参与者，搜索群成员，消息免打挠，置顶聊天） */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onAction('more', conversation.id)}
          className="h-8 w-8 p-0"
        >
          <MoreHorizontal className="w-4 h-4" />
        </Button>
      </div>
      
      {/* 聊天记录 */}
      <div 
        ref={chatContainerRef}
        data-chat-container
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {/* 加载状态 */}
        {loadingMessages && (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-2"></div>
              <p className="text-sm text-gray-500">加载消息中...</p>
            </div>
          </div>
        )}
        
        {/* 只有在不加载时才显示内容 */}
        {!loadingMessages && (
          <>
            {renderMessageList()}
            {renderEmptyState()}
          </>
        )}
      </div>
      
      {/* 消息输入组件 */}
      <MessageInput
        conversationId={conversation.id}
        onSendMessage={handleSendMessage}
        toggleSearch={() => setShowSearch(!showSearch)}
        showSearch={showSearch}
        onUpdateMessages={() => {}}
        messages={messages}
      />
    </div>
  )
} 