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
  
  // 使用ref来存储最新值，避免useCallback依赖循环
  const latestParamsRef = useRef({ userId, conversationId })
  const isConnectingRef = useRef(false)
  
  // 更新最新参数引用
  useEffect(() => {
    latestParamsRef.current = { userId, conversationId }
  }, [userId, conversationId])

  // 重新连接WebSocket的函数 - 移除wsStatus依赖
  const reconnectWebSocket = useCallback(() => {
    const { userId: currentUserId, conversationId: currentConversationId } = latestParamsRef.current
    
    console.log('[useWebSocketConnection] reconnectWebSocket called. User:', !!currentUserId, 'ConversationId:', currentConversationId)
    
    if (!mounted.current || !currentUserId || !currentConversationId || isConnectingRef.current) {
      console.log('[useWebSocketConnection] 跳过连接：组件未挂载、参数缺失或正在连接中')
      return
    }
    
    console.log(`[useWebSocketConnection] 尝试重新连接WebSocket for ${currentConversationId} with user ${currentUserId}`)
    
    // 设置连接状态标志
    isConnectingRef.current = true
    
    // 先关闭任何现有连接
    closeWebSocketConnection()
    
    // 立即设置状态为连接中
    setWsStatus(ConnectionStatus.CONNECTING)
    
    // 短暂延迟后初始化连接
    setTimeout(() => {
      if (mounted.current) {
        console.log(`[useWebSocketConnection] 调用 initializeWebSocket for ${currentConversationId}`)
        initializeWebSocket(currentUserId, currentConversationId)
          .finally(() => {
            isConnectingRef.current = false
          })
      } else {
        console.log('[useWebSocketConnection] 组件已卸载，取消初始化')
        isConnectingRef.current = false
      }
    }, 500) // 增加延迟确保完全清理
  }, [mounted]) // 只依赖mounted

  // 监听WebSocket状态变化
  useEffect(() => {
    const handleStatusChange = (event: any) => {
      console.log('useWebSocketConnection收到状态变化事件:', event)
      if (event?.newStatus) {
        setWsStatus(event.newStatus)
        
        // 重置连接标志
        if (event.newStatus === ConnectionStatus.CONNECTED || event.newStatus === ConnectionStatus.DISCONNECTED) {
          isConnectingRef.current = false
        }
      }
    }

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
    
    try {
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

  // 初始化和清理WebSocket连接 - 移除循环依赖
  useEffect(() => {
    if (!userId || !conversationId || !mounted.current) return

    console.log(`useWebSocketConnection: 初始化WebSocket连接 ${conversationId}`)
    
    // 防抖连接初始化
    const initTimeout = setTimeout(() => {
      if (!mounted.current || isConnectingRef.current) return
      
      isConnectingRef.current = true
      setWsStatus(ConnectionStatus.CONNECTING)
      closeWebSocketConnection()
      
      initializeWebSocket(userId, conversationId)
        .finally(() => {
          if (mounted.current) {
            isConnectingRef.current = false
          }
        })
    }, 100)

    return () => {
      console.log('useWebSocketConnection清理，关闭WebSocket连接')
      clearTimeout(initTimeout)
      closeWebSocketConnection()
      isConnectingRef.current = false
    }
  }, [conversationId, userId]) // 移除mounted和reconnectWebSocket依赖

  // 页面可见性和焦点处理 - 分离到独立的useEffect
  useEffect(() => {
    if (!userId || !conversationId) return

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && wsStatus === ConnectionStatus.DISCONNECTED) {
        console.log('页面变为可见，检查WebSocket连接')
        setTimeout(reconnectWebSocket, 1000) // 延迟重连
      }
    }

    const handleFocus = () => {
      if (wsStatus === ConnectionStatus.DISCONNECTED && document.visibilityState === 'visible') {
        console.log('窗口获得焦点，检查WebSocket连接')
        setTimeout(reconnectWebSocket, 1000) // 延迟重连
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('focus', handleFocus)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('focus', handleFocus)
    }
  }, [userId, conversationId, wsStatus, reconnectWebSocket])

  return {
    wsStatus,
    reconnectWebSocket
  }
} 