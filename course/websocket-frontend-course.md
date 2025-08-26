# 🚀 前端WebSocket、广播、事件系统实战教案

## 📚 课程概述

本课程专注于前端WebSocket技术的深度应用，基于安美智享项目的实际代码，系统讲解WebSocket连接管理、消息广播、事件处理等核心概念。通过理论与实践相结合，帮助您掌握现代前端实时通信系统的开发技能。

### 🎯 学习目标

- 深入理解WebSocket在前端的应用原理
- 掌握页面级WebSocket连接管理策略
- 学会消息广播和事件处理机制
- 能够设计和实现高效的实时通信功能
- 理解分布式连接管理和状态同步

### 📋 课程大纲

1. **WebSocket基础** - 协议原理与前端应用
2. **连接管理** - 页面级智能连接策略
3. **消息处理** - 事件驱动架构设计
4. **状态管理** - 连接状态与用户反馈
5. **实战应用** - 聊天系统完整实现
6. **性能优化** - 连接复用与资源管理

---

## 🎓 第一部分：WebSocket基础 - 协议原理与前端应用

### 1.1 WebSocket协议基础

#### 1.1.1 什么是WebSocket？

WebSocket是一种在单个TCP连接上进行全双工通信的协议，为前端提供了真正的实时双向通信能力。

```javascript
// 传统HTTP轮询（低效）
setInterval(async () => {
  const response = await fetch('/api/messages');
  const messages = await response.json();
  if (messages.length > 0) {
    updateUI(messages);
  }
}, 1000); // 每秒轮询一次

// WebSocket（高效）
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  updateUI(message); // 实时接收消息
};
```

#### 1.1.2 WebSocket生命周期

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

// 1. 连接建立
ws.onopen = () => {
  console.log('WebSocket连接已建立');
};

// 2. 消息接收
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到消息:', data);
};

// 3. 连接关闭
ws.onclose = (event) => {
  console.log('WebSocket连接已关闭:', event.code, event.reason);
};

// 4. 错误处理
ws.onerror = (error) => {
  console.error('WebSocket错误:', error);
};
```

### 1.2 项目中的WebSocket架构

#### 1.2.1 页面级连接管理

项目采用页面级WebSocket管理策略，根据页面需求智能管理连接：

```typescript
// 文件：web/src/hooks/useWebSocketByPage.ts
interface PageWebSocketConfig {
  enabled: boolean;           // 是否启用WebSocket
  requireAuth: boolean;       // 是否需要认证
  autoConnect: boolean;       // 是否自动连接
  connectionType: string;     // 连接类型
  features: string[];         // 功能特性
}

const PAGE_WEBSOCKET_CONFIG: Record<string, PageWebSocketConfig> = {
  // 聊天页面 - 完整功能
  '/chat': { 
    enabled: true, 
    requireAuth: true, 
    autoConnect: true,
    connectionType: 'chat',
    features: ['messaging', 'typing_indicator', 'file_upload', 'voice_note']
  },
  
  // 管理页面 - 监控功能
  '/admin': { 
    enabled: true, 
    requireAuth: true, 
    autoConnect: true,
    connectionType: 'admin',
    features: ['system_notifications', 'user_monitoring', 'real_time_stats']
  },
  
  // 登录页面 - 不启用WebSocket
  '/login': { 
    enabled: false, 
    requireAuth: false, 
    autoConnect: false,
    connectionType: 'none',
    features: []
  }
};
```

#### 1.2.2 智能连接策略

```typescript
// 文件：web/src/hooks/useWebSocketByPage.ts
export function useWebSocketByPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  
  // 获取当前页面配置
  const config = useMemo(() => {
    const path = router.pathname;
    return PAGE_WEBSOCKET_CONFIG[path] || DEFAULT_CONFIG;
  }, [router.pathname]);
  
  // 智能连接决策
  const shouldConnect = useMemo(() => {
    if (!config.enabled) return false;
    if (config.requireAuth && !isAuthenticated) return false;
    return config.autoConnect;
  }, [config, isAuthenticated]);
  
  // 根据决策建立连接
  useEffect(() => {
    if (shouldConnect) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }
  }, [shouldConnect]);
  
  return { isConnected, connectionStatus, lastMessage, sendMessage, config };
}
```

---

## 🎓 第二部分：连接管理 - 页面级智能连接策略

### 2.1 连接生命周期管理

#### 2.1.1 连接建立流程

```typescript
// 文件：web/src/service/websocket/core/connection.ts
export class WebSocketConnection {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 15;
  
  async connect(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(url);
      
        this.ws.onopen = () => {
          console.log('WebSocket连接已建立');
          this.reconnectAttempts = 0;
          resolve();
        };
      
        this.ws.onerror = (error) => {
          console.error('WebSocket连接错误:', error);
          reject(error);
        };
      
        this.ws.onclose = (event) => {
          console.log('WebSocket连接关闭:', event.code, event.reason);
          this.handleReconnect();
        };
      
      } catch (error) {
        reject(error);
      }
    });
  }
}
```

#### 2.1.2 智能重连机制

```typescript
// 文件：web/src/service/websocket/core/reconnect.ts
export class ReconnectManager {
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 15;
  private baseDelay = 2000; // 2秒基础延迟
  
  private async handleReconnect(): Promise<void> {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('达到最大重连次数，停止重连');
      return;
    }
  
    // 指数退避策略
    const delay = this.baseDelay * Math.pow(2, this.reconnectAttempts);
    const maxDelay = 30000; // 最大30秒
    const actualDelay = Math.min(delay, maxDelay);
  
    console.log(`第${this.reconnectAttempts + 1}次重连，延迟${actualDelay}ms`);
  
    await new Promise(resolve => setTimeout(resolve, actualDelay));
  
    try {
      await this.connect();
      this.reconnectAttempts = 0; // 重连成功，重置计数
    } catch (error) {
      this.reconnectAttempts++;
      await this.handleReconnect(); // 递归重连
    }
  }
}
```

### 2.2 心跳机制

#### 2.2.1 心跳实现

```typescript
// 文件：web/src/service/websocket/core/heartbeat.ts
export class HeartbeatManager {
  private heartbeatInterval: number = 45000; // 45秒
  private heartbeatTimer: NodeJS.Timeout | null = null;
  
  startHeartbeat(ws: WebSocket): void {
    this.stopHeartbeat(); // 停止之前的心跳
  
    this.heartbeatTimer = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        const heartbeatMessage = {
          type: 'heartbeat',
          timestamp: Date.now()
        };
      
        ws.send(JSON.stringify(heartbeatMessage));
        console.log('发送心跳消息');
      }
    }, this.heartbeatInterval);
  }
  
  stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}
```

#### 2.2.2 连接状态监控

```typescript
// 文件：web/src/components/WebSocketStatus.tsx
export function WebSocketStatus() {
  const { isConnected, connectionStatus, reconnect } = useWebSocketByPage();
  
  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      case 'disconnected': return 'text-red-500';
      case 'reconnecting': return 'text-orange-500';
      default: return 'text-gray-500';
    }
  };
  
  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return '已连接';
      case 'connecting': return '连接中...';
      case 'disconnected': return '已断开';
      case 'reconnecting': return '重连中...';
      default: return '未知状态';
    }
  };
  
  return (
    <div className="flex items-center space-x-2">
      <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
      <span className="text-sm">{getStatusText()}</span>
      {connectionStatus === 'disconnected' && (
        <button 
          onClick={reconnect}
          className="text-xs text-blue-500 hover:text-blue-700"
        >
          重连
        </button>
      )}
    </div>
  );
}
```

---

## 🎓 第三部分：消息处理 - 事件驱动架构设计

### 3.1 消息类型定义

#### 3.1.1 消息结构

```typescript
// 文件：web/src/service/websocket/types.ts
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
```

#### 3.1.2 消息序列化

```typescript
// 文件：web/src/service/websocket/core/serializer.ts
export class MessageSerializer {
  static serialize(message: WebSocketMessage): string {
    try {
      return JSON.stringify({
        ...message,
        timestamp: Date.now()
      });
    } catch (error) {
      console.error('消息序列化失败:', error);
      throw new Error('消息序列化失败');
    }
  }
  
  static deserialize(data: string): WebSocketMessage {
    try {
      const message = JSON.parse(data);
    
      // 验证必要字段
      if (!message.id || !message.type || !message.action) {
        throw new Error('消息格式无效');
      }
    
      return message;
    } catch (error) {
      console.error('消息反序列化失败:', error);
      throw new Error('消息反序列化失败');
    }
  }
}
```

### 3.2 事件处理器

#### 3.2.1 事件处理器注册

事件处理器模式是WebSocket消息处理的核心设计模式。它通过注册不同的处理器函数来处理不同类型的消息，实现了关注点分离和代码模块化。

**核心思想**：将消息处理逻辑分散到不同的处理器中，而不是在一个巨大的switch语句中处理所有消息类型。

```typescript
// 文件：web/src/service/websocket/handlers/index.ts

// 核心类型定义
type MessageHandler = (message: WebSocketMessage) => Promise<void>;

class MessageEventHandler {
  private handlers = new Map<string, MessageHandler>();
  
  // 注册处理器
  registerHandler(action: string, handler: MessageHandler) {
    this.handlers.set(action, handler);
  }
  
  // 处理消息
  async handleMessage(message: WebSocketMessage) {
    const handler = this.handlers.get(message.action);
    
    if (handler) {
      try {
        await handler(message);
      } catch (error) {
        console.error(`处理失败 [${message.action}]:`, error);
      }
    }
  }
}

// 创建事件处理器
const eventHandler = new MessageEventHandler();

// 注册聊天消息处理器
eventHandler.registerHandler('new_message', async (message) => {
  // 伪代码：添加到聊天列表
  addMessageToChat(message);
  
  // 伪代码：播放提示音
  playNotificationSound();
  
  // 伪代码：显示桌面通知
  showDesktopNotification(message);
});

// 注册输入状态处理器
eventHandler.registerHandler('typing_status', async (message) => {
  // 伪代码：更新输入状态
  updateTypingStatus(
    message.data.conversationId,
    message.sender.id,
    message.data.isTyping
  );
});

// 注册系统通知处理器
eventHandler.registerHandler('system_notification', async (message) => {
  // 伪代码：显示系统通知
  showSystemNotification(message.data);
});
```

#### 3.2.2 与WebSocket集成

```typescript
// 伪代码：在WebSocket连接中集成
class WebSocketConnection {
  setupMessageHandler() {
    this.ws.onmessage = async (event) => {
      const message = JSON.parse(event.data);
      
      // 使用事件处理器处理消息
      await eventHandler.handleMessage(message);
    };
  }
}
```

#### 3.2.3 关键优势

**模块化设计**：每个处理器职责单一
```typescript
// 每个处理器只处理一种类型的消息
const chatMessageHandler = async (message) => {
  // 只处理聊天消息相关逻辑
};

const typingHandler = async (message) => {
  // 只处理输入状态相关逻辑
};
```

**易于扩展**：添加新消息类型很简单
```typescript
// 添加新消息类型
eventHandler.registerHandler('file_upload', async (message) => {
  // 处理文件上传消息
});

eventHandler.registerHandler('voice_message', async (message) => {
  // 处理语音消息
});
```

**错误隔离**：每个处理器的错误不会影响其他处理器
```typescript
// 每个处理器的错误不会影响其他处理器
eventHandler.registerHandler('new_message', async (message) => {
  try {
    // 处理消息
  } catch (error) {
    // 只影响当前处理器
    console.error('聊天消息处理失败:', error);
  }
});
```

#### 3.2.4 消息适配器

消息适配器负责在WebSocket消息和业务消息之间进行转换，确保数据格式的一致性。

```typescript
// 文件：web/src/service/websocket/adapters/messageAdapter.ts
export class MessageAdapter {
  // 将业务消息转换为WebSocket消息
  static toWebSocketMessage(
    action: string, 
    data: any, 
    type: MessageType = 'text'
  ): WebSocketMessage {
    return {
      id: generateMessageId(),
      type,
      action,
      data,
      timestamp: Date.now()
    };
  }
  
  // 将WebSocket消息转换为业务消息
  static fromWebSocketMessage(message: WebSocketMessage): any {
    switch (message.type) {
      case 'text':
        return this.parseTextMessage(message);
      case 'image':
        return this.parseImageMessage(message);
      case 'file':
        return this.parseFileMessage(message);
      case 'audio':
        return this.parseAudioMessage(message);
      case 'system':
        return this.parseSystemMessage(message);
      default:
        return message.data;
    }
  }
  
  private static parseTextMessage(message: WebSocketMessage): ChatMessage {
    return {
      ...message,
      content: message.data.content,
      conversationId: message.data.conversationId
    } as ChatMessage;
  }
  
  private static parseImageMessage(message: WebSocketMessage): ChatMessage {
    return {
      ...message,
      content: message.data.url,
      conversationId: message.data.conversationId
    } as ChatMessage;
  }
}
```

---

## 🎓 第四部分：状态管理 - 连接状态与用户反馈

### 4.1 连接状态管理

#### 4.1.1 状态定义

```typescript
// 文件：web/src/service/websocket/types.ts
export type ConnectionStatus = 
  | 'disconnected'    // 未连接
  | 'connecting'      // 连接中
  | 'connected'       // 已连接
  | 'reconnecting'    // 重连中
  | 'error';          // 错误状态

export interface ConnectionState {
  status: ConnectionStatus;
  lastConnected?: Date;
  lastDisconnected?: Date;
  reconnectAttempts: number;
  error?: string;
}
```

#### 4.1.2 状态管理Hook

```typescript
// 文件：web/src/hooks/useWebSocketByPage.ts
export function useWebSocketByPage() {
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    status: 'disconnected',
    reconnectAttempts: 0
  });
  
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [messageQueue, setMessageQueue] = useState<WebSocketMessage[]>([]);
  
  // 更新连接状态
  const updateConnectionStatus = useCallback((status: ConnectionStatus, error?: string) => {
    setConnectionState(prev => ({
      ...prev,
      status,
      error,
      lastConnected: status === 'connected' ? new Date() : prev.lastConnected,
      lastDisconnected: status === 'disconnected' ? new Date() : prev.lastDisconnected
    }));
  }, []);
  
  // 处理消息接收
  const handleMessage = useCallback((message: WebSocketMessage) => {
    setLastMessage(message);
  
    // 添加到消息队列
    setMessageQueue(prev => [...prev, message]);
  
    // 限制队列长度
    if (messageQueue.length > 100) {
      setMessageQueue(prev => prev.slice(-100));
    }
  }, [messageQueue.length]);
  
  return {
    connectionState,
    lastMessage,
    messageQueue,
    updateConnectionStatus,
    handleMessage
  };
}
```

### 4.2 用户反馈机制

#### 4.2.1 连接状态指示器

```typescript
// 文件：web/src/components/WebSocketStatus.tsx
export function WebSocketStatus({
  isConnected,
  connectionStatus,
  isEnabled,
  connectionType,
  connect,
  disconnect
}: WebSocketStatusProps) {
  const { connectionState, reconnect } = useWebSocketByPage();
  
  const getStatusIcon = () => {
    switch (connectionState.status) {
      case 'connected':
        return <CheckCircleIcon className="w-4 h-4 text-green-500" />;
      case 'connecting':
        return <ClockIcon className="w-4 h-4 text-yellow-500 animate-spin" />;
      case 'reconnecting':
        return <ArrowPathIcon className="w-4 h-4 text-orange-500 animate-spin" />;
      case 'disconnected':
        return <XCircleIcon className="w-4 h-4 text-red-500" />;
      case 'error':
        return <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />;
      default:
        return <QuestionMarkCircleIcon className="w-4 h-4 text-gray-500" />;
    }
  };
  
  const getStatusText = () => {
    switch (connectionState.status) {
      case 'connected':
        return '实时连接正常';
      case 'connecting':
        return '正在连接...';
      case 'reconnecting':
        return `重连中... (${connectionState.reconnectAttempts}/15)`;
      case 'disconnected':
        return '连接已断开';
      case 'error':
        return `连接错误: ${connectionState.error}`;
      default:
        return '未知状态';
    }
  };
  
  return (
    <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded-lg">
      {getStatusIcon()}
      <span className="text-sm font-medium">{getStatusText()}</span>
  
      {connectionState.status === 'disconnected' && (
        <button
          onClick={reconnect}
          className="ml-2 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          重连
        </button>
      )}
  
      {connectionState.status === 'error' && (
        <button
          onClick={() => window.location.reload()}
          className="ml-2 px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
        >
          刷新页面
        </button>
      )}
    </div>
  );
}
```

#### 4.2.2 消息通知系统

```typescript
// 文件：web/src/components/MessageNotification.tsx
export function MessageNotification() {
  const { lastMessage } = useWebSocketByPage();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'text') {
      // 创建新通知
      const notification: Notification = {
        id: lastMessage.id,
        title: lastMessage.sender?.name || '新消息',
        content: lastMessage.data.content,
        timestamp: new Date(),
        type: 'message'
      };
    
      setNotifications(prev => [...prev, notification]);
    
      // 播放提示音
      playNotificationSound();
    
      // 显示桌面通知
      if (Notification.permission === 'granted') {
        new Notification(notification.title, {
          body: notification.content,
          icon: '/favicon.ico'
        });
      }
    
      // 自动移除通知（5秒后）
      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== notification.id));
      }, 5000);
    }
  }, [lastMessage]);
  
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map(notification => (
        <div
          key={notification.id}
          className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className="font-medium text-gray-900">{notification.title}</h4>
              <p className="text-sm text-gray-600 mt-1">{notification.content}</p>
              <p className="text-xs text-gray-400 mt-2">
                {notification.timestamp.toLocaleTimeString()}
              </p>
            </div>
            <button
              onClick={() => setNotifications(prev => prev.filter(n => n.id !== notification.id))}
              className="ml-2 text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## 🎓 第五部分：实战应用 - 聊天系统完整实现

### 5.1 聊天页面实现

#### 5.1.1 页面组件结构

```typescript
// 文件：web/src/app/chat/page.tsx
'use client';

import { useWebSocketByPage } from '@/hooks/useWebSocketByPage';
import { WebSocketStatus } from '@/components/WebSocketStatus';
import { MessageNotification } from '@/components/MessageNotification';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { MessageInput } from '@/components/chat/MessageInput';

export default function ChatPage() {
  const {
    isConnected,
    connectionStatus,
    lastMessage,
    sendMessage,
    config
  } = useWebSocketByPage();
  
  // 监听新消息
  useEffect(() => {
    if (lastMessage?.action === 'new_message') {
      console.log('收到新消息:', lastMessage.data);
      // 消息会自动添加到聊天窗口
    }
  }, [lastMessage]);
  
  // 发送消息
  const handleSendMessage = async (content: string, type: MessageType = 'text') => {
    if (!isConnected) {
      alert('WebSocket未连接，无法发送消息');
      return;
    }
  
    try {
      await sendMessage({
        action: 'send_message',
        data: {
          content,
          type,
          conversationId: 'current_conversation_id'
        }
      });
    } catch (error) {
      console.error('发送消息失败:', error);
      alert('发送消息失败，请重试');
    }
  };
  
  return (
    <div className="flex flex-col h-screen">
      {/* 状态栏 */}
      <div className="flex items-center justify-between p-4 border-b">
        <h1 className="text-xl font-semibold">聊天</h1>
        <WebSocketStatus />
      </div>
    
      {/* 聊天窗口 */}
      <div className="flex-1 overflow-hidden">
        <ChatWindow />
      </div>
    
      {/* 消息输入 */}
      <div className="p-4 border-t">
        <MessageInput onSendMessage={handleSendMessage} />
      </div>
    
      {/* 消息通知 */}
      <MessageNotification />
    </div>
  );
}
```

#### 5.1.2 聊天窗口组件

```typescript
// 文件：web/src/components/chat/ChatWindow.tsx
export function ChatWindow() {
  const { messageQueue } = useWebSocketByPage();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // 更新消息列表
  useEffect(() => {
    const chatMessages = messageQueue
      .filter(msg => msg.type === 'text' || msg.type === 'image' || msg.type === 'file')
      .map(msg => MessageAdapter.fromWebSocketMessage(msg));
  
    setMessages(chatMessages);
  }, [messageQueue]);
  
  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  return (
    <div className="flex flex-col h-full">
      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <ChatMessage key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>
    
      {/* 输入状态指示器 */}
      <TypingIndicator />
    </div>
  );
}
```

### 5.2 消息输入组件

#### 5.2.1 基础输入功能

```typescript
// 文件：web/src/components/chat/MessageInput.tsx
export function MessageInput({ onSendMessage }: { onSendMessage: (content: string, type: MessageType) => void }) {
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const { sendMessage } = useWebSocketByPage();
  
  // 发送文本消息
  const handleSendText = async () => {
    if (!inputValue.trim()) return;
  
    try {
      await onSendMessage(inputValue.trim(), 'text');
      setInputValue('');
      setIsTyping(false);
    
      // 发送停止输入状态
      await sendMessage({
        action: 'typing_status',
        data: { isTyping: false }
      });
    } catch (error) {
      console.error('发送消息失败:', error);
    }
  };
  
  // 处理输入状态
  const handleInputChange = async (value: string) => {
    setInputValue(value);
  
    // 发送输入状态
    if (!isTyping && value.trim()) {
      setIsTyping(true);
      await sendMessage({
        action: 'typing_status',
        data: { isTyping: true }
      });
    } else if (isTyping && !value.trim()) {
      setIsTyping(false);
      await sendMessage({
        action: 'typing_status',
        data: { isTyping: false }
      });
    }
  };
  
  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  };
  
  return (
    <div className="flex items-end space-x-2">
      <div className="flex-1">
        <textarea
          value={inputValue}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="输入消息..."
          className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows={1}
        />
      </div>
    
      <button
        onClick={handleSendText}
        disabled={!inputValue.trim()}
        className="px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        发送
      </button>
    </div>
  );
}
```

#### 5.2.2 文件上传功能

```typescript
// 文件：web/src/components/chat/MessageInput.tsx
export function MessageInput({ onSendMessage }: { onSendMessage: (content: string, type: MessageType) => void }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { sendMessage } = useWebSocketByPage();
  
  // 处理文件上传
  const handleFileUpload = async (file: File) => {
    try {
      // 上传文件到服务器
      const formData = new FormData();
      formData.append('file', file);
    
      const response = await fetch('/api/v1/files/upload', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });
    
      if (!response.ok) {
        throw new Error('文件上传失败');
      }
    
      const result = await response.json();
    
      // 发送文件消息
      await sendMessage({
        action: 'send_message',
        data: {
          content: result.url,
          type: getFileType(file.type),
          fileName: file.name,
          fileSize: file.size
        }
      });
    
    } catch (error) {
      console.error('文件上传失败:', error);
      alert('文件上传失败，请重试');
    }
  };
  
  // 获取文件类型
  const getFileType = (mimeType: string): MessageType => {
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType.startsWith('audio/')) return 'audio';
    return 'file';
  };
  
  return (
    <div className="flex items-end space-x-2">
      {/* 文件上传按钮 */}
      <button
        onClick={() => fileInputRef.current?.click()}
        className="p-3 text-gray-500 hover:text-gray-700"
      >
        <PaperClipIcon className="w-5 h-5" />
      </button>
    
      <input
        ref={fileInputRef}
        type="file"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            handleFileUpload(file);
          }
        }}
        className="hidden"
        accept="image/*,audio/*,video/*,.pdf,.doc,.docx,.txt"
      />
    
      {/* 文本输入框 */}
      <div className="flex-1">
        <textarea
          value={inputValue}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="输入消息..."
          className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows={1}
        />
      </div>
    
      <button
        onClick={handleSendText}
        disabled={!inputValue.trim()}
        className="px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        发送
      </button>
    </div>
  );
}
```

---

## 🎓 第六部分：性能优化 - 连接复用与资源管理

### 6.1 连接复用策略

#### 6.1.1 单例连接管理

```typescript
// 文件：web/src/service/websocket/index.ts
class WebSocketManager {
  private static instance: WebSocketManager;
  private connection: WebSocketConnection | null = null;
  private subscribers: Set<(message: WebSocketMessage) => void> = new Set();
  
  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }
  
  async connect(config: WebSocketConfig): Promise<void> {
    if (this.connection && this.connection.isConnected()) {
      return; // 已连接，直接返回
    }
  
    this.connection = new WebSocketConnection();
    await this.connection.connect(config.url);
  
    // 设置消息处理器
    this.connection.onMessage = (message) => {
      this.notifySubscribers(message);
    };
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
  
  disconnect(): void {
    if (this.connection) {
      this.connection.disconnect();
      this.connection = null;
    }
  }
}

export const wsManager = WebSocketManager.getInstance();
```

#### 6.1.2 消息队列优化

```typescript
// 文件：web/src/service/websocket/core/messageQueue.ts
export class MessageQueue {
  private queue: WebSocketMessage[] = [];
  private maxSize: number = 100;
  private processing: boolean = false;
  
  add(message: WebSocketMessage): void {
    this.queue.push(message);
  
    // 限制队列大小
    if (this.queue.length > this.maxSize) {
      this.queue = this.queue.slice(-this.maxSize);
    }
  
    // 异步处理消息
    if (!this.processing) {
      this.processQueue();
    }
  }
  
  private async processQueue(): Promise<void> {
    if (this.processing || this.queue.length === 0) {
      return;
    }
  
    this.processing = true;
  
    while (this.queue.length > 0) {
      const message = this.queue.shift()!;
    
      try {
        await this.processMessage(message);
      } catch (error) {
        console.error('处理消息失败:', error);
      }
    
      // 添加小延迟避免阻塞
      await new Promise(resolve => setTimeout(resolve, 10));
    }
  
    this.processing = false;
  }
  
  private async processMessage(message: WebSocketMessage): Promise<void> {
    // 根据消息类型分发到不同的处理器
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
  }
  
  private async handleTextMessage(message: WebSocketMessage): Promise<void> {
    // 处理文本消息
    console.log('处理文本消息:', message.data.content);
  }
  
  private async handleImageMessage(message: WebSocketMessage): Promise<void> {
    // 处理图片消息
    console.log('处理图片消息:', message.data.url);
  }
  
  private async handleFileMessage(message: WebSocketMessage): Promise<void> {
    // 处理文件消息
    console.log('处理文件消息:', message.data.fileName);
  }
  
  private async handleSystemMessage(message: WebSocketMessage): Promise<void> {
    // 处理系统消息
    console.log('处理系统消息:', message.data.message);
  }
}
```

### 6.2 资源管理

#### 6.2.1 内存泄漏防护

```typescript
// 文件：web/src/hooks/useWebSocketByPage.ts
export function useWebSocketByPage() {
  const [state, setState] = useState<WebSocketState>(initialState);
  const mountedRef = useRef(true);
  
  // 组件卸载时清理
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      // 清理订阅
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, []);
  
  // 安全的状态更新
  const safeSetState = useCallback((updater: (prev: WebSocketState) => WebSocketState) => {
    if (mountedRef.current) {
      setState(updater);
    }
  }, []);
  
  // 订阅WebSocket消息
  useEffect(() => {
    const unsubscribe = wsManager.subscribe((message) => {
      if (mountedRef.current) {
        safeSetState(prev => ({
          ...prev,
          lastMessage: message,
          messageQueue: [...prev.messageQueue, message].slice(-100)
        }));
      }
    });
  
    unsubscribeRef.current = unsubscribe;
  
    return unsubscribe;
  }, [safeSetState]);
  
  return state;
}
```

#### 6.2.2 错误边界处理

```typescript
// 文件：web/src/components/WebSocketErrorBoundary.tsx
export class WebSocketErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('WebSocket错误:', error, errorInfo);
  
    // 发送错误报告
    this.reportError(error, errorInfo);
  }
  
  private reportError(error: Error, errorInfo: React.ErrorInfo) {
    // 发送错误到服务器
    fetch('/api/v1/errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString()
      })
    }).catch(console.error);
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-red-800 font-medium">WebSocket连接错误</h3>
          <p className="text-red-600 text-sm mt-1">
            {this.state.error?.message || '未知错误'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
          >
            刷新页面
          </button>
        </div>
      );
    }
  
    return this.props.children;
  }
}
```

---

## 🎯 总结与最佳实践

### 核心要点回顾

1. **页面级连接管理**：根据页面需求智能管理WebSocket连接
2. **事件驱动架构**：使用消息处理器和适配器处理不同类型的消息
3. **状态管理**：实时反馈连接状态和消息处理结果
4. **性能优化**：实现连接复用和消息队列
5. **错误处理**：完善的错误边界和恢复机制

### 最佳实践

#### ✅ 推荐做法

- **连接管理**：使用页面级配置，避免不必要的连接
- **消息处理**：使用事件处理器模式，保持代码模块化
- **状态反馈**：提供清晰的连接状态和错误信息
- **性能优化**：实现连接复用和消息队列
- **错误处理**：使用错误边界和自动重连机制

#### ❌ 避免做法

- **全局连接**：在所有页面都建立WebSocket连接
- **阻塞处理**：在主线程中处理大量消息
- **内存泄漏**：不清理事件监听器和定时器
- **错误忽略**：不处理连接错误和消息处理异常

### 扩展学习

1. **WebRTC**：点对点通信技术
2. **Server-Sent Events (SSE)**：服务器推送事件
3. **GraphQL Subscriptions**：GraphQL实时订阅
4. **Socket.IO**：更高级的WebSocket库
5. **消息队列**：RabbitMQ、Redis Streams等

---

**课程版本**：WebSocket前端实战 V1.0
**适用对象**：前端开发者、全栈开发者
**前置知识**：JavaScript/TypeScript基础、React基础
**学习时长**：4-6小时
**实践项目**：聊天系统、实时通知系统
