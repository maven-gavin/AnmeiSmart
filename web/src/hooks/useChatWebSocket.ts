'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  initializeWebSocket, 
  closeWebSocketConnection, 
  getConnectionStatus,
  addMessageCallback, 
  removeMessageCallback 
} from '@/service/chatService';
import { ConnectionStatus } from '@/service/websocket';

/**
 * 管理WebSocket连接的自定义Hook
 */
export function useChatWebSocket(userId: string | undefined, conversationId: string | null) {
  // WebSocket连接状态
  const [wsStatus, setWsStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  
  // 使用ref追踪组件是否已挂载
  const mounted = useRef(true);
  
  // 初始化WebSocket连接
  const connectWebSocket = useCallback(() => {
    if (!userId || !conversationId) {
      return;
    }
    
    console.log(`初始化WebSocket连接: 用户ID=${userId}, 会话ID=${conversationId}`);
    initializeWebSocket(userId, conversationId);
  }, [userId, conversationId]);
  
  // 重新连接WebSocket
  const reconnectWebSocket = useCallback(() => {
    if (!userId || !conversationId) {
      return;
    }
    
    console.log(`手动重新连接WebSocket: 用户ID=${userId}, 会话ID=${conversationId}`);
    
    // 先清除之前的连接
    closeWebSocketConnection();
    
    // 延迟一点时间再连接，确保之前的连接已完全关闭
    setTimeout(() => {
      // 再次检查组件是否仍然挂载
      if (mounted.current) {
        initializeWebSocket(userId, conversationId);
      }
    }, 300);
  }, [userId, conversationId]);
  
  // 监听WebSocket状态
  useEffect(() => {
    // 检查连接状态
    const checkConnectionStatus = () => {
      const status = getConnectionStatus();
      setWsStatus(status);
      
      // 如果WebSocket连接断开且页面可见，尝试重新连接
      if (status === ConnectionStatus.DISCONNECTED && 
          document.visibilityState === 'visible' && 
          userId && 
          conversationId) {
        console.log(`WebSocket连接断开，将尝试重新连接`);
        setTimeout(() => {
          if (mounted.current && 
              getConnectionStatus() === ConnectionStatus.DISCONNECTED && 
              document.visibilityState === 'visible') {
            console.log(`尝试重新连接WebSocket: ${conversationId}`);
            initializeWebSocket(userId, conversationId);
          }
        }, 3000);
      }
    };
    
    // 定时检查连接状态
    const statusInterval = setInterval(checkConnectionStatus, 5000);
    checkConnectionStatus(); // 立即检查一次
    
    // 添加页面可见性变化监听器
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        console.log('页面变为可见，检查WebSocket连接');
        if (userId && conversationId && wsStatus !== ConnectionStatus.CONNECTED) {
          console.log('页面可见且WebSocket未连接，尝试重新连接');
          reconnectWebSocket();
        }
      } else if (document.visibilityState === 'hidden') {
        console.log('页面变为隐藏，关闭WebSocket连接');
        closeWebSocketConnection();
      }
    };
    
    // 添加窗口焦点变化监听器
    const handleFocus = () => {
      console.log('窗口获得焦点，检查WebSocket连接');
      if (userId && conversationId && wsStatus !== ConnectionStatus.CONNECTED && 
          document.visibilityState === 'visible') {
        console.log('窗口获得焦点且WebSocket未连接，尝试重新连接');
        reconnectWebSocket();
      }
    };
    
    // 添加事件监听
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);
    
    // 组件卸载时清理
    return () => {
      mounted.current = false;
      clearInterval(statusInterval);
      closeWebSocketConnection();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, [userId, conversationId, wsStatus, reconnectWebSocket]);
  
  // 设置消息监听器
  const setupMessageListener = useCallback((callback: (data: any) => void) => {
    // 添加消息回调
    addMessageCallback('message', callback);
    addMessageCallback('system', callback);
    addMessageCallback('connect', callback);
    
    // 返回清理函数
    return () => {
      removeMessageCallback('message', callback);
      removeMessageCallback('system', callback);
      removeMessageCallback('connect', callback);
    };
  }, []);
  
  return {
    wsStatus,
    connectWebSocket,
    reconnectWebSocket,
    setupMessageListener
  };
} 