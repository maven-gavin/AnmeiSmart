'use client';

import { useState, useEffect } from 'react';
import { getConnectionStatus, ConnectionStatus } from '@/service/chatService';

export default function ConnectionStatusBar() {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);

  useEffect(() => {
    // 定期检查连接状态
    const intervalId = setInterval(() => {
      const status = getConnectionStatus();
      setConnectionStatus(status);
    }, 1000);

    return () => clearInterval(intervalId);
  }, []);

  // 只在连接中或错误状态时显示连接状态栏
  if (connectionStatus === ConnectionStatus.CONNECTED) {
    return null;
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 border-t border-red-200 bg-red-50 p-2 text-center text-sm text-red-600">
      {connectionStatus === ConnectionStatus.DISCONNECTED && '连接已断开，正在尝试重新连接...'}
      {connectionStatus === ConnectionStatus.CONNECTING && '正在建立连接...'}
      {connectionStatus === ConnectionStatus.ERROR && '连接出错，请刷新页面重试'}
    </div>
  );
} 