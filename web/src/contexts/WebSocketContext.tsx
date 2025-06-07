'use client';

import React, { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { chatWebSocket } from '@/service/chat/websocket';
import { authService } from '@/service/authService';
import { ConnectionStatus } from '@/service/websocket/types';

interface WebSocketContextType {
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  connect: (conversationId: string) => Promise<void>;
  disconnect: () => void;
  addMessageHandler: (action: string, handler: (data: any) => void) => void;
  removeMessageHandler: (action: string) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  const currentConversationId = useRef<string | null>(null);
  const mounted = useRef(true);

  // 连接状态监听器
  useEffect(() => {
    const statusListener = (event: any) => {
      if (!mounted.current) return;
      
      const newStatus = event.newStatus || ConnectionStatus.DISCONNECTED;
      setConnectionStatus(newStatus);
      setIsConnected(newStatus === ConnectionStatus.CONNECTED);
      
      console.log('分布式WebSocket连接状态更新:', {
        oldStatus: event.oldStatus,
        newStatus: newStatus,
        conversationId: currentConversationId.current,
        architecture: 'distributed-redis-pubsub'
      });
    };

    chatWebSocket.addConnectionStatusListener(statusListener);

    return () => {
      mounted.current = false;
      chatWebSocket.removeConnectionStatusListener(statusListener);
    };
  }, []);

  // 连接到指定会话
  const connect = async (conversationId: string) => {
    try {
      const user = authService.getCurrentUser();
      if (!user) {
        console.error('用户未登录，无法建立WebSocket连接');
        return;
      }

      // 如果已连接到相同会话，无需重连
      if (currentConversationId.current === conversationId && isConnected) {
        console.log('已连接到相同会话，无需重连');
        return;
      }

      // 先断开现有连接
      if (isConnected) {
        disconnect();
      }

      currentConversationId.current = conversationId;
      
      console.log('建立分布式WebSocket连接:', {
        userId: user.id,
        conversationId,
        architecture: 'distributed-redis-pubsub'
      });

      await chatWebSocket.connect(user.id, conversationId);
      
    } catch (error) {
      console.error('WebSocket连接失败:', error);
      currentConversationId.current = null;
    }
  };

  // 断开连接
  const disconnect = () => {
    try {
      chatWebSocket.disconnect();
      currentConversationId.current = null;
      setIsConnected(false);
      setConnectionStatus(ConnectionStatus.DISCONNECTED);
    } catch (error) {
      console.error('断开WebSocket连接失败:', error);
    }
  };

  // 添加消息处理器
  const addMessageHandler = (action: string, handler: (data: any) => void) => {
    chatWebSocket.addMessageHandler(action, handler);
  };

  // 移除消息处理器
  const removeMessageHandler = (action: string) => {
    chatWebSocket.removeMessageHandler(action);
  };

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
    connect,
    disconnect,
    addMessageHandler,
    removeMessageHandler,
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