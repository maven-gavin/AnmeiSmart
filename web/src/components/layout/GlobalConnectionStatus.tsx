'use client';

import { useState, useEffect } from 'react';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { ConnectionStatus } from '@/service/websocket/types';

/**
 * 全局WebSocket连接状态指示器
 * 新架构下用于显示全局连接状态，只在连接异常时显示
 */
export function GlobalConnectionStatus() {
  const { connectionStatus } = useWebSocket();
  const [showStatus, setShowStatus] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  // 延迟显示状态，避免频繁闪烁
  useEffect(() => {
    if (connectionStatus === ConnectionStatus.CONNECTED) {
      setShowStatus(false);
      setRetryCount(0);
      return;
    }

    // 如果是断开连接状态，延迟3秒后显示
    const timer = setTimeout(() => {
      setShowStatus(true);
             if (connectionStatus === ConnectionStatus.DISCONNECTED) {
         setRetryCount((prev: number) => prev + 1);
       }
    }, 3000);

    return () => clearTimeout(timer);
  }, [connectionStatus]);

  // 如果连接正常或不需要显示状态，则不渲染
  if (connectionStatus === ConnectionStatus.CONNECTED || !showStatus) {
    return null;
  }

  const getStatusConfig = () => {
    const baseConfig = {
      [ConnectionStatus.CONNECTING]: {
        bgColor: 'bg-blue-50 border-blue-200',
        textColor: 'text-blue-700',
        iconColor: 'text-blue-500',
        message: '正在连接服务器...',
        showSpinner: true
      },
      [ConnectionStatus.ERROR]: {
        bgColor: 'bg-red-50 border-red-200',
        textColor: 'text-red-700',
        iconColor: 'text-red-500',
        message: retryCount > 3 ? '服务器连接异常，请检查网络或稍后重试' : '连接服务器失败，正在自动重试...',
        showSpinner: retryCount <= 3
      },
      [ConnectionStatus.DISCONNECTED]: {
        bgColor: 'bg-yellow-50 border-yellow-200',
        textColor: 'text-yellow-700',
        iconColor: 'text-yellow-500',
        message: retryCount > 5 ? '连接服务器超时，请检查后端服务是否启动' : `与服务器断开连接，正在重新连接...${retryCount > 1 ? ` (${retryCount}/10)` : ''}`,
        showSpinner: retryCount <= 5
      }
    };
    
    return baseConfig;
  };

  const statusConfig = getStatusConfig();

  const config = statusConfig[connectionStatus] || statusConfig[ConnectionStatus.DISCONNECTED];

  return (
    <div className={`fixed top-0 left-0 right-0 z-50 border-b ${config.bgColor}`}>
      <div className="container mx-auto px-4 py-2">
        <div className={`flex items-center justify-center text-sm ${config.textColor}`}>
          {config.showSpinner ? (
            <svg 
              className={`animate-spin -ml-1 mr-2 h-4 w-4 ${config.iconColor}`}
              xmlns="http://www.w3.org/2000/svg" 
              fill="none" 
              viewBox="0 0 24 24"
            >
              <circle 
                className="opacity-25" 
                cx="12" 
                cy="12" 
                r="10" 
                stroke="currentColor" 
                strokeWidth="4"
              />
              <path 
                className="opacity-75" 
                fill="currentColor" 
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : (
            <svg 
              className={`mr-2 h-4 w-4 ${config.iconColor}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" 
              />
            </svg>
          )}
          <span>{config.message}</span>
          
          {/* 连接状态详情（开发模式） */}
          {process.env.NODE_ENV === 'development' && (
            <span className="ml-2 text-xs opacity-60">
              [{connectionStatus}]
            </span>
          )}
        </div>
      </div>
    </div>
  );
} 