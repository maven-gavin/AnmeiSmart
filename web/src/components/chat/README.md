# WebSocket 新架构使用指南

## 概述

新的WebSocket架构采用全局连接模式，通过React Context提供统一的状态管理和消息分发。

## 核心原则

1. **全局唯一连接**：应用启动时建立唯一的WebSocket连接
2. **事件驱动**：组件通过监听 `lastJsonMessage`来消费实时事件
3. **自动过滤**：组件根据消息中的 `conversationId`过滤相关消息

## 使用方式

### 1. 在聊天组件中使用

```tsx
'use client';

import { useWebSocket } from '@/contexts/WebSocketContext';
import { useEffect, useState } from 'react';

function ChatWindow({ conversationId }: { conversationId: string }) {
  const { lastJsonMessage, isConnected } = useWebSocket();
  const [messages, setMessages] = useState<any[]>([]);

  // 监听新消息事件
  useEffect(() => {
    if (lastJsonMessage?.action === 'new_message') {
      const data = lastJsonMessage.data;
    
      // 只处理当前会话的消息
      if (data.conversation_id === conversationId) {
        console.log('收到当前会话的新消息:', data);
        setMessages(prev => [...prev, data]);
      }
    }
  }, [lastJsonMessage, conversationId]);

  // 监听在线状态更新
  useEffect(() => {
    if (lastJsonMessage?.action === 'presence_update') {
      const data = lastJsonMessage.data;
      console.log('用户在线状态更新:', data);
      // 更新用户在线状态显示
    }
  }, [lastJsonMessage]);

  return (
    <div>
      <div>连接状态: {isConnected ? '已连接' : '未连接'}</div>
      <div>
        {messages.map(msg => (
          <div key={msg.id}>{msg.content}</div>
        ))}
      </div>
    </div>
  );
}
```

### 2. 在顾问界面中监听客户消息

```tsx
'use client';

import { useWebSocket } from '@/contexts/WebSocketContext';
import { useEffect } from 'react';

function ConsultantDashboard() {
  const { lastJsonMessage } = useWebSocket();

  // 监听所有客户的新消息
  useEffect(() => {
    if (lastJsonMessage?.action === 'new_message') {
      const data = lastJsonMessage.data;
    
      // 如果是客户发送的消息，显示通知
      if (data.sender_type === 'customer') {
        console.log('收到客户消息:', data);
        // 显示新消息通知
        showNotification(`客户 ${data.sender_name} 发送了新消息`);
      }
    }
  }, [lastJsonMessage]);

  return (
    <div>
      {/* 顾问界面内容 */}
    </div>
  );
}
```

### 3. 监听多种事件类型

```tsx
'use client';

import { useWebSocket } from '@/contexts/WebSocketContext';
import { useEffect } from 'react';

function RealtimeComponent() {
  const { lastJsonMessage } = useWebSocket();

  useEffect(() => {
    if (!lastJsonMessage) return;

    switch (lastJsonMessage.action) {
      case 'new_message':
        handleNewMessage(lastJsonMessage.data);
        break;
    
      case 'presence_update':
        handlePresenceUpdate(lastJsonMessage.data);
        break;
    
      case 'typing_update':
        handleTypingUpdate(lastJsonMessage.data);
        break;
    
      default:
        console.log('未处理的WebSocket事件:', lastJsonMessage);
    }
  }, [lastJsonMessage]);

  const handleNewMessage = (data: any) => {
    // 处理新消息
  };

  const handlePresenceUpdate = (data: any) => {
    // 处理在线状态更新
  };

  const handleTypingUpdate = (data: any) => {
    // 处理输入状态更新
  };

  return <div>实时组件</div>;
}
```

## 事件格式

### 新消息事件

```json
{
  "action": "new_message",
  "data": {
    "id": "msg_123",
    "conversation_id": "conv_456",
    "content": "消息内容",
    "sender_type": "customer",
    "sender_name": "张三",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

### 在线状态事件

```json
{
  "action": "presence_update", 
  "data": {
    "user_id": "user_123",
    "status": "online",
    "last_seen": "2024-01-01T12:00:00Z"
  }
}
```

## 注意事项

1. **消息过滤**：组件必须根据 `conversationId`过滤消息，避免处理无关消息
2. **性能优化**：避免在 `useEffect`中进行复杂计算，使用 `useMemo`缓存处理结果
3. **错误处理**：始终检查 `lastJsonMessage`的结构，避免访问不存在的属性
4. **清理副作用**：组件卸载时清理相关状态和订阅

## 迁移指南

### 从旧Hook迁移

**旧代码**：

```tsx
// ❌ 旧架构 - 已删除
import { useChatWebSocket } from '@/hooks/useChatWebSocket';

function ChatComponent({ conversationId }) {
  const { wsStatus, setupMessageListener } = useChatWebSocket(userId, conversationId);
  // ...
}
```

**新代码**：

```tsx
// ✅ 新架构
import { useWebSocket } from '@/contexts/WebSocketContext';

function ChatComponent({ conversationId }) {
  const { isConnected, lastJsonMessage } = useWebSocket();
  
  useEffect(() => {
    if (lastJsonMessage?.action === 'new_message' && 
        lastJsonMessage.data.conversation_id === conversationId) {
      // 处理消息
    }
  }, [lastJsonMessage, conversationId]);
}
```

## 架构优势

1. **简化代码**：不再需要管理多个WebSocket连接
2. **性能优化**：全局单一连接，减少资源消耗
3. **状态统一**：全局状态管理，避免状态不一致
4. **易于扩展**：新的事件类型只需在组件中添加处理逻辑
