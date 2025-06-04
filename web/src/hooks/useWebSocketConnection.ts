import { useState, useEffect, useCallback, useRef } from 'react'
import { ConnectionStatus } from '@/service/websocket'
import { 
  initializeWebSocket,
  closeWebSocketConnection,
  addMessageCallback,
  removeMessageCallback,
  getConnectionStatus,
  addWsConnectionStatusListener,
  removeWsConnectionStatusListener
} from '@/service/chatService'

interface UseWebSocketConnectionProps {
  userId?: string
  conversationId: string | null
  mounted: React.MutableRefObject<boolean>
  onMessageReceived?: (data: any) => void
}

export function useWebSocketConnection({ 
  userId, 
  conversationId, 
  mounted, 
  onMessageReceived 
}: UseWebSocketConnectionProps) {
  const [wsStatus, setWsStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED)

  // 重新连接WebSocket的函数
  const reconnectWebSocket = useCallback(() => {
    console.log('[useWebSocketConnection] reconnectWebSocket called. User:', !!userId, 'ConversationId:', conversationId, 'Status:', wsStatus)
    
    if (!mounted.current || !userId || !conversationId) {
      console.log('[useWebSocketConnection] 跳过连接：组件未挂载或参数缺失')
      return
    }
    
    console.log(`[useWebSocketConnection] 尝试重新连接WebSocket for ${conversationId} with user ${userId}`)
    
    // 先关闭任何现有连接
    closeWebSocketConnection()
    
    // 立即设置状态为连接中
    setWsStatus(ConnectionStatus.CONNECTING)
    
    // 短暂延迟后初始化连接
    setTimeout(() => {
      if (mounted.current) {
        console.log(`[useWebSocketConnection] 调用 initializeWebSocket for ${conversationId}`)
        initializeWebSocket(userId, conversationId)
      } else {
        console.log('[useWebSocketConnection] 组件已卸载，取消初始化')
      }
    }, 100)
  }, [userId, conversationId, mounted, wsStatus])

  // 监听WebSocket状态变化
  useEffect(() => {
    const handleStatusChange = (event: any) => {
      console.log('useWebSocketConnection收到状态变化事件:', event)
      if (event?.newStatus) {
        setWsStatus(event.newStatus)
      }
    }

    // 添加错误处理，确保WebSocket已初始化
    try {
      addWsConnectionStatusListener(handleStatusChange)
    } catch (error) {
      console.warn('添加WebSocket状态监听器失败，可能WebSocket未初始化:', error)
    }

    return () => {
      try {
        removeWsConnectionStatusListener(handleStatusChange)
      } catch (error) {
        console.warn('移除WebSocket状态监听器失败:', error)
      }
    }
  }, [])

  // 监听WebSocket消息
  useEffect(() => {
    if (!userId || !conversationId || !onMessageReceived) return

    console.log(`设置WebSocket消息监听: 用户ID=${userId}, 会话ID=${conversationId}`)
    
    const abortController = new AbortController()
    
    const handleMessage = async (data: any) => {
      if (abortController.signal.aborted) return
      
      // 确保只处理当前会话的消息
      if (!data.conversation_id || data.conversation_id !== conversationId) {
        console.log(`忽略非当前会话的消息: ${data.conversation_id} vs ${conversationId}`)
        return
      }
      
      console.log(`useWebSocketConnection收到当前会话的WebSocket消息:`, data)
      
      if (!abortController.signal.aborted) {
        onMessageReceived(data)
      }
    }
    
    // 添加错误处理
    try {
      // 添加消息回调
      addMessageCallback('message', handleMessage)
      addMessageCallback('system', handleMessage)
      addMessageCallback('connect', handleMessage)
    } catch (error) {
      console.warn('添加WebSocket消息回调失败，可能WebSocket未初始化:', error)
    }
    
    return () => {
      console.log(`移除WebSocket消息回调, 会话ID: ${conversationId}`)
      abortController.abort()
      try {
        removeMessageCallback('message', handleMessage)
        removeMessageCallback('system', handleMessage)
        removeMessageCallback('connect', handleMessage)
      } catch (error) {
        console.warn('移除WebSocket消息回调失败:', error)
      }
    }
  }, [conversationId, userId, onMessageReceived])

  // 初始化和清理WebSocket连接
  useEffect(() => {
    if (!userId || !conversationId || !mounted.current) return

    console.log(`useWebSocketConnection: 初始化WebSocket连接 ${conversationId}`)
    
    // 监听页面可见性变化
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && wsStatus !== ConnectionStatus.CONNECTED) {
        console.log('页面变为可见，检查WebSocket连接')
        reconnectWebSocket()
      }
    }

    // 监听窗口焦点变化
    const handleFocus = () => {
      if (wsStatus !== ConnectionStatus.CONNECTED && document.visibilityState === 'visible') {
        console.log('窗口获得焦点，检查WebSocket连接')
        reconnectWebSocket()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('focus', handleFocus)

    // 初始化连接
    setWsStatus(ConnectionStatus.CONNECTING)
    closeWebSocketConnection()
    try {
      initializeWebSocket(userId, conversationId)
    } catch (error) {
      console.error('初始化WebSocket失败:', error)
      setWsStatus(ConnectionStatus.ERROR)
    }

    return () => {
      console.log('useWebSocketConnection清理，关闭WebSocket连接')
      closeWebSocketConnection()
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('focus', handleFocus)
    }
  }, [conversationId, userId, mounted, reconnectWebSocket, wsStatus])

  // 初始化状态
  useEffect(() => {
    if (mounted.current && wsStatus == null) {
      try {
        const status = getConnectionStatus()
        setWsStatus(status)
      } catch (e) {
        console.warn('获取WebSocket状态失败:', e)
        setWsStatus(ConnectionStatus.DISCONNECTED)
      }
    }
  }, [mounted, wsStatus])

  return {
    wsStatus,
    reconnectWebSocket
  }
} 