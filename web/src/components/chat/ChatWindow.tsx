'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { type Message } from '@/types/chat'
import ChatMessage from '@/components/chat/message/ChatMessage'
import { SearchBar } from '@/components/chat/SearchBar'
import MessageInput from '@/components/chat/MessageInput'
import { getOrCreateConversation } from '@/service/chatService'
import { useAuthContext } from '@/contexts/AuthContext'
import { useSearchParams, useRouter } from 'next/navigation'

// 自定义hooks
import { useChatMessages } from '@/hooks/useChatMessages'
import { useWebSocketByPage } from '@/hooks/useWebSocketByPage'
import { useSearch } from '@/hooks/useSearch'

interface ChatWindowProps {
  conversationId?: string;
}

export default function ChatWindow({ conversationId }: ChatWindowProps) {
  const router = useRouter();
  const searchParams = useSearchParams()
  const { user } = useAuthContext();
  
  // 状态管理
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(
    conversationId || searchParams?.get('conversationId') || null
  )
  
  // 引用和挂载状态
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const mounted = useRef(false)

  // 组件挂载状态管理
  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])

  // 自定义hooks
  const {
    messages,
    importantMessages,
    showImportantOnly,
    silentlyUpdateMessages,
    toggleShowImportantOnly,
    addMessage
  } = useChatMessages({ conversationId: currentConversationId, mounted })

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

  // 使用页面级WebSocket架构
  const { lastMessage } = useWebSocketByPage()

  // 监听conversationId变化
  useEffect(() => {
    if (conversationId) {
      if (conversationId !== currentConversationId) {
        setCurrentConversationId(conversationId)
      }
    } else {
      const urlConversationId = searchParams?.get('conversationId')
      if (urlConversationId && urlConversationId !== currentConversationId) {
        setCurrentConversationId(urlConversationId)
      }
    }
  }, [conversationId, searchParams, currentConversationId])

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [])

  // 监听WebSocket消息
  useEffect(() => {
    if (!lastMessage || !currentConversationId) return

    if (lastMessage.action === 'new_message' && 
        lastMessage.data?.conversation_id === currentConversationId) {
      silentlyUpdateMessages().then(hasNewMessage => {
        if (hasNewMessage) {
          setTimeout(scrollToBottom, 100)
        }
      }).catch(error => {
        console.error('更新消息失败:', error)
      })
    }
  }, [lastMessage, currentConversationId, silentlyUpdateMessages, scrollToBottom])

  // 新消息自动滚动
  useEffect(() => {
    scrollToBottom()
  }, [showImportantOnly ? importantMessages : messages, scrollToBottom])

  // 处理发送消息
  const handleSendMessage = useCallback(async (message: Message) => {
    if (!user) {
      throw new Error('用户未登录，请重新登录')
    }

    let targetConversationId = currentConversationId

    try {
      // 如果没有会话ID，创建新会话
      if (!targetConversationId) {
        const conversation = await getOrCreateConversation()
        targetConversationId = conversation.id
        setCurrentConversationId(conversation.id)
        router.replace(`?conversationId=${conversation.id}`, { scroll: false })
      }

      message.conversationId = targetConversationId;
      addMessage(message);
      setTimeout(scrollToBottom, 100)
      
    } catch (error) {
      console.error('处理消息发送失败:', error)
    }
  }, [currentConversationId, router, user, scrollToBottom])

  // 按日期分组消息
  const messageGroups = useMemo(() => {
    const formatMessageDate = (timestamp: string): string => {
      const date = new Date(timestamp)
      const today = new Date()
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)
      
      if (date.toDateString() === today.toDateString()) {
        return '今天'
      } else if (date.toDateString() === yesterday.toDateString()) {
        return '昨天'
      } else {
        return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
      }
    }

    const messagesToGroup = showImportantOnly ? importantMessages : messages
    const groups: { date: string; messages: Message[] }[] = []
    
    messagesToGroup.forEach((msg: Message) => {
      const dateStr = formatMessageDate(msg.timestamp)
      
      let group = groups.find(g => g.date === dateStr)
      if (!group) {
        group = { date: dateStr, messages: [] }
        groups.push(group)
      }
      
      group.messages.push(msg)
    })
    
    return groups
  }, [showImportantOnly, importantMessages, messages])

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
      
      {/* 聊天记录 */}
      <div 
        ref={chatContainerRef}
        data-chat-container
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {/* 重点消息切换按钮 */}
        {importantMessages.length > 0 && (
          <div className="sticky top-0 z-10 mb-2 flex justify-end">
            <button
              className={`rounded-full px-3 py-1 text-xs font-medium flex items-center space-x-1 transition-colors ${
                showImportantOnly 
                ? 'bg-orange-100 text-orange-700 border border-orange-300' 
                : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
              }`}
              onClick={toggleShowImportantOnly}
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
              <span>{showImportantOnly ? '查看全部消息' : '仅显示重点标记'}</span>
            </button>
          </div>
        )}

        {/* 分组消息列表 */}
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
              />
            ))}
          </div>
        ))}
        
        {/* 空状态 */}
        {showImportantOnly && importantMessages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-32 text-gray-500">
            <svg className="h-12 w-12 mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            <p className="text-sm">暂无标记的重点消息</p>
            <button 
              className="mt-2 text-sm text-orange-500 hover:underline"
              onClick={() => toggleShowImportantOnly()}
            >
              返回全部消息
            </button>
          </div>
        )}
      </div>
      
      {/* 消息输入组件 */}
      <MessageInput
        conversationId={currentConversationId}
        onSendMessage={handleSendMessage}
        toggleSearch={() => setShowSearch(!showSearch)}
        showSearch={showSearch}
        onUpdateMessages={silentlyUpdateMessages}
        messages={messages}
      />
    </div>
  )
} 