'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { authService } from '@/service/authService';
import { getWebSocketClient, ConnectionStatus, WebSocketConfig } from '@/service/websocket';
import { SenderType } from '@/service/websocket/types';
import { getDeviceInfo } from '@/service/utils';
import { WS_BASE_URL } from '@/config';

type AppWebSocketState = {
  // 连接状态
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  isEnabled: boolean;
  connectionType: string;

  // 最近一条事件消息（例如 new_message）
  lastMessage: any;

  // 操作
  connect: () => Promise<boolean>;
  disconnect: () => void;
  sendMessage: (message: any) => boolean;
};

function getDefaultWebSocketConfig(): WebSocketConfig {
  return {
    url: WS_BASE_URL,
    reconnectAttempts: 5,
    reconnectInterval: 3000,
    heartbeatInterval: 30000,
    connectionTimeout: 10000,
    debug: process.env.NODE_ENV === 'development',
  };
}

function getWebSocketClientSafely(): ReturnType<typeof getWebSocketClient> {
  try {
    return getWebSocketClient();
  } catch {
    const defaultConfig = getDefaultWebSocketConfig();
    return getWebSocketClient(defaultConfig);
  }
}

export function useAppWebSocket(): AppWebSocketState {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  const [lastMessage, setLastMessage] = useState<any>(null);

  const isConnectingRef = useRef(false);
  const hasTriedInitialConnectRef = useRef(false);

  // 统一的连接函数
  const connect = useCallback(async (): Promise<boolean> => {
    const user = authService.getCurrentUser();
    const token = await authService.getValidToken();

    if (!user || !token) {
      console.warn('WebSocket: 用户未登录或无可用 token，跳过连接');
      return false;
    }

    if (isConnectingRef.current) {
      return false;
    }

    const client = getWebSocketClientSafely();

    if (client.isConnected()) {
      setIsConnected(true);
      setConnectionStatus(client.getConnectionStatus());
      return true;
    }

    try {
      isConnectingRef.current = true;

      const deviceInfo = await getDeviceInfo();
      const connectionParams = {
        userId: user.id,
        token,
        userType: mapUserRoleToSenderType(user.currentRole || 'user'),
        connectionId: `app_${Date.now()}`,
        deviceId: deviceInfo?.deviceId,
        deviceType: deviceInfo?.type,
        deviceIP: deviceInfo?.ip,
        userAgent: deviceInfo?.userAgent,
        platform: deviceInfo?.platform,
        screenResolution: deviceInfo
          ? `${deviceInfo.screenWidth}x${deviceInfo.screenHeight}`
          : undefined,
      };

      await client.connect(connectionParams);
      setIsConnected(true);
      setConnectionStatus(client.getConnectionStatus());
      return true;
    } catch (error) {
      console.error('应用级 WebSocket 连接失败:', error);
      setIsConnected(false);
      setConnectionStatus(ConnectionStatus.ERROR);
      return false;
    } finally {
      isConnectingRef.current = false;
    }
  }, []);

  const disconnect = useCallback(() => {
    try {
      const client = getWebSocketClientSafely();
      client.disconnect();
      setIsConnected(false);
      setConnectionStatus(ConnectionStatus.DISCONNECTED);
    } catch (error) {
      console.error('应用级 WebSocket 断开失败:', error);
    }
  }, []);

  const sendMessage = useCallback(
    (message: any): boolean => {
      const client = getWebSocketClientSafely();
      if (!client.isConnected()) {
        console.warn('WebSocket 未连接，无法发送消息');
        return false;
      }

      return client.sendMessage({
        ...message,
        source: 'app',
        timestamp: new Date().toISOString(),
      });
    },
    [],
  );

  // 监听连接状态变化
  useEffect(() => {
    const client = getWebSocketClientSafely();

    const statusListener = (event: any) => {
      setConnectionStatus(event.newStatus);
      setIsConnected(event.newStatus === ConnectionStatus.CONNECTED);
    };

    client.addConnectionStatusListener(statusListener);

    // 初始化当前状态
    setConnectionStatus(client.getConnectionStatus());
    setIsConnected(client.isConnected());

    return () => {
      client.removeConnectionStatusListener(statusListener);
    };
  }, []);

  // 监听 MessageEventHandler，统一分发 new_message / 其他事件
  useEffect(() => {
    const client = getWebSocketClientSafely();

    // 聊天新消息：直接使用 new_message 事件（已由后端统一为 action: new_message）
    const offNewMessage = client.onNewMessage((eventData: any) => {
      setLastMessage({
        action: 'new_message',
        data: eventData,
      });
    });

    // 通用事件：用于 direct_message、system_notification 等
    const offEvent = client.onEvent((eventData: any) => {
      // 只处理带 type 字段的通用事件，避免与 new_message 重复
      if (!eventData || !eventData.type) {
        return;
      }

      setLastMessage({
        // 统一使用 type 作为高层事件名称，例如 friend_request_received 等
        action: eventData.type,
        // data 直接是业务有效负载，优先使用 payload 字段
        data: eventData.payload ?? eventData,
      });
    });

    return () => {
      offNewMessage && offNewMessage();
      offEvent && offEvent();
    };
  }, []);

  // 首次尝试自动连接（应用级一次）
  useEffect(() => {
    if (hasTriedInitialConnectRef.current) return;
    hasTriedInitialConnectRef.current = true;
    void connect();
  }, [connect]);

  return {
    isConnected,
    connectionStatus,
    isEnabled: true,
    connectionType: 'app',
    lastMessage,
    connect,
    disconnect,
    sendMessage,
  };
}

function mapUserRoleToSenderType(role: string): SenderType {
  switch (role) {
    case 'customer':
      return SenderType.CUSTOMER;
    case 'consultant':
      return SenderType.CONSULTANT;
    case 'doctor':
      return SenderType.DOCTOR;
    default:
      return SenderType.USER;
  }
}


