import { useState, useCallback, useRef, useEffect } from 'react'
import { type Message } from '@/types/chat'
import { 
  getConversationMessages, 
  markMessageAsImportant,
  syncConsultantTakeoverStatus
} from '@/service/chatService'

interface UseChatMessagesProps {
  conversationId: string | null
  mounted: React.MutableRefObject<boolean>
}

export function useChatMessages({ conversationId, mounted }: UseChatMessagesProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [importantMessages, setImportantMessages] = useState<Message[]>([])
  const [showImportantOnly, setShowImportantOnly] = useState(false)
  const [isConsultantTakeover, setIsConsultantTakeover] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  // 静默更新消息的方法
  const silentlyUpdateMessages = useCallback(async () => {
    if (!conversationId || !mounted.current) return false

    try {
      const currentMessagesList = [...messages]
      const lastMessageId = currentMessagesList.length > 0 
        ? currentMessagesList[currentMessagesList.length - 1].id 
        : null

      const newMessages = await getConversationMessages(conversationId, true)

      if (!mounted.current) return false

      const hasChanges = newMessages.length > currentMessagesList.length || 
        JSON.stringify(newMessages) !== JSON.stringify(currentMessagesList)
      
      if (hasChanges) {
        console.log('ChatWindow:静默更新，消息有变化，更新UI')
        setMessages(newMessages)
        
        if (showImportantOnly) {
          const important = newMessages.filter(msg => msg.isImportant)
          setImportantMessages(important)
        }

        const newLastMessageId = newMessages.length > 0 
          ? newMessages[newMessages.length - 1].id 
          : null
        
        return lastMessageId !== newLastMessageId
      }

      // 同步顾问状态
      try {
        const isConsultantModeActive = await syncConsultantTakeoverStatus(conversationId)
        if (isConsultantModeActive !== isConsultantTakeover) {
          setIsConsultantTakeover(isConsultantModeActive)
        }
      } catch (error) {
        console.error('ChatWindow:同步顾问状态失败(静默更新中):', error)
      }

      return false
    } catch (error) {
      console.error('ChatWindow:静默获取消息出错:', error)
      return false
    }
  }, [conversationId, showImportantOnly, isConsultantTakeover, messages, mounted])

  // 获取消息
  const fetchMessages = useCallback(async () => {
    console.log(`=================== fetchMessages: conversationId=== ${conversationId}，mounted.current=== ${mounted.current}`)
    if (!conversationId || !mounted.current) return

    try {
      setIsLoading(true)
      
      const messagesData = await getConversationMessages(conversationId, true)
      if (!mounted.current) return

      setMessages(messagesData)
      const important = messagesData.filter(msg => msg.isImportant)
      setImportantMessages(important)

      const isConsultantModeActive = await syncConsultantTakeoverStatus(conversationId)
      setIsConsultantTakeover(isConsultantModeActive)
    } catch (error) {
      console.error('获取消息失败:', error)
    } finally {
      if (mounted.current) {
        setIsLoading(false)
      }
    }
  }, [conversationId, mounted])

  // 切换消息重点标记
  const toggleMessageImportant = useCallback(async (messageId: string, currentStatus = false) => {
    if (!conversationId) return

    try {
      await markMessageAsImportant(conversationId, messageId, !currentStatus)
      await fetchMessages()
    } catch (error) {
      console.error('标记重点消息失败:', error)
    }
  }, [conversationId, fetchMessages])

  // 切换是否只显示重点消息
  const toggleShowImportantOnly = useCallback(() => {
    setShowImportantOnly(prev => !prev)
  }, [])

  // 添加消息到本地状态
  const addMessage = useCallback((message: Message) => {
    setMessages(prev => [...prev, message])
  }, [])

  // 更新消息列表
  const updateMessages = useCallback((newMessages: Message[]) => {
    setMessages(newMessages)
    if (showImportantOnly) {
      const important = newMessages.filter(msg => msg.isImportant)
      setImportantMessages(important)
    }

  }, [showImportantOnly])

  const countRef = useRef(0)
  // 当 conversationId 变化时自动获取消息
  useEffect(() => {
    countRef.current ++
    console.log(`=================== useChatMessages: countRef 变化为 ${countRef.current}，开始获取消息 mounted.current=== ${mounted.current}`)
    if (conversationId && mounted.current) {
      console.log(`useChatMessages: conversationId 变化为 ${conversationId}，开始获取消息`)
      fetchMessages()
    } else if (!conversationId) {
      // 如果没有 conversationId，清空消息
      setMessages([])
      setImportantMessages([])
    }
  }, [conversationId, fetchMessages])

  return {
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
    updateMessages,
    setIsConsultantTakeover
  }
} 
