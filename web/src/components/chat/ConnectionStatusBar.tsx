'use client';

import { useState, useEffect } from 'react';
import { getConnectionStatus, ConnectionStatus } from '@/service/chatService';

export default function ConnectionStatusBar() {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  const [visible, setVisible] = useState(false); // 默认不显示

  useEffect(() => {
    // 定期检查连接状态
    const intervalId = setInterval(() => {
      const status = getConnectionStatus();
      setConnectionStatus(status);
      
      // 只在错误状态且持续30秒以上时显示
      if (status === ConnectionStatus.ERROR) {
        setTimeout(() => {
          // 30秒后再次检查，如果仍然是错误状态，才显示
          if (getConnectionStatus() === ConnectionStatus.ERROR) {
            setVisible(true);
          }
        }, 30000);
      } else {
        // 非错误状态时隐藏
        setVisible(false);
      }
    }, 1000);

    return () => clearInterval(intervalId);
  }, []);

  // 如果不可见，直接返回null
  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 border-t border-red-200 bg-red-50 p-2 text-center text-sm text-red-600">
      {connectionStatus === ConnectionStatus.DISCONNECTED && '连接已断开，正在尝试重新连接...'}
      {connectionStatus === ConnectionStatus.CONNECTING && '正在建立连接...'}
      {connectionStatus === ConnectionStatus.ERROR && '连接出错，请刷新页面重试'}
      {connectionStatus === ConnectionStatus.CONNECTED && '连接已建立'}
    </div>
  );
} 