'use client';

import React, { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { chatWebSocket } from '@/service/chat/websocket';
import { authService } from '@/service/authService';
import { ConnectionStatus } from '@/service/websocket/types';

interface WebSocketContextType {
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  lastJsonMessage: any | null;
  connect: () => Promise<void>;
  disconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  const [lastJsonMessage, setLastJsonMessage] = useState<any | null>(null);
  const mounted = useRef(true);
  const isConnecting = useRef(false);

  // 连接状态监听器
  useEffect(() => {
    const statusListener = (event: any) => {
      if (!mounted.current) return;
      
      const newStatus = event.newStatus || ConnectionStatus.DISCONNECTED;
      setConnectionStatus(newStatus);
      setIsConnected(newStatus === ConnectionStatus.CONNECTED);
      
      console.log('全局WebSocket连接状态更新:', {
        oldStatus: event.oldStatus,
        newStatus: newStatus,
        architecture: 'distributed-global-connection'
      });
    };

    chatWebSocket.addConnectionStatusListener(statusListener);

    return () => {
      chatWebSocket.removeConnectionStatusListener(statusListener);
    };
  }, []);

  // 消息监听器 - 全局消息处理
  useEffect(() => {
    const messageHandler = (data: any) => {
      if (!mounted.current) return;
      
      console.log('收到全局WebSocket消息:', data);
      setLastJsonMessage(data);
    };

    // 注册全局消息处理器
    chatWebSocket.addMessageHandler('*', messageHandler);
    chatWebSocket.addMessageHandler('new_message', messageHandler);
    chatWebSocket.addMessageHandler('presence_update', messageHandler);
    chatWebSocket.addMessageHandler('typing_update', messageHandler);

    return () => {
      chatWebSocket.removeMessageHandler('*');
      chatWebSocket.removeMessageHandler('new_message');
      chatWebSocket.removeMessageHandler('presence_update');
      chatWebSocket.removeMessageHandler('typing_update');
    };
  }, []);

  // 自动连接 - 用户登录后建立全局连接
  useEffect(() => {
    const initializeConnection = async () => {
      const user = authService.getCurrentUser();
      if (user && !isConnected && !isConnecting.current && mounted.current) {
        console.log('用户已登录，建立全局WebSocket连接');
        await connect();
      }
    };

    // 监听认证状态变化
    const checkAuthInterval = setInterval(initializeConnection, 2000);
    
    // 立即检查一次
    initializeConnection();

    return () => {
      clearInterval(checkAuthInterval);
    };
  }, [isConnected]);

  // 全局连接方法 - 不需要conversationId
  const connect = async () => {
    if (isConnecting.current || isConnected) return;
    
    try {
      const user = authService.getCurrentUser();
      if (!user) {
        console.log('用户未登录，无法建立WebSocket连接');
        return;
      }

      isConnecting.current = true;
      
      console.log('建立全局分布式WebSocket连接:', {
        userId: user.id,
        userRoles: user.roles,
        architecture: 'distributed-global-connection'
      });

      // 连接到全局端点，不指定具体会话
      await chatWebSocket.connect(user.id, 'global');
      
    } catch (error) {
      console.error('全局WebSocket连接失败:', error);
    } finally {
      isConnecting.current = false;
    }
  };

  // 断开连接
  const disconnect = () => {
    try {
      chatWebSocket.disconnect();
      setIsConnected(false);
      setConnectionStatus(ConnectionStatus.DISCONNECTED);
      setLastJsonMessage(null);
      console.log('全局WebSocket连接已断开');
    } catch (error) {
      console.error('断开WebSocket连接失败:', error);
    }
  };

  // 页面可见性处理
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && !isConnected) {
        console.log('页面变为可见，检查全局WebSocket连接');
        connect();
      }
    };

    const handleFocus = () => {
      if (!isConnected) {
        console.log('窗口获得焦点，检查全局WebSocket连接');
        connect();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, [isConnected]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      mounted.current = false;
      disconnect();
    };
  }, []);

  const contextValue: WebSocketContextType = {
    isConnected,
    connectionStatus,
    lastJsonMessage,
    connect,
    disconnect,
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket必须在WebSocketProvider内使用');
  }
  return context;
}

export default WebSocketContext; 