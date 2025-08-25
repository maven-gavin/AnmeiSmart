# 🚀 前端WebSocket实战练习

## 📚 练习概述

本练习文件配合《前端WebSocket、广播、事件系统实战教案》使用，通过实际编程练习帮助您掌握前端WebSocket开发技能。

### 🎯 练习目标

- 巩固WebSocket基础概念
- 掌握页面级连接管理
- 学会消息处理和事件驱动
- 理解状态管理和用户反馈
- 能够独立实现实时通信功能

---

## 🎓 基础练习（1-4）

### 练习1：WebSocket基础连接

**目标**：理解WebSocket连接的生命周期

**任务**：
1. 创建一个简单的WebSocket连接
2. 实现连接状态监听
3. 处理连接建立、消息接收、连接关闭事件

**代码位置**：`web/src/components/WebSocketDemo.tsx`

**参考实现**：
```typescript
import React, { useState, useEffect } from 'react';

export function WebSocketDemo() {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  const [messages, setMessages] = useState<string[]>([]);

  const connect = () => {
    const websocket = new WebSocket('ws://localhost:8000/ws');
    
    websocket.onopen = () => {
      setStatus('connected');
      setMessages(prev => [...prev, '连接已建立']);
    };
    
    websocket.onmessage = (event) => {
      setMessages(prev => [...prev, `收到消息: ${event.data}`]);
    };
    
    websocket.onclose = () => {
      setStatus('disconnected');
      setMessages(prev => [...prev, '连接已关闭']);
    };
    
    websocket.onerror = (error) => {
      setMessages(prev => [...prev, `连接错误: ${error}`]);
    };
    
    setWs(websocket);
    setStatus('connecting');
  };

  const disconnect = () => {
    if (ws) {
      ws.close();
      setWs(null);
    }
  };

  const sendMessage = (message: string) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(message);
      setMessages(prev => [...prev, `发送消息: ${message}`]);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">WebSocket基础连接</h2>
      
      <div className="space-y-4">
        <div className="flex space-x-2">
          <button
            onClick={connect}
            disabled={status === 'connected'}
            className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300"
          >
            连接
          </button>
          <button
            onClick={disconnect}
            disabled={status !== 'connected'}
            className="px-4 py-2 bg-red-500 text-white rounded disabled:bg-gray-300"
          >
            断开
          </button>
        </div>
        
        <div className="p-2 bg-gray-100 rounded">
          状态: {status}
        </div>
        
        <div className="space-y-2">
          <input
            type="text"
            placeholder="输入消息"
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                sendMessage(e.currentTarget.value);
                e.currentTarget.value = '';
              }
            }}
            className="w-full p-2 border rounded"
          />
        </div>
        
        <div className="h-64 overflow-y-auto border rounded p-2">
          {messages.map((msg, index) => (
            <div key={index} className="text-sm mb-1">{msg}</div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

**练习要求**：
- 实现连接状态显示
- 添加消息发送功能
- 处理连接错误情况
- 实现优雅的连接关闭

---

### 练习2：页面级连接管理

**目标**：实现智能的页面级WebSocket连接管理

**任务**：
1. 创建页面配置系统
2. 实现条件连接逻辑
3. 处理页面切换时的连接管理

**代码位置**：`web/src/hooks/useWebSocketByPage.ts`

**参考实现**：
```typescript
import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/router';

interface PageWebSocketConfig {
  enabled: boolean;
  requireAuth: boolean;
  autoConnect: boolean;
  connectionType: string;
  features: string[];
}

const PAGE_WEBSOCKET_CONFIG: Record<string, PageWebSocketConfig> = {
  '/chat': {
    enabled: true,
    requireAuth: true,
    autoConnect: true,
    connectionType: 'chat',
    features: ['messaging', 'typing_indicator']
  },
  '/admin': {
    enabled: true,
    requireAuth: true,
    autoConnect: true,
    connectionType: 'admin',
    features: ['system_notifications']
  },
  '/login': {
    enabled: false,
    requireAuth: false,
    autoConnect: false,
    connectionType: 'none',
    features: []
  }
};

export function useWebSocketByPage() {
  const router = useRouter();
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  
  // 获取当前页面配置
  const config = useMemo(() => {
    const path = router.pathname;
    return PAGE_WEBSOCKET_CONFIG[path] || {
      enabled: false,
      requireAuth: false,
      autoConnect: false,
      connectionType: 'none',
      features: []
    };
  }, [router.pathname]);
  
  // 模拟认证状态
  const isAuthenticated = true; // 实际项目中从认证上下文获取
  
  // 判断是否应该连接
  const shouldConnect = useMemo(() => {
    if (!config.enabled) return false;
    if (config.requireAuth && !isAuthenticated) return false;
    return config.autoConnect;
  }, [config, isAuthenticated]);
  
  // 连接管理
  useEffect(() => {
    if (shouldConnect) {
      console.log(`页面 ${router.pathname} 需要WebSocket连接`);
      // 这里实现实际的连接逻辑
      setConnectionStatus('connecting');
      setTimeout(() => {
        setIsConnected(true);
        setConnectionStatus('connected');
      }, 1000);
    } else {
      console.log(`页面 ${router.pathname} 不需要WebSocket连接`);
      setIsConnected(false);
      setConnectionStatus('disconnected');
    }
  }, [shouldConnect, router.pathname]);
  
  return {
    isConnected,
    connectionStatus,
    config,
    shouldConnect
  };
}
```

**练习要求**：
- 实现页面配置系统
- 添加认证检查逻辑
- 处理页面路由变化
- 实现连接状态管理

---

### 练习3：消息类型定义和处理

**目标**：掌握消息类型定义和事件处理机制

**任务**：
1. 定义完整的消息类型
2. 实现消息序列化/反序列化
3. 创建消息处理器系统

**代码位置**：`web/src/service/websocket/types.ts` 和 `web/src/service/websocket/handlers/index.ts`

**参考实现**：
```typescript
// types.ts
export interface WebSocketMessage {
  id: string;
  type: MessageType;
  action: string;
  data: any;
  timestamp: number;
  sender?: {
    id: string;
    name: string;
    avatar?: string;
  };
}

export type MessageType = 
  | 'text'
  | 'image'
  | 'file'
  | 'audio'
  | 'system'
  | 'typing'
  | 'read'
  | 'heartbeat';

export interface ChatMessage extends WebSocketMessage {
  type: 'text' | 'image' | 'file' | 'audio';
  conversationId: string;
  content: string;
  replyTo?: string;
}

export interface TypingMessage extends WebSocketMessage {
  type: 'typing';
  conversationId: string;
  isTyping: boolean;
}

export interface SystemMessage extends WebSocketMessage {
  type: 'system';
  level: 'info' | 'warning' | 'error';
  title: string;
  message: string;
}

// handlers/index.ts
type MessageHandler = (message: WebSocketMessage) => Promise<void>;

export class MessageEventHandler {
  private handlers: Map<string, MessageHandler> = new Map();
  
  registerHandler(action: string, handler: MessageHandler): void {
    this.handlers.set(action, handler);
  }
  
  async handleMessage(message: WebSocketMessage): Promise<void> {
    const handler = this.handlers.get(message.action);
    
    if (handler) {
      try {
        await handler(message);
      } catch (error) {
        console.error(`处理消息失败 [${message.action}]:`, error);
      }
    } else {
      console.warn(`未找到消息处理器: ${message.action}`);
    }
  }
  
  // 注册默认处理器
  registerDefaultHandlers(): void {
    this.registerHandler('new_message', async (message: ChatMessage) => {
      console.log('处理新消息:', message.data.content);
      // 这里可以触发UI更新
    });
    
    this.registerHandler('typing_status', async (message: TypingMessage) => {
      console.log('处理输入状态:', message.data.isTyping);
      // 这里可以更新输入指示器
    });
    
    this.registerHandler('system_notification', async (message: SystemMessage) => {
      console.log('处理系统通知:', message.data.message);
      // 这里可以显示系统通知
    });
  }
}
```

**练习要求**：
- 完善消息类型定义
- 实现消息验证逻辑
- 添加更多消息处理器
- 实现错误处理机制

---

### 练习4：连接状态管理

**目标**：实现完整的连接状态管理和用户反馈

**任务**：
1. 创建连接状态管理Hook
2. 实现状态指示器组件
3. 添加用户交互功能

**代码位置**：`web/src/hooks/useWebSocketState.ts` 和 `web/src/components/WebSocketStatus.tsx`

**参考实现**：
```typescript
// useWebSocketState.ts
import { useState, useCallback } from 'react';

export type ConnectionStatus = 
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'error';

export interface ConnectionState {
  status: ConnectionStatus;
  lastConnected?: Date;
  lastDisconnected?: Date;
  reconnectAttempts: number;
  error?: string;
}

export function useWebSocketState() {
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    status: 'disconnected',
    reconnectAttempts: 0
  });
  
  const updateStatus = useCallback((status: ConnectionStatus, error?: string) => {
    setConnectionState(prev => ({
      ...prev,
      status,
      error,
      lastConnected: status === 'connected' ? new Date() : prev.lastConnected,
      lastDisconnected: status === 'disconnected' ? new Date() : prev.lastDisconnected
    }));
  }, []);
  
  const incrementReconnectAttempts = useCallback(() => {
    setConnectionState(prev => ({
      ...prev,
      reconnectAttempts: prev.reconnectAttempts + 1
    }));
  }, []);
  
  const resetReconnectAttempts = useCallback(() => {
    setConnectionState(prev => ({
      ...prev,
      reconnectAttempts: 0
    }));
  }, []);
  
  return {
    connectionState,
    updateStatus,
    incrementReconnectAttempts,
    resetReconnectAttempts
  };
}

// WebSocketStatus.tsx
import React from 'react';
import { ConnectionStatus } from '@/hooks/useWebSocketState';

interface WebSocketStatusProps {
  status: ConnectionStatus;
  reconnectAttempts: number;
  onReconnect: () => void;
  onRefresh: () => void;
}

export function WebSocketStatus({ 
  status, 
  reconnectAttempts, 
  onReconnect, 
  onRefresh 
}: WebSocketStatusProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      case 'reconnecting': return 'text-orange-500';
      case 'disconnected': return 'text-red-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };
  
  const getStatusText = () => {
    switch (status) {
      case 'connected': return '已连接';
      case 'connecting': return '连接中...';
      case 'reconnecting': return `重连中... (${reconnectAttempts}/15)`;
      case 'disconnected': return '已断开';
      case 'error': return '连接错误';
      default: return '未知状态';
    }
  };
  
  const getStatusIcon = () => {
    switch (status) {
      case 'connected': return '🟢';
      case 'connecting': return '🟡';
      case 'reconnecting': return '🟠';
      case 'disconnected': return '🔴';
      case 'error': return '❌';
      default: return '❓';
    }
  };
  
  return (
    <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded-lg">
      <span className="text-lg">{getStatusIcon()}</span>
      <span className={`text-sm font-medium ${getStatusColor()}`}>
        {getStatusText()}
      </span>
      
      {status === 'disconnected' && (
        <button
          onClick={onReconnect}
          className="ml-2 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          重连
        </button>
      )}
      
      {status === 'error' && (
        <button
          onClick={onRefresh}
          className="ml-2 px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
        >
          刷新
        </button>
      )}
    </div>
  );
}
```

**练习要求**：
- 完善状态管理逻辑
- 添加更多状态指示器
- 实现自动重连功能
- 优化用户交互体验

---

## 🎓 进阶练习（5-8）

### 练习5：消息队列和性能优化

**目标**：实现消息队列和性能优化机制

**任务**：
1. 创建消息队列系统
2. 实现消息批处理
3. 添加性能监控

**代码位置**：`web/src/service/websocket/core/messageQueue.ts`

**参考实现**：
```typescript
export class MessageQueue {
  private queue: WebSocketMessage[] = [];
  private maxSize: number = 100;
  private processing: boolean = false;
  private batchSize: number = 10;
  private batchTimeout: number = 100; // 100ms批处理超时
  
  add(message: WebSocketMessage): void {
    this.queue.push(message);
    
    // 限制队列大小
    if (this.queue.length > this.maxSize) {
      this.queue = this.queue.slice(-this.maxSize);
    }
    
    // 触发批处理
    this.scheduleBatchProcessing();
  }
  
  private scheduleBatchProcessing(): void {
    if (!this.processing) {
      this.processing = true;
      
      // 立即处理一批消息
      this.processBatch();
      
      // 设置超时处理剩余消息
      setTimeout(() => {
        if (this.queue.length > 0) {
          this.processBatch();
        }
        this.processing = false;
      }, this.batchTimeout);
    }
  }
  
  private async processBatch(): Promise<void> {
    const batch = this.queue.splice(0, this.batchSize);
    
    if (batch.length === 0) return;
    
    console.log(`处理消息批次: ${batch.length} 条消息`);
    
    // 并行处理消息
    const promises = batch.map(message => this.processMessage(message));
    
    try {
      await Promise.allSettled(promises);
    } catch (error) {
      console.error('批处理消息失败:', error);
    }
  }
  
  private async processMessage(message: WebSocketMessage): Promise<void> {
    const startTime = performance.now();
    
    try {
      // 根据消息类型分发处理
      switch (message.type) {
        case 'text':
          await this.handleTextMessage(message);
          break;
        case 'image':
          await this.handleImageMessage(message);
          break;
        case 'file':
          await this.handleFileMessage(message);
          break;
        case 'system':
          await this.handleSystemMessage(message);
          break;
        default:
          console.warn('未知消息类型:', message.type);
      }
      
      const endTime = performance.now();
      console.log(`消息处理完成: ${message.type}, 耗时: ${endTime - startTime}ms`);
      
    } catch (error) {
      console.error(`处理消息失败 [${message.type}]:`, error);
    }
  }
  
  private async handleTextMessage(message: WebSocketMessage): Promise<void> {
    // 模拟文本消息处理
    await new Promise(resolve => setTimeout(resolve, 10));
    console.log('处理文本消息:', message.data.content);
  }
  
  private async handleImageMessage(message: WebSocketMessage): Promise<void> {
    // 模拟图片消息处理
    await new Promise(resolve => setTimeout(resolve, 50));
    console.log('处理图片消息:', message.data.url);
  }
  
  private async handleFileMessage(message: WebSocketMessage): Promise<void> {
    // 模拟文件消息处理
    await new Promise(resolve => setTimeout(resolve, 30));
    console.log('处理文件消息:', message.data.fileName);
  }
  
  private async handleSystemMessage(message: WebSocketMessage): Promise<void> {
    // 模拟系统消息处理
    await new Promise(resolve => setTimeout(resolve, 5));
    console.log('处理系统消息:', message.data.message);
  }
  
  // 获取队列状态
  getStats() {
    return {
      queueLength: this.queue.length,
      isProcessing: this.processing,
      maxSize: this.maxSize
    };
  }
  
  // 清空队列
  clear(): void {
    this.queue = [];
  }
}
```

**练习要求**：
- 实现消息优先级处理
- 添加消息去重机制
- 实现队列监控和统计
- 优化批处理性能

---

### 练习6：连接复用和资源管理

**目标**：实现连接复用和内存泄漏防护

**任务**：
1. 创建单例连接管理器
2. 实现连接复用机制
3. 添加资源清理逻辑

**代码位置**：`web/src/service/websocket/index.ts`

**参考实现**：
```typescript
class WebSocketManager {
  private static instance: WebSocketManager;
  private connection: WebSocketConnection | null = null;
  private subscribers: Set<(message: WebSocketMessage) => void> = new Set();
  private connectionConfig: WebSocketConfig | null = null;
  private isConnecting: boolean = false;
  
  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }
  
  async connect(config: WebSocketConfig): Promise<void> {
    // 如果已经连接且配置相同，直接返回
    if (this.connection && this.connection.isConnected() && 
        JSON.stringify(this.connectionConfig) === JSON.stringify(config)) {
      return;
    }
    
    // 如果正在连接，等待连接完成
    if (this.isConnecting) {
      return new Promise((resolve, reject) => {
        const checkConnection = () => {
          if (!this.isConnecting) {
            if (this.connection && this.connection.isConnected()) {
              resolve();
            } else {
              reject(new Error('连接失败'));
            }
          } else {
            setTimeout(checkConnection, 100);
          }
        };
        checkConnection();
      });
    }
    
    this.isConnecting = true;
    
    try {
      // 断开现有连接
      if (this.connection) {
        await this.disconnect();
      }
      
      // 创建新连接
      this.connection = new WebSocketConnection();
      await this.connection.connect(config.url);
      
      // 设置消息处理器
      this.connection.onMessage = (message) => {
        this.notifySubscribers(message);
      };
      
      this.connectionConfig = config;
      console.log('WebSocket连接已建立');
      
    } catch (error) {
      console.error('WebSocket连接失败:', error);
      throw error;
    } finally {
      this.isConnecting = false;
    }
  }
  
  subscribe(callback: (message: WebSocketMessage) => void): () => void {
    this.subscribers.add(callback);
    
    // 返回取消订阅函数
    return () => {
      this.subscribers.delete(callback);
    };
  }
  
  private notifySubscribers(message: WebSocketMessage): void {
    this.subscribers.forEach(callback => {
      try {
        callback(message);
      } catch (error) {
        console.error('消息处理错误:', error);
      }
    });
  }
  
  async sendMessage(message: WebSocketMessage): Promise<void> {
    if (!this.connection || !this.connection.isConnected()) {
      throw new Error('WebSocket未连接');
    }
    
    await this.connection.send(message);
  }
  
  async disconnect(): Promise<void> {
    if (this.connection) {
      await this.connection.disconnect();
      this.connection = null;
      this.connectionConfig = null;
    }
    
    // 清空订阅者
    this.subscribers.clear();
  }
  
  isConnected(): boolean {
    return this.connection?.isConnected() || false;
  }
  
  getConnectionConfig(): WebSocketConfig | null {
    return this.connectionConfig;
  }
  
  // 获取连接统计信息
  getStats() {
    return {
      isConnected: this.isConnected(),
      subscriberCount: this.subscribers.size,
      isConnecting: this.isConnecting,
      config: this.connectionConfig
    };
  }
}

export const wsManager = WebSocketManager.getInstance();
```

**练习要求**：
- 实现连接池管理
- 添加连接健康检查
- 实现自动重连机制
- 优化资源使用

---

### 练习7：错误边界和异常处理

**目标**：实现完善的错误处理和恢复机制

**任务**：
1. 创建WebSocket错误边界组件
2. 实现错误报告机制
3. 添加自动恢复功能

**代码位置**：`web/src/components/WebSocketErrorBoundary.tsx`

**参考实现**：
```typescript
import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
  retryCount: number;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  maxRetries?: number;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

export class WebSocketErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { 
      hasError: false, 
      retryCount: 0 
    };
  }
  
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('WebSocket错误边界捕获到错误:', error, errorInfo);
    
    this.setState({ errorInfo });
    
    // 调用错误回调
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
    
    // 发送错误报告
    this.reportError(error, errorInfo);
  }
  
  private async reportError(error: Error, errorInfo: React.ErrorInfo) {
    try {
      const errorReport = {
        error: {
          message: error.message,
          stack: error.stack,
          name: error.name
        },
        errorInfo: {
          componentStack: errorInfo.componentStack
        },
        context: {
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString()
        }
      };
      
      // 发送错误报告到服务器
      await fetch('/api/v1/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(errorReport)
      });
      
    } catch (reportError) {
      console.error('发送错误报告失败:', reportError);
    }
  }
  
  private handleRetry = () => {
    const maxRetries = this.props.maxRetries || 3;
    
    if (this.state.retryCount < maxRetries) {
      this.setState(prev => ({
        hasError: false,
        error: undefined,
        errorInfo: undefined,
        retryCount: prev.retryCount + 1
      }));
    } else {
      // 达到最大重试次数，刷新页面
      window.location.reload();
    }
  };
  
  private handleRefresh = () => {
    window.location.reload();
  };
  
  render() {
    if (this.state.hasError) {
      const maxRetries = this.props.maxRetries || 3;
      const canRetry = this.state.retryCount < maxRetries;
      
      return (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-red-800">
                WebSocket连接错误
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{this.state.error?.message || '未知错误'}</p>
                {this.state.errorInfo && (
                  <details className="mt-2">
                    <summary className="cursor-pointer">错误详情</summary>
                    <pre className="mt-1 text-xs bg-red-100 p-2 rounded overflow-auto">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
              <div className="mt-4 flex space-x-2">
                {canRetry && (
                  <button
                    onClick={this.handleRetry}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                  >
                    重试 ({this.state.retryCount + 1}/{maxRetries})
                  </button>
                )}
                <button
                  onClick={this.handleRefresh}
                  className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700"
                >
                  刷新页面
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

**练习要求**：
- 实现错误分类处理
- 添加错误恢复策略
- 实现错误监控和报警
- 优化错误用户体验

---

### 练习8：消息通知系统

**目标**：实现完整的消息通知和用户反馈系统

**任务**：
1. 创建消息通知组件
2. 实现桌面通知
3. 添加声音和视觉反馈

**代码位置**：`web/src/components/MessageNotification.tsx`

**参考实现**：
```typescript
import React, { useState, useEffect, useRef } from 'react';
import { WebSocketMessage } from '@/service/websocket/types';

interface Notification {
  id: string;
  title: string;
  content: string;
  timestamp: Date;
  type: 'message' | 'system' | 'error';
  level?: 'info' | 'warning' | 'error';
  action?: string;
  data?: any;
}

interface MessageNotificationProps {
  lastMessage?: WebSocketMessage | null;
  enabled?: boolean;
}

export function MessageNotification({ lastMessage, enabled = true }: MessageNotificationProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const audioRef = useRef<HTMLAudioElement | null>(null);
  
  // 请求通知权限
  useEffect(() => {
    if ('Notification' in window) {
      setPermission(Notification.permission);
      
      if (Notification.permission === 'default') {
        Notification.requestPermission().then(setPermission);
      }
    }
  }, []);
  
  // 创建音频元素
  useEffect(() => {
    audioRef.current = new Audio('/sounds/notification.mp3');
    audioRef.current.preload = 'auto';
  }, []);
  
  // 处理新消息
  useEffect(() => {
    if (!enabled || !lastMessage) return;
    
    const notification = createNotification(lastMessage);
    if (notification) {
      addNotification(notification);
    }
  }, [lastMessage, enabled]);
  
  const createNotification = (message: WebSocketMessage): Notification | null => {
    switch (message.type) {
      case 'text':
        return {
          id: message.id,
          title: message.sender?.name || '新消息',
          content: message.data.content,
          timestamp: new Date(),
          type: 'message',
          action: 'open_conversation',
          data: { conversationId: message.data.conversationId }
        };
        
      case 'system':
        return {
          id: message.id,
          title: message.data.title || '系统通知',
          content: message.data.message,
          timestamp: new Date(),
          type: 'system',
          level: message.data.level || 'info',
          action: message.data.action,
          data: message.data
        };
        
      default:
        return null;
    }
  };
  
  const addNotification = (notification: Notification) => {
    setNotifications(prev => [...prev, notification]);
    
    // 播放提示音
    playNotificationSound();
    
    // 显示桌面通知
    showDesktopNotification(notification);
    
    // 自动移除通知（5秒后）
    setTimeout(() => {
      removeNotification(notification.id);
    }, 5000);
  };
  
  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };
  
  const playNotificationSound = () => {
    if (audioRef.current) {
      audioRef.current.play().catch(error => {
        console.warn('播放提示音失败:', error);
      });
    }
  };
  
  const showDesktopNotification = (notification: Notification) => {
    if (permission === 'granted' && 'Notification' in window) {
      const desktopNotification = new Notification(notification.title, {
        body: notification.content,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: notification.id,
        requireInteraction: notification.type === 'error',
        actions: notification.action ? [
          {
            action: notification.action,
            title: '查看详情'
          }
        ] : undefined
      });
      
      // 处理通知点击
      desktopNotification.onclick = () => {
        handleNotificationClick(notification);
        desktopNotification.close();
      };
      
      // 处理通知操作
      if (notification.action) {
        desktopNotification.onactionclick = (event) => {
          if (event.action === notification.action) {
            handleNotificationClick(notification);
          }
          desktopNotification.close();
        };
      }
    }
  };
  
  const handleNotificationClick = (notification: Notification) => {
    switch (notification.action) {
      case 'open_conversation':
        // 打开对话
        window.location.href = `/chat?conversation=${notification.data.conversationId}`;
        break;
      case 'open_settings':
        // 打开设置
        window.location.href = '/settings';
        break;
      default:
        // 默认行为
        window.focus();
    }
  };
  
  const getNotificationIcon = (type: string, level?: string) => {
    switch (type) {
      case 'message':
        return '💬';
      case 'system':
        switch (level) {
          case 'warning': return '⚠️';
          case 'error': return '❌';
          default: return 'ℹ️';
        }
      case 'error':
        return '❌';
      default:
        return '📢';
    }
  };
  
  const getNotificationColor = (type: string, level?: string) => {
    switch (type) {
      case 'message':
        return 'border-blue-200 bg-blue-50';
      case 'system':
        switch (level) {
          case 'warning': return 'border-yellow-200 bg-yellow-50';
          case 'error': return 'border-red-200 bg-red-50';
          default: return 'border-gray-200 bg-gray-50';
        }
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };
  
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map(notification => (
        <div
          key={notification.id}
          className={`border rounded-lg shadow-lg p-4 max-w-sm transition-all duration-300 ${getNotificationColor(notification.type, notification.level)}`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <span className="text-lg">{getNotificationIcon(notification.type, notification.level)}</span>
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-gray-900 truncate">
                  {notification.title}
                </h4>
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                  {notification.content}
                </p>
                <p className="text-xs text-gray-400 mt-2">
                  {notification.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
            <button
              onClick={() => removeNotification(notification.id)}
              className="ml-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              ✕
            </button>
          </div>
          
          {notification.action && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <button
                onClick={() => handleNotificationClick(notification)}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium"
              >
                查看详情 →
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

**练习要求**：
- 实现通知分类管理
- 添加通知优先级
- 实现通知历史记录
- 优化通知交互体验

---

## 🎓 高级练习（9-12）

### 练习9：聊天系统完整实现

**目标**：实现一个完整的聊天系统

**任务**：
1. 创建聊天页面组件
2. 实现消息发送和接收
3. 添加输入状态指示器

**代码位置**：`web/src/app/chat/page.tsx` 和 `web/src/components/chat/`

**练习要求**：
- 实现完整的聊天界面
- 支持文本、图片、文件消息
- 添加消息时间戳和状态
- 实现消息搜索功能
- 添加表情和快捷回复

---

### 练习10：实时协作功能

**目标**：实现实时协作功能

**任务**：
1. 实现多人实时编辑
2. 添加光标位置同步
3. 实现冲突解决机制

**练习要求**：
- 实现操作转换算法
- 添加用户在线状态
- 实现编辑冲突检测
- 优化实时同步性能

---

### 练习11：性能监控和优化

**目标**：实现WebSocket性能监控

**任务**：
1. 创建性能监控系统
2. 实现连接质量检测
3. 添加性能指标收集

**练习要求**：
- 监控连接延迟和丢包率
- 实现自动质量调整
- 添加性能报告功能
- 优化资源使用

---

### 练习12：移动端适配

**目标**：实现移动端WebSocket优化

**任务**：
1. 适配移动端连接管理
2. 实现离线消息同步
3. 添加推送通知

**练习要求**：
- 优化移动端连接策略
- 实现消息离线存储
- 添加推送通知集成
- 优化移动端性能

---

## 🎯 综合项目练习

### 项目1：实时协作编辑器

**目标**：实现类似Google Docs的实时协作编辑器

**功能要求**：
- 多人实时编辑文档
- 光标位置同步
- 编辑冲突解决
- 版本历史记录
- 权限管理

**技术栈**：
- React + TypeScript
- WebSocket实时通信
- 操作转换算法
- 富文本编辑器

**实现步骤**：
1. 设计文档数据结构
2. 实现操作转换算法
3. 创建WebSocket通信层
4. 构建富文本编辑器
5. 添加用户界面
6. 实现权限控制
7. 添加版本管理
8. 性能优化

### 项目2：实时监控仪表板

**目标**：实现实时数据监控仪表板

**功能要求**：
- 实时数据展示
- 多数据源集成
- 图表可视化
- 告警系统
- 历史数据查询

**技术栈**：
- React + TypeScript
- WebSocket数据推送
- 图表库（Chart.js/D3.js）
- 实时数据处理

**实现步骤**：
1. 设计数据模型
2. 实现WebSocket数据推送
3. 创建图表组件
4. 构建仪表板布局
5. 添加告警系统
6. 实现数据过滤
7. 添加历史查询
8. 性能优化

---

## 🎯 练习评估标准

### 基础练习（1-4）
- ✅ 代码能正常运行
- ✅ 功能实现完整
- ✅ 错误处理得当
- ✅ 代码结构清晰

### 进阶练习（5-8）
- ✅ 性能优化合理
- ✅ 资源管理完善
- ✅ 错误处理健壮
- ✅ 用户体验良好

### 高级练习（9-12）
- ✅ 功能实现完整
- ✅ 性能表现优秀
- ✅ 代码质量高
- ✅ 扩展性良好

### 综合项目
- ✅ 项目架构合理
- ✅ 功能实现完整
- ✅ 性能表现优秀
- ✅ 代码质量高
- ✅ 文档完善

---

## 🎉 练习完成指南

### 学习建议

1. **循序渐进**
   - 按顺序完成练习
   - 确保基础概念掌握
   - 遇到问题及时查阅文档

2. **动手实践**
   - 每个练习都要实际编码
   - 尝试修改和扩展功能
   - 测试不同的使用场景

3. **代码审查**
   - 检查代码质量
   - 优化性能表现
   - 完善错误处理

4. **文档记录**
   - 记录学习过程
   - 总结技术要点
   - 分享学习心得

### 扩展学习

完成所有练习后，建议继续学习：

1. **WebRTC**：点对点通信技术
2. **Server-Sent Events**：服务器推送事件
3. **GraphQL Subscriptions**：GraphQL实时订阅
4. **Socket.IO**：更高级的WebSocket库
5. **消息队列**：RabbitMQ、Redis Streams等

---

**练习版本**：WebSocket前端实战练习 V1.0
**适用对象**：前端开发者、全栈开发者
**前置知识**：JavaScript/TypeScript基础、React基础
**练习时长**：8-12小时
**项目时长**：16-24小时
