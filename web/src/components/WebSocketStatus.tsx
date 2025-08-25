'use client';

import { ConnectionStatus } from '@/service/websocket/types';

/**
 * WebSocket状态组件的Props接口
 */
export interface WebSocketStatusProps {
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  isEnabled: boolean;
  connectionType: string;
  connect: () => Promise<boolean>;
  disconnect: () => void;
}

/**
 * 聊天页面WebSocket状态指示器
 */
export function WebSocketStatus({
  isConnected,
  connectionStatus,
  isEnabled,
  connectionType,
  connect,
  disconnect
}: WebSocketStatusProps) {
  // 如果当前页面不需要WebSocket，不显示状态
  if (!isEnabled) {
    return null;
  }

  const getStatusColor = () => {
    switch (connectionStatus) {
      case ConnectionStatus.CONNECTED:
        return 'bg-green-500';
      case ConnectionStatus.CONNECTING:
        return 'bg-yellow-500';
      case ConnectionStatus.ERROR:
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case ConnectionStatus.CONNECTED:
        return '已连接';
      case ConnectionStatus.CONNECTING:
        return '连接中...';
      case ConnectionStatus.ERROR:
        return '连接错误';
      default:
        return '未连接';
    }
  };

  return (
    <div className="flex items-center space-x-3">
      {/* 连接状态 */}
      <div className="flex items-center space-x-2">
        <div className={`w-3 h-3 rounded-full ${getStatusColor()}`}></div>
        <span className="text-sm font-medium">{getStatusText()}</span>
        {connectionType && (
          <span className="text-xs text-gray-500">({connectionType})</span>
        )}
      </div>

      {/* 连接控制 */}
      {!isConnected ? (
        <button
          onClick={connect}
          className="px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
        >
          连接
        </button>
      ) : (
        <button
          onClick={disconnect}
          className="px-3 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition-colors"
        >
          断开
        </button>
      )}
    </div>
  );
} 