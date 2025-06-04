'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { type Message } from '@/types/chat'
import ChatMessage from '@/components/chat/ChatMessage'
import { SearchBar } from '@/components/chat/SearchBar'
import { ConnectionStatusIndicator } from '@/components/chat/ConnectionStatus'
import { MediaPreview } from '@/components/chat/MediaPreview'
import { RecordingControls } from '@/components/chat/RecordingControls'
import { 
  sendTextMessage, 
  sendImageMessage, 
  sendVoiceMessage,
  getAIResponse,
  takeoverConversation,
  switchBackToAI,
  getOrCreateConversation
} from '@/service/chatService'
import { useAuthContext } from '@/contexts/AuthContext'
import { useSearchParams, useRouter } from 'next/navigation'
import FAQSection, { type FAQ } from './FAQSection'

// 自定义hooks
import { useChatMessages } from '@/hooks/useChatMessages'
import { useWebSocketConnection } from '@/hooks/useWebSocketConnection'
import { useMediaUpload } from '@/hooks/useMediaUpload'
import { useRecording } from '@/hooks/useRecording'
import { useSearch } from '@/hooks/useSearch'

interface ChatWindowProps {
  conversationId?: string;
}

export default function ChatWindow({ conversationId }: ChatWindowProps) {
  const router = useRouter();
  const searchParams = useSearchParams()
  const { user } = useAuthContext();
  
  // 基本状态
  const [message, setMessage] = useState('')
  const [showFAQ, setShowFAQ] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [isSending, setIsSending] = useState(false)
  
  // 当前对话ID
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(
    conversationId || searchParams?.get('conversationId') || null
  )
  
  // 用户角色状态
  const isConsultant = user?.currentRole === 'consultant'
  
  // 聊天区域引用和挂载状态
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const mounted = useRef(false)

  // 使用自定义hooks
  const {
    messages,
    importantMessages,
    showImportantOnly,
    isConsultantTakeover,
    isLoading,
    silentlyUpdateMessages,
    fetchMessages,
    toggleMessageImportant,
    toggleShowImportantOnly,
    addMessage,
    setIsConsultantTakeover
  } = useChatMessages({ conversationId: currentConversationId, mounted })

  const {
    imagePreview,
    uploadingImage,
    fileInputRef,
    handleImageUpload,
    cancelImagePreview,
    triggerFileSelect,
    audioPreview,
    setAudioPreview,
    cancelAudioPreview
  } = useMediaUpload()

  const {
    isRecording,
    recordingTime,
    startRecording,
    stopRecording,
    cancelRecording,
    formatRecordingTime
  } = useRecording()

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

  // TODO： data 值没有使用，为什么不是从Socket中获取？
  // WebSocket消息处理回调
  const handleWebSocketMessage = useCallback(async (data: any) => {
    console.log(`ChatWindow收到当前会话的WebSocket消息:`, data)
    
    try {
      const hasNewMessage = await silentlyUpdateMessages()
      if (hasNewMessage) {
        setTimeout(scrollToBottom, 100)
      }
    } catch (error) {
      console.error('更新消息失败:', error)
    }
  }, [silentlyUpdateMessages])

  // TODO： 为什么需要传uerId，这个不是从token中获取的吗？这里应该就是WebSocket初始配置
  const { wsStatus, reconnectWebSocket } = useWebSocketConnection({
    userId: user?.id,
    conversationId: currentConversationId,
    mounted,
    onMessageReceived: handleWebSocketMessage
  })

  // 监听props/searchParams中的conversationId变化
  useEffect(() => {
    if (conversationId) {
      if (conversationId !== currentConversationId) {
        console.log(`ChatWindow props中的conversationId变化: ${conversationId}`)
        setCurrentConversationId(conversationId)
      }
    } else {
      const urlConversationId = searchParams?.get('conversationId')
      if (urlConversationId && urlConversationId !== currentConversationId) {
        console.log(`ChatWindow URL中的conversationId变化: ${urlConversationId}`)
        setCurrentConversationId(urlConversationId)
      }
    }
  }, [conversationId, searchParams, currentConversationId])

  // 组件挂载状态管理
  useEffect(() => {
    mounted.current = true
    console.log('ChatWindow: 组件实际挂载, mounted=true')
    
    return () => {
      mounted.current = false
      console.log('ChatWindow: 组件实际卸载, mounted=false')
    }
  }, [])

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [])

  // 新消息自动滚动到底部
  useEffect(() => {
    scrollToBottom()
  }, [showImportantOnly ? importantMessages : messages, scrollToBottom])

  // 插入FAQ内容
  const insertFAQ = useCallback((faq: FAQ) => {
    setMessage(faq.question)
    setShowFAQ(false)
  }, [])

  // 消息发送逻辑
  const handleSendMessage = useCallback(async () => {
    if (isSending) return

    // 根据消息类型发送
    if (imagePreview) {
      await handleSendImageMessage()
    } else if (audioPreview) {
      await handleSendVoiceMessage()
    } else {
      await handleSendTextMessage()
    }
  }, [isSending, imagePreview, audioPreview])

  const handleSendTextMessage = useCallback(async () => {
    if (!message.trim() || isSending) return

    // 如果没有会话ID，创建一个新会话
    if (!currentConversationId) {
      try {
        setIsSending(true)
        const conversation = await getOrCreateConversation()
        setCurrentConversationId(conversation.id)
        
        router.replace(`?conversationId=${conversation.id}`, { scroll: false })
        
        // 延迟发送消息
        setTimeout(async () => {
          await sendMessageWithId(conversation.id)
        }, 800)
      } catch (error) {
        console.error('创建会话失败:', error)
        setIsSending(false)
      }
    } else {
      await sendMessageWithId(currentConversationId)
    }
  }, [message, isSending, currentConversationId, router])

  const sendMessageWithId = useCallback(async (conversationId: string) => {
    try {
      setIsSending(true)
      
      // 发送用户消息
      const userMessage = await sendTextMessage(conversationId, message)
      addMessage(userMessage)
      setMessage('')
      scrollToBottom()
      
      // 在顾问未接管的情况下获取AI回复
      if (!isConsultantTakeover) {
        try {
          const aiResponsePromise = getAIResponse(conversationId, userMessage)
          const timeoutPromise = new Promise<null>((_, reject) => 
            setTimeout(() => reject(new Error('获取AI回复超时')), 15000)
          )
          
          const aiResponse = await Promise.race([aiResponsePromise, timeoutPromise])
          
          if (aiResponse) {
            addMessage(aiResponse)
            scrollToBottom()
          }
        } catch (error) {
          console.error('获取AI回复失败:', error)
        }
      }
    } catch (error) {
      console.error('发送消息失败:', error)
    } finally {
      setIsSending(false)
    }
  }, [addMessage, scrollToBottom, isConsultantTakeover])

  const handleSendImageMessage = useCallback(async () => {
    if (!imagePreview || !currentConversationId || isSending) return
    
    setIsSending(true)
    try {
      await sendImageMessage(currentConversationId, imagePreview)
      cancelImagePreview()
      silentlyUpdateMessages()
    } catch (error) {
      console.error('发送图片失败:', error)
    } finally {
      setIsSending(false)
    }
  }, [imagePreview, currentConversationId, isSending, cancelImagePreview, silentlyUpdateMessages])

  const handleSendVoiceMessage = useCallback(async () => {
    if (!audioPreview || !currentConversationId || isSending) return
    
    setIsSending(true)
    try {
      await sendVoiceMessage(currentConversationId, audioPreview)
      cancelAudioPreview()
      silentlyUpdateMessages()
    } catch (error) {
      console.error('发送语音失败:', error)
    } finally {
      setIsSending(false)
    }
  }, [audioPreview, currentConversationId, isSending, cancelAudioPreview, silentlyUpdateMessages])

  // 录音处理
  const handleStartRecording = useCallback(async () => {
    cancelAudioPreview()
    await startRecording()
  }, [startRecording, cancelAudioPreview])

  const handleStopRecording = useCallback(async () => {
    const audioUrl = await stopRecording()
    if (audioUrl) {
      setAudioPreview(audioUrl)
    }
  }, [stopRecording, setAudioPreview])

  // 切换顾问接管状态
  const toggleConsultantMode = useCallback(async () => {
    if (!currentConversationId) return

    try {
      if (isConsultantTakeover) {
        const success = await switchBackToAI(currentConversationId)
        if (success) {
          setIsConsultantTakeover(false)
        }
      } else {
        const success = await takeoverConversation(currentConversationId)
        if (success) {
          setIsConsultantTakeover(true)
        }
      }
      fetchMessages()
    } catch (error) {
      console.error('切换顾问模式失败:', error)
    }
  }, [currentConversationId, isConsultantTakeover, setIsConsultantTakeover, fetchMessages])

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
      
      {/* WebSocket连接状态指示器 */}
      <ConnectionStatusIndicator 
        wsStatus={wsStatus} 
        onReconnect={reconnectWebSocket} 
      />
      
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
              className={`rounded-full px-3 py-1 text-xs font-medium flex items-center space-x-1 ${
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

        {/* 显示分组后的消息列表 */}
        {messageGroups.map((group) => (
          <div key={group.date} className="space-y-4">
            {/* 日期分隔符 */}
            <div className="flex items-center justify-center my-4">
              <div className="h-px flex-grow bg-gray-200" />
              <div className="mx-4 text-xs text-gray-500">{group.date}</div>
              <div className="h-px flex-grow bg-gray-200" />
            </div>
            
            {/* 当前日期组的消息 */}
            {group.messages.map(msg => (
              <ChatMessage
                key={msg.id}
                message={msg}
                isSelected={selectedMessageId === msg.id}
                searchTerm={showSearch ? searchTerm : ''}
                onToggleImportant={toggleMessageImportant}
              />
            ))}
          </div>
        ))}
        
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
      
      {/* FAQ快捷入口 */}
      {showFAQ && (
        <FAQSection 
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          insertFAQ={insertFAQ}
          closeFAQ={() => setShowFAQ(false)}
          messages={messages}
        />
      )}
      
      {/* 录音状态 */}
      <RecordingControls
        isRecording={isRecording}
        recordingTime={recordingTime}
        formatRecordingTime={formatRecordingTime}
        onCancel={cancelRecording}
        onStop={handleStopRecording}
      />
      
      {/* 媒体预览 */}
      <MediaPreview
        imagePreview={imagePreview}
        audioPreview={audioPreview}
        onCancelImage={cancelImagePreview}
        onCancelAudio={cancelAudioPreview}
      />
      
      {/* 隐藏的文件输入 */}
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept="image/*"
        onChange={handleImageUpload}
      />
      
      {/* 输入区域 */}
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="flex space-x-4">
          <button 
            className={`flex-shrink-0 ${showFAQ ? 'text-orange-500' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setShowFAQ(!showFAQ)}
            title="常见问题"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
          
          <button 
            className={`flex-shrink-0 ${showSearch ? 'text-orange-500' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setShowSearch(!showSearch)}
            title="搜索聊天记录"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
          
          {/* 顾问接管按钮 */}
          {isConsultant && (
            <button 
              className={`flex-shrink-0 ${isConsultantTakeover ? 'text-green-500' : 'text-gray-500 hover:text-gray-700'}`}
              onClick={toggleConsultantMode}
              title={isConsultantTakeover ? "切换回AI助手" : "顾问接管"}
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={isConsultantTakeover 
                    ? "M13 10V3L4 14h7v7l9-11h-7z"
                    : "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  }
                />
              </svg>
            </button>
          )}
                    
          <button className="flex-shrink-0 text-gray-500 hover:text-gray-700" title="表情">
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
          
          <button 
            className={`flex-shrink-0 text-gray-500 hover:text-gray-700`}
            title="图片"
            onClick={triggerFileSelect}
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {uploadingImage && (
              <span className="absolute w-3 h-3 rounded-full bg-orange-500 animate-ping" />
            )}
          </button>
          
          <button 
            className={`flex-shrink-0 ${isRecording ? 'text-red-500' : 'text-gray-500 hover:text-gray-700'}`}
            title="语音"
            onClick={isRecording ? handleStopRecording : handleStartRecording}
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 016 0v6a3 3 0 01-3 3z" />
            </svg>
          </button>
          
          <div className="flex flex-1 items-center space-x-2">
            <input
              type="text"
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="输入消息..."
              className="flex-1 rounded-lg border border-gray-200 px-4 py-2 focus:border-orange-500 focus:outline-none"
              disabled={isRecording || isSending}
              onKeyPress={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage()
                }
              }}
            />
            <Button
              onClick={handleSendMessage}
              disabled={isRecording || isSending || (!message.trim() && !imagePreview && !audioPreview)}
              className={isSending ? 'opacity-70 cursor-not-allowed' : ''}
            >
              {isSending ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  发送中
                </span>
              ) : '发送'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
} 