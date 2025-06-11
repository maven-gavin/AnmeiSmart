import { useState, useCallback, useRef, useEffect } from 'react'
import toast from 'react-hot-toast'
import { type Message } from '@/types/chat'
import { 
  getConversationMessages, 
  markMessageAsImportant,
} from '@/service/chatService'

interface UseChatMessagesProps {
  conversationId: string | null
  mounted: React.MutableRefObject<boolean>
}

export function useChatMessages({ conversationId, mounted }: UseChatMessagesProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [importantMessages, setImportantMessages] = useState<Message[]>([])
  const [showImportantOnly, setShowImportantOnly] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  // 生成本地消息ID
  const generateLocalId = useCallback(() => {
    return `local_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }, [])

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
        
        // 始终更新重点消息列表，不论当前是否显示重点消息
        const important = newMessages.filter(msg => msg.is_important)
        setImportantMessages(important)

        const newLastMessageId = newMessages.length > 0 
          ? newMessages[newMessages.length - 1].id 
          : null
        
        return lastMessageId !== newLastMessageId
      }
      return false
    } catch (error) {
      console.error('ChatWindow:静默获取消息出错:', error)
      return false
    }
  }, [conversationId, messages, mounted])

  // 获取消息
  const fetchMessages = useCallback(async () => {
    if (!conversationId || !mounted.current) return

    try {
      setIsLoading(true)
      
      const messagesData = await getConversationMessages(conversationId, true)
      if (!mounted.current) return

      setMessages(messagesData)
      const important = messagesData.filter(msg => msg.is_important)
      setImportantMessages(important)

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
      const result = await markMessageAsImportant(conversationId, messageId, !currentStatus)
      if (result) {
        // 成功时显示提示
        toast.success(!currentStatus ? '消息已标记为重点' : '已取消重点标记')
        await fetchMessages()
      } else {
        toast.error('操作失败，请重试')
      }
    } catch (error) {
      console.error('标记重点消息失败:', error)
      // 显示用户友好的错误提示
      toast.error('标记重点消息失败，请检查网络连接')
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
    // 始终更新重点消息列表
    const important = newMessages.filter(msg => msg.is_important)
    setImportantMessages(important)
  }, [])

  // 当 conversationId 变化时自动获取消息
  useEffect(() => {
    if (conversationId && mounted.current) {
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
    isLoading,
    silentlyUpdateMessages,
    fetchMessages,
    toggleMessageImportant,
    toggleShowImportantOnly,
    addMessage,
    updateMessages
  }
} 
