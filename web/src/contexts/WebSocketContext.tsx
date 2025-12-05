'use client';

import React, { createContext, useContext } from 'react';
import { useAppWebSocket } from '@/hooks/useAppWebSocket';

type WebSocketContextValue = ReturnType<typeof useAppWebSocket>;

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const websocketState = useAppWebSocket();

  return (
    <WebSocketContext.Provider value={websocketState}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket(): WebSocketContextValue {
  const ctx = useContext(WebSocketContext);
  if (!ctx) {
    throw new Error('useWebSocket 必须在 WebSocketProvider 内部使用');
  }
  return ctx;
}



