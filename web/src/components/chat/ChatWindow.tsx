'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { type Message } from '@/types/chat'
import ChatMessage from '@/components/chat/ChatMessage'
import { SearchBar } from '@/components/chat/SearchBar'
import { ConnectionStatusIndicator } from '@/components/chat/ConnectionStatus'
import MessageInput from '@/components/chat/MessageInput'
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
  console.log('ChatWindow 组件正在渲染，conversationId:', conversationId)
  
  const router = useRouter();
  const searchParams = useSearchParams()
  const { user } = useAuthContext();
  
  console.log('ChatWindow 组件状态:', { 
    hasRouter: !!router, 
    hasSearchParams: !!searchParams, 
    hasUser: !!user 
  })
  
  // 基本状态
  const [message, setMessage] = useState('')
  const [showFAQ, setShowFAQ] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)
  
  // 当前对话ID
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(
    conversationId || searchParams?.get('conversationId') || null
  )
  
  // 用户角色状态
  const isConsultant = user?.currentRole === 'consultant'
  
  // 聊天区域引用和挂载状态
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const mounted = useRef(false)

  // 组件挂载状态管理
  useEffect(() => {
    mounted.current = true
    console.log('ChatWindow: 组件实际挂载, mounted=true')
    
    return () => {
      mounted.current = false
      console.log('ChatWindow: 组件实际卸载, mounted=false')
    }
  }, [])


  // 使用自定义hooks
  const {
    messages,
    importantMessages,
    showImportantOnly,
    isConsultantTakeover,
    silentlyUpdateMessages,
    toggleMessageImportant,
    toggleShowImportantOnly,
    addMessage,
    setIsConsultantTakeover
  } = useChatMessages({ conversationId: currentConversationId, mounted })

  const {
    imagePreview,
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
    cancelRecording
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
  const handleWebSocketMessage = useCallback(async (data: unknown) => {
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
    console.log('handleSendMessage 函数被调用了！')
    console.log('函数内部状态:', { isSending, imagePreview, audioPreview })
    
    if (isSending) {
      console.log('当前正在发送中，忽略此次点击')
      return
    }

    // 根据消息类型发送
    if (imagePreview) {
      console.log('发送图片消息')
      await handleSendImageMessage()
    } else if (audioPreview) {
      console.log('发送语音消息')
      await handleSendVoiceMessage()
    } else {
      console.log('发送文本消息')
      console.log('准备调用 handleSendTextMessage...')
      console.log('当前message值:', message)
      try {
        await handleSendTextMessage(message)
        console.log('handleSendTextMessage 调用完成')
      } catch (error) {
        console.error('handleSendTextMessage 调用出错:', error)
      }
    }
  }, [isSending, imagePreview, audioPreview, message])

  const handleSendTextMessage = useCallback(async (currentMessage?: string) => {
    // 使用参数传入的消息或当前的message状态
    const messageToSend = currentMessage || message;
    
    console.log('🔥 handleSendTextMessage 函数开始执行')
    console.log('🔥 函数内变量检查:', { 
      currentMessage,
      message,
      messageToSend,
      messageLength: messageToSend?.length, 
      messageTrim: messageToSend?.trim(), 
      isSending 
    })
    
    if (!messageToSend.trim() || isSending) {
      console.log('🔥 提前返回: message为空或正在发送中')
      return
    }

    console.log('=== 开始发送消息 ===')
    console.log('消息内容:', messageToSend)
    console.log('当前会话ID:', currentConversationId)
    console.log('用户信息:', user)
    console.log('WebSocket状态:', wsStatus)
    console.log('顾问接管状态:', isConsultantTakeover)

    // 检查用户认证状态
    if (!user) {
      console.error('发送失败: 用户未登录')
      setSendError('用户未登录，请重新登录')
      return
    }

    // 清除之前的错误
    setSendError(null)

    // 如果没有会话ID，创建一个新会话
    if (!currentConversationId) {
      try {
        console.log('没有会话ID，正在创建新会话...')
        setIsSending(true)
        const conversation = await getOrCreateConversation()
        console.log('新会话创建成功:', conversation)
        setCurrentConversationId(conversation.id)
        
        router.replace(`?conversationId=${conversation.id}`, { scroll: false })
        
        // 延迟发送消息
        setTimeout(async () => {
          console.log('延迟发送消息，会话ID:', conversation.id)
          await sendMessageDirectly(conversation.id, messageToSend)
        }, 800)
      } catch (error) {
        console.error('创建会话失败:', error)
        setSendError('创建会话失败，请稍后重试')
        setIsSending(false)
      }
    } else {
      await sendMessageDirectly(currentConversationId, messageToSend)
    }

    // 直接发送消息的内联函数
    async function sendMessageDirectly(conversationId: string, msgContent: string) {
      try {
        console.log('=== 发送消息到会话 ===')
        console.log('会话ID:', conversationId)
        console.log('消息内容:', msgContent)
        
        setIsSending(true)
        
        // 发送用户消息
        console.log('正在发送用户消息...')
        const userMessage = await sendTextMessage(conversationId, msgContent)
        console.log('用户消息发送成功:', userMessage)
        
        addMessage(userMessage)
        setMessage('')
        scrollToBottom()
        
        // 在顾问未接管的情况下获取AI回复
        if (!isConsultantTakeover) {
          try {
            console.log('正在获取AI回复...')
            const aiResponsePromise = getAIResponse(conversationId, userMessage)
            const timeoutPromise = new Promise<null>((_, reject) => 
              setTimeout(() => reject(new Error('获取AI回复超时')), 15000)
            )
            
            const aiResponse = await Promise.race([aiResponsePromise, timeoutPromise])
            
            if (aiResponse) {
              console.log('AI回复获取成功:', aiResponse)
              addMessage(aiResponse)
              scrollToBottom()
            } else {
              console.log('未收到AI回复')
            }
          } catch (error) {
            console.error('获取AI回复失败:', error)
          }
        } else {
          console.log('顾问已接管，跳过AI回复')
        }
      } catch (error) {
        console.error('发送消息失败:', error)
        // 添加用户友好的错误提示
        if (error instanceof Error) {
          console.error('错误详情:', error.message)
          setSendError(`发送失败: ${error.message}`)
        } else {
          setSendError('发送消息失败，请稍后重试')
        }
      } finally {
        setIsSending(false)
      }
    }
  }, [message, isSending, currentConversationId, router, user, wsStatus, isConsultantTakeover, addMessage, scrollToBottom])

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
    } catch (error) {
      console.error('切换顾问模式失败:', error)
    }
  }, [currentConversationId, isConsultantTakeover, setIsConsultantTakeover])

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
      
      {/* 隐藏的文件输入 */}
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept="image/*"
        onChange={handleImageUpload}
      />
      
      {/* 使用MessageInput组件替换原来的输入区域 */}
      <MessageInput
        message={message}
        setMessage={setMessage}
        imagePreview={imagePreview}
        audioPreview={audioPreview}
        isRecording={isRecording}
        recordingTime={recordingTime}
        isSending={isSending}
        handleSendMessage={handleSendMessage}
        startRecording={handleStartRecording}
        stopRecording={handleStopRecording}
        cancelRecording={cancelRecording}
        cancelImagePreview={cancelImagePreview}
        cancelAudioPreview={cancelAudioPreview}
        triggerFileSelect={triggerFileSelect}
        toggleFAQ={() => setShowFAQ(!showFAQ)}
        toggleSearch={() => setShowSearch(!showSearch)}
        isConsultant={isConsultant}
        isConsultantTakeover={isConsultantTakeover}
        toggleConsultantMode={toggleConsultantMode}
        showFAQ={showFAQ}
        showSearch={showSearch}
        sendError={sendError}
        setSendError={setSendError}
      />
    </div>
  )
} 