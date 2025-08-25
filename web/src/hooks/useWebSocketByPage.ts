'use client';

import { useEffect, useState, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { authService } from '@/service/authService';
import { getWebSocketClient, ConnectionStatus } from '@/service/websocket';
import { SenderType } from '@/service/websocket/types';
import { getDeviceInfo, getWebSocketDeviceConfig } from '@/service/utils';
import { createCustomHandler } from '@/service/websocket/handlers';

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

    const messageHandler = (data: any): boolean => {
      setLastMessage(data);
      return true; // 表示已处理
    };

    // 注册消息处理器
    const wsClient = getWebSocketClient();
    const handler = createCustomHandler('page-message-handler', [], messageHandler);
    wsClient.registerHandler(handler);

    return () => {
      wsClient.unregisterHandler('page-message-handler');
    };
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
        (!config.requireAuth || (user && token));

      if (shouldDisconnect && isConnected) {
        console.log(`断开页面WebSocket连接：${pathname}，原因：配置变更或认证失效`);
        getWebSocketClient().disconnect();
        connectionRef.current = null;
        return;
      }

      if (shouldConnect && !isConnected && !isConnectingRef.current) {
        // 检查是否已经存在连接
        const currentIsConnected = getWebSocketClient().isConnected();
        if (currentIsConnected) {
          console.log(`检测到已有WebSocket连接，更新页面状态：${pathname}`);
          setIsConnected(true);
          setConnectionStatus(getWebSocketClient().getConnectionStatus());
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
            await getWebSocketClient().connect(connectionParams);
            
            connectionRef.current = connectionId;
            setIsConnected(true);
            setConnectionStatus(getWebSocketClient().getConnectionStatus());
            
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
        getWebSocketClient().disconnect();
        connectionRef.current = null;
      }
    };
  }, [pathname, isConnected]);

  // 手动连接
  const connect = async (): Promise<boolean> => {
    if (!config?.enabled || isConnected || isConnectingRef.current) {
      return false;
    }

    try {
      isConnectingRef.current = true;
      const user = authService.getCurrentUser();
      const connectionId = `${config.connectionType}_${pathname.replace(/\//g, '_')}_${Date.now()}`;
      await getWebSocketClient().connect({
        userId: user?.id || 'anonymous',
        token: await authService.getValidToken() || undefined,
        userType: mapUserRoleToSenderType(user?.currentRole || 'user'),
        connectionId
      });
      connectionRef.current = connectionId;
      return true;
    } catch (error) {
      console.error('手动连接WebSocket失败:', error);
      return false;
    } finally {
      isConnectingRef.current = false;
    }
  };

  // 手动断开
  const disconnect = () => {
    if (connectionRef.current) {
      getWebSocketClient().disconnect();
      connectionRef.current = null;
    }
  };

  // 发送消息
  const sendMessage = (message: any): boolean => {
    if (!isConnected) {
      console.warn('WebSocket未连接，无法发送消息');
      return false;
    }

    return getWebSocketClient().sendMessage({
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
    
    // 配置信息
    config
  };
} 