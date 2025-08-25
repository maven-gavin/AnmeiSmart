'use client';

import { useEffect, useState, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { authService } from '@/service/authService';
import { chatWebSocket } from '@/service/chat/websocket';
import { ConnectionStatus } from '@/service/websocket/types';

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

  // 连接状态监听
  useEffect(() => {
    if (!config?.enabled) return;

    const statusListener = (event: any) => {
      const newStatus = event.newStatus || ConnectionStatus.DISCONNECTED;
      setConnectionStatus(newStatus);
      setIsConnected(newStatus === ConnectionStatus.CONNECTED);
      
      if (newStatus === ConnectionStatus.CONNECTED && connectionRef.current) {
        console.log(`页面WebSocket连接成功：${pathname}，连接类型：${config.connectionType}`);
      }
    };

    // 添加状态监听器
    chatWebSocket.addConnectionStatusListener(statusListener);

    // 立即检查当前连接状态（防止错过状态变化事件）
    const currentStatus = chatWebSocket.getConnectionStatus();
    const currentIsConnected = chatWebSocket.isConnected();
    
    console.log(`页面${pathname}检查当前WebSocket状态:`, {
      currentStatus,
      currentIsConnected,
      connectionType: config.connectionType
    });

    setConnectionStatus(currentStatus);
    setIsConnected(currentIsConnected);

    return () => {
      chatWebSocket.removeConnectionStatusListener(statusListener);
    };
  }, [config, pathname]);

  // 消息监听
  useEffect(() => {
    if (!config?.enabled) return;

    const messageHandler = (data: any) => {
      // 只处理当前页面相关的消息
      if (config.features.includes(data.feature) || data.feature === '*') {
        setLastMessage(data);
        console.log(`页面收到WebSocket消息：${pathname}，类型：${data.action || data.type}`);
      }
    };

    chatWebSocket.addMessageHandler('*', messageHandler);

    return () => {
      chatWebSocket.removeMessageHandler('*');
    };
  }, [config, pathname]);

  // 智能连接管理
  useEffect(() => {
    const manageConnection = async () => {
      if (!config) return;

      const user = authService.getCurrentUser();
      const isAuthenticated = !!user;

      // 检查是否需要建立连接
      const shouldConnect = 
        config.enabled && 
        (!config.requireAuth || isAuthenticated) && 
        config.autoConnect &&
        !isConnectingRef.current;

      // 检查是否需要断开连接
      const shouldDisconnect = 
        !config.enabled || 
        (config.requireAuth && !isAuthenticated) ||
        !config.autoConnect;

      if (shouldDisconnect && isConnected) {
        console.log(`断开页面WebSocket连接：${pathname}，原因：配置变更或认证失效`);
        chatWebSocket.disconnect();
        connectionRef.current = null;
        return;
      }

      if (shouldConnect && !isConnected && !isConnectingRef.current) {
        // 检查是否已经存在连接
        const currentIsConnected = chatWebSocket.isConnected();
        if (currentIsConnected) {
          console.log(`检测到已有WebSocket连接，更新页面状态：${pathname}`);
          setIsConnected(true);
          setConnectionStatus(chatWebSocket.getConnectionStatus());
          return;
        }

        try {
          isConnectingRef.current = true;
          
          console.log(`建立页面WebSocket连接：${pathname}，类型：${config.connectionType}`);
          
          // 根据页面类型使用不同的连接策略
          const connectionId = `${config.connectionType}_${pathname.replace(/\//g, '_')}_${Date.now()}`;
          await chatWebSocket.connect(user!.id, connectionId);
          
          connectionRef.current = connectionId;
        } catch (error) {
          console.error(`页面WebSocket连接失败：${pathname}`, error);
        } finally {
          isConnectingRef.current = false;
        }
      }
    };

    manageConnection();
  }, [config, pathname, isConnected]);

  // 页面卸载时清理连接
  useEffect(() => {
    return () => {
      if (connectionRef.current && isConnected) {
        console.log(`页面卸载，断开WebSocket连接：${pathname}`);
        chatWebSocket.disconnect();
        connectionRef.current = null;
      }
    };
  }, [pathname]);

  // 手动连接方法
  const connect = async () => {
    if (!config?.enabled || isConnectingRef.current) return false;

    const user = authService.getCurrentUser();
    if (config.requireAuth && !user) {
      console.warn(`页面WebSocket连接失败：${pathname}，用户未认证`);
      return false;
    }

    try {
      isConnectingRef.current = true;
      const connectionId = `${config.connectionType}_${pathname.replace(/\//g, '_')}_${Date.now()}`;
      await chatWebSocket.connect(user?.id || 'anonymous', connectionId);
      connectionRef.current = connectionId;
      return true;
    } catch (error) {
      console.error(`手动WebSocket连接失败：${pathname}`, error);
      return false;
    } finally {
      isConnectingRef.current = false;
    }
  };

  // 断开连接方法
  const disconnect = () => {
    if (connectionRef.current) {
      chatWebSocket.disconnect();
      connectionRef.current = null;
    }
  };

  // 发送消息方法
  const sendMessage = (message: any) => {
    if (!isConnected || !config?.enabled) {
      console.warn(`无法发送消息：${pathname}，WebSocket未连接`);
      return false;
    }

    return chatWebSocket.sendMessage({
      ...message,
      source_page: pathname,
      connection_type: config.connectionType,
      features: config.features
    });
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