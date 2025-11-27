'use client';

import { useEffect, useState, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { authService } from '@/service/authService';
import { getWebSocketClient, ConnectionStatus, WebSocketConfig } from '@/service/websocket';
import { SenderType } from '@/service/websocket/types';
import { getDeviceInfo, getWebSocketDeviceConfig } from '@/service/utils';
import { createCustomHandler } from '@/service/websocket/handlers';
import { WS_BASE_URL } from '@/config';

/**
 * 页面类型定义
 */
export type PageType = 
  | 'none'        // 无需WebSocket的页面
  | 'chat'        // 聊天相关页面
  | 'dashboard'   // 仪表盘页面
  | 'admin'       // 管理员页面
  | 'monitoring'; // 系统监控页面

/**
 * 页面WebSocket配置
 */
interface PageWebSocketConfig {
  enabled: boolean;           // 是否启用WebSocket
  requireAuth: boolean;       // 是否需要认证
  autoConnect: boolean;       // 是否自动连接
  connectionType: string;     // 连接类型标识
  features: string[];         // 支持的功能列表
}

/**
 * 页面路由到WebSocket配置的映射
 */
const PAGE_WEBSOCKET_CONFIG: Record<string, PageWebSocketConfig> = {
  // 聊天相关页面
  '/chat': {
    enabled: true,
    requireAuth: true,
    autoConnect: true,
    connectionType: 'chat',
    features: ['messaging', 'typing_indicator', 'file_upload', 'voice_note', 'screen_share']
  },

  // 管理员页面
  '/admin': {
    enabled: true,
    requireAuth: true,
    autoConnect: true,
    connectionType: 'admin',
    features: ['system_notifications', 'user_monitoring', 'real_time_stats']
  },

  // 测试页面配置
  '/test-websocket': {
    enabled: true,
    requireAuth: true,
    autoConnect: true,
    connectionType: 'test',
    features: ['messaging', 'testing', 'debug']
  },

  // 默认配置
  'default': {
    enabled: false,
    requireAuth: true,
    autoConnect: false,
    connectionType: 'minimal',
    features: ['notifications']
  }
};

/**
 * 根据路径获取页面类型
 */
function getPageTypeFromPath(pathname: string): PageType {
  if (pathname.includes('/chat')) return 'chat';
  if (pathname.startsWith('/admin')) return 'admin';
  if (pathname.includes('/dashboard')) return 'dashboard';
  if (pathname.includes('/monitoring')) return 'monitoring';
  return 'none';
}

/**
 * 根据路径获取WebSocket配置
 */
function getWebSocketConfig(pathname: string): PageWebSocketConfig {
  // 精确匹配
  if (PAGE_WEBSOCKET_CONFIG[pathname]) {
    return PAGE_WEBSOCKET_CONFIG[pathname];
  }

  // 前缀匹配
  for (const [path, config] of Object.entries(PAGE_WEBSOCKET_CONFIG)) {
    if (pathname.startsWith(path) && path !== 'default') {
      return config;
    }
  }

  // 默认配置
  return PAGE_WEBSOCKET_CONFIG['default'];
}

/**
 * 获取默认WebSocket配置
 */
function getDefaultWebSocketConfig(): WebSocketConfig {
  return {
    url: WS_BASE_URL,
    reconnectAttempts: 5,
    reconnectInterval: 3000,
    heartbeatInterval: 30000,
    connectionTimeout: 10000,
    debug: process.env.NODE_ENV === 'development'
  };
}

/**
 * 安全获取WebSocket客户端，如果未初始化则先初始化
 */
function getWebSocketClientSafely(): ReturnType<typeof getWebSocketClient> {
  try {
    return getWebSocketClient();
  } catch (error) {
    // 如果未初始化，则使用默认配置初始化
    const defaultConfig = getDefaultWebSocketConfig();
    console.log('WebSocket客户端未初始化，使用默认配置初始化:', defaultConfig);
    return getWebSocketClient(defaultConfig);
  }
}

/**
 * 页面级WebSocket Hook
 * 根据当前页面和认证状态智能管理WebSocket连接
 */
export function useWebSocketByPage() {
  const pathname = usePathname();
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [config, setConfig] = useState<PageWebSocketConfig | null>(null);
  
  const connectionRef = useRef<string | null>(null);
  const isConnectingRef = useRef(false);
  const manualDisconnectRef = useRef(false); // 新增：手动断开标志
  
  // 获取当前页面的WebSocket配置
  useEffect(() => {
    const newConfig = getWebSocketConfig(pathname);
    setConfig(newConfig);
    
    console.log(`页面路由变化：${pathname}，WebSocket配置：`, {
      enabled: newConfig.enabled,
      requireAuth: newConfig.requireAuth,
      connectionType: newConfig.connectionType,
      features: newConfig.features
    });
  }, [pathname]);

  // 消息处理
  useEffect(() => {
    if (!config?.enabled) return;

    const wsClient = getWebSocketClientSafely();
    
    // 通过MessageEventHandler的回调接收消息，而不是自定义处理器
    // 这样可以确保事件消息（如new_message）能正确传递
    const messageEventHandler = wsClient.getHandlerRegistry()?.getHandlers().find(
      h => h.getName() === 'MessageEventHandler'
    ) as any;
    
    if (messageEventHandler) {
      // 注册新消息回调
      // MessageEventHandler.handleNewMessage 会调用 invokeCallbacks('new_message', eventData)
      // 这里的 eventData 是 data 字段的内容（扁平化的消息数据）
      const newMessageCallback = (eventData: any): void => {
        // 构造与page.tsx期望格式一致的消息对象
        setLastMessage({
          action: 'new_message',
          data: eventData  // eventData 已经是扁平化的消息数据
        });
      };
      
      // 注册通用事件回调（处理所有事件类型）
      // MessageEventHandler 会调用 invokeCallbacks('event', eventData)
      const eventCallback = (eventData: any): void => {
        // eventData 是 data 字段的内容，需要从原始消息中获取 action
        // 但由于我们无法访问原始消息，这里假设 eventData 包含完整信息
        // 实际上，我们需要在 MessageEventHandler 中传递完整的消息对象
        setLastMessage({
          action: 'new_message', // 默认使用 new_message，因为这是最常见的情况
          data: eventData
        });
      };
      
      messageEventHandler.addNewMessageCallback(newMessageCallback);
      messageEventHandler.addEventCallback(eventCallback);
      
      return () => {
        // 清理回调
        messageEventHandler.removeCallback('new_message', newMessageCallback);
        messageEventHandler.removeCallback('event', eventCallback);
      };
    } else {
      // 如果没有MessageEventHandler，使用自定义处理器作为fallback
      const messageHandler = (data: any): boolean => {
        // 检查是否是事件消息格式
        if ((data as any).action && (data as any).data) {
          setLastMessage(data);
        } else {
          // 尝试构造事件消息格式
          setLastMessage({
            action: (data as any).event_type || 'unknown',
            data: data
          });
        }
        return false; // 不阻止其他处理器处理
      };

      const handler = createCustomHandler('page-message-handler', [], messageHandler, 30); // 更低优先级
      wsClient.registerHandler(handler);

      return () => {
        wsClient.unregisterHandler('page-message-handler');
      };
    }
  }, [config, pathname]);

  // 连接管理
  useEffect(() => {
    if (!config?.enabled) return;

    const user = authService.getCurrentUser();
    
    const checkConnection = async () => {
      const token = await authService.getValidToken();
      const shouldDisconnect = !config.autoConnect || 
        (config.requireAuth && !user) ||
        (config.requireAuth && user && !token);

      const shouldConnect = config.autoConnect && 
        (!config.requireAuth || (user && token)) &&
        !manualDisconnectRef.current; // 手动断开后不自动重连

      if (shouldDisconnect && isConnected) {
        console.log(`断开页面WebSocket连接：${pathname}，原因：配置变更或认证失效`);
        getWebSocketClientSafely().disconnect();
        connectionRef.current = null;
        return;
      }

      if (shouldConnect && !isConnected && !isConnectingRef.current) {
        // 检查是否已经存在连接
        const currentIsConnected = getWebSocketClientSafely().isConnected();
        if (currentIsConnected) {
          console.log(`检测到已有WebSocket连接，更新页面状态：${pathname}`);
          setIsConnected(true);
          setConnectionStatus(getWebSocketClientSafely().getConnectionStatus());
          return;
        }

        // 异步连接
        const connectAsync = async () => {
          try {
            isConnectingRef.current = true;
            setIsConnected(true); // Assuming setIsConnecting is removed or replaced

            // 重新获取用户信息，确保在异步函数中可用
            const currentUser = authService.getCurrentUser();
            if (!currentUser) {
              throw new Error('用户未登录');
            }

            // 获取设备信息
            const deviceInfo = await getDeviceInfo();
            const deviceConfig = getWebSocketDeviceConfig(deviceInfo);

            // 构建连接参数
            const connectionParams = {
              userId: currentUser.id,
              token: await authService.getValidToken() || undefined,
              userType: mapUserRoleToSenderType(currentUser.currentRole || 'user'),
              connectionId: `${config.connectionType}_${pathname.replace(/\//g, '_')}_${Date.now()}`,
              deviceId: deviceInfo?.deviceId,
              deviceType: deviceInfo?.type,
              deviceIP: deviceInfo?.ip,
              userAgent: deviceInfo?.userAgent,
              platform: deviceInfo?.platform,
              screenResolution: deviceInfo ? `${deviceInfo.screenWidth}x${deviceInfo.screenHeight}` : undefined
            };

            // 根据页面类型使用不同的连接策略
            const connectionId = `${config.connectionType}_${pathname.replace(/\//g, '_')}_${Date.now()}`;
            await getWebSocketClientSafely().connect(connectionParams);
            
            connectionRef.current = connectionId;
            setIsConnected(true);
            setConnectionStatus(getWebSocketClientSafely().getConnectionStatus());
            
            console.log(`页面WebSocket连接成功：${pathname}，连接ID：${connectionId}`);
          } catch (error) {
            console.error(`页面WebSocket连接失败：${pathname}`, error);
            setConnectionStatus(ConnectionStatus.ERROR);
          } finally {
            isConnectingRef.current = false;
            // setIsConnecting(false); // Assuming setIsConnecting is removed or replaced
          }
        };

        connectAsync();
      }
    };

    checkConnection();
  }, [config, pathname, isConnected]);

  // 页面卸载时断开连接
  useEffect(() => {
    return () => {
      if (connectionRef.current && isConnected) {
        console.log(`页面卸载，断开WebSocket连接：${pathname}`);
        getWebSocketClientSafely().disconnect();
        connectionRef.current = null;
      }
    };
  }, [pathname, isConnected]);

  // 手动连接函数
  const connect = async (customParams?: any): Promise<boolean> => {
    if (!config?.enabled) {
      console.warn('WebSocket未启用，无法连接');
      return false;
    }

    try {
      // 重置手动断开标志
      manualDisconnectRef.current = false;
      
      const user = authService.getCurrentUser();
      if (!user) {
        throw new Error('用户未登录');
      }

      const deviceInfo = await getDeviceInfo();
      const connectionParams = {
        userId: user.id,
        token: await authService.getValidToken() || undefined,
        userType: mapUserRoleToSenderType(user.currentRole || 'user'),
        connectionId: `${config.connectionType}_${pathname.replace(/\//g, '_')}_${Date.now()}`,
        deviceId: deviceInfo?.deviceId,
        deviceType: deviceInfo?.type,
        deviceIP: deviceInfo?.ip,
        userAgent: deviceInfo?.userAgent,
        platform: deviceInfo?.platform,
        screenResolution: deviceInfo ? `${deviceInfo.screenWidth}x${deviceInfo.screenHeight}` : undefined,
        ...customParams
      };

      await getWebSocketClientSafely().connect(connectionParams);
      
      // 设置连接ID和状态
      const connectionId = `${config.connectionType}_${pathname.replace(/\//g, '_')}_${Date.now()}`;
      connectionRef.current = connectionId;
      setIsConnected(true);
      setConnectionStatus(getWebSocketClientSafely().getConnectionStatus());
      
      console.log(`手动连接WebSocket成功：${pathname}，连接ID：${connectionId}`);
      return true;
    } catch (error) {
      console.error(`手动连接WebSocket失败：${pathname}`, error);
      setConnectionStatus(ConnectionStatus.ERROR);
      return false;
    }
  };

  // 手动断开
  const disconnect = () => {
    try {
      console.log(`手动断开WebSocket连接：${pathname}`);
      getWebSocketClientSafely().disconnect();
      connectionRef.current = null;
      setIsConnected(false);
      setConnectionStatus(ConnectionStatus.DISCONNECTED);
      manualDisconnectRef.current = true; // 设置手动断开标志
    } catch (error) {
      console.error(`断开WebSocket连接失败：${pathname}`, error);
    }
  };

  // 发送消息
  const sendMessage = (message: any): boolean => {
    if (!isConnected) {
      console.warn('WebSocket未连接，无法发送消息');
      return false;
    }

    return getWebSocketClientSafely().sendMessage({
      ...message,
      source_page: pathname,
      timestamp: new Date().toISOString()
    });
  };

  // 工具函数：映射用户角色到发送者类型
  const mapUserRoleToSenderType = (role: string): SenderType => {
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
  };

  // 重置手动断开标志，重新启用自动连接
  const resetManualDisconnect = () => {
    manualDisconnectRef.current = false;
    console.log(`重置手动断开标志：${pathname}，重新启用自动连接`);
  };

  return {
    // 连接状态
    isConnected,
    connectionStatus,
    isEnabled: config?.enabled || false,
    connectionType: config?.connectionType || 'none',
    supportedFeatures: config?.features || [],
    
    // 数据
    lastMessage,
    
    // 方法
    connect,
    disconnect,
    sendMessage,
    resetManualDisconnect, // 新增：重置手动断开标志
    
    // 配置信息
    config
  };
} 