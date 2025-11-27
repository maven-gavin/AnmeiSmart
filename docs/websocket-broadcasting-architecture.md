# WebSocket 广播服务架构指南

> **状态：已完全部署** ✅

## 概述

AnmeiSmart系统采用了基于**页面级管理**和**智能广播**的WebSocket架构，实现了高效的实时通信和消息推送解决方案。架构包含两个核心组件：

1. **WebSocket 架构 V2**：基于"按需连接"和"页面级管理"的前端实时通信
2. **BroadcastingService**：统一的消息广播和离线推送服务

## 项目文件结构

### 前端文件结构（web/）

```
web/src/
├── hooks/
│   └── useWebSocketByPage.ts              # 页面级WebSocket Hook
├── components/
│   └── WebSocketStatus.tsx                # WebSocket状态指示器组件
├── service/
│   ├── websocket/
│   │   ├── index.ts                       # WebSocket客户端主入口
│   │   ├── types.ts                       # TypeScript类型定义
│   │   ├── core/
│   │   │   ├── connection.ts              # WebSocket连接管理
│   │   │   ├── heartbeat.ts               # 心跳机制
│   │   │   ├── reconnect.ts               # 重连逻辑
│   │   │   ├── serializer.ts              # 消息序列化
│   │   │   └── messageQueue.ts            # 消息队列
│   │   ├── adapters/
│   │   │   └── messageAdapter.ts          # 消息适配器
│   │   └── handlers/
│   │       ├── index.ts                   # 处理器注册中心
│   │       └── messageEventHandler.ts     # 消息事件处理器
│   ├── chat/
│   │   ├── api.ts                         # 聊天API服务
│   │   ├── state.ts                       # 聊天状态管理
│   │   └── types.ts                       # 聊天相关类型定义
│   ├── authService.ts                     # 认证服务
│   └── utils.ts                          # 设备检测和配置工具
└── app/
    ├── test-websocket/
    │   └── page.tsx                       # WebSocket测试页面
    └── [各业务页面...]
```

### 后端文件结构（api/）

```
api/app/
├── services/
│   ├── broadcasting_service.py            # 主要广播服务
│   ├── broadcasting_factory.py            # 广播服务工厂和依赖注入
│   ├── notification_service.py            # 通知推送服务
│   └── websocket/
│       ├── __init__.py                    # 服务包初始化
│       ├── websocket_handler.py           # 消息处理器
│       ├── websocket_service.py           # 统一WebSocket服务
│       └── websocket_factory.py           # WebSocket服务工厂
├── core/
│   ├── distributed_connection_manager.py  # 分布式连接管理器
│   ├── redis_client.py                   # Redis客户端
│   ├── events.py                         # 事件系统
│   └── websocket_lifecycle.py            # 生命周期管理
├── api/
│   ├── deps.py                           # FastAPI依赖注入
│   └── v1/
│       └── endpoints/
│           └── websocket.py              # WebSocket端点
├── db/
│   └── models/
│       ├── chat.py                       # 聊天相关模型
│       └── user.py                       # 用户模型
├── schemas/
│   └── chat.py                           # 聊天相关Schema
└── utils/
    └── websocket_utils.py                # 公共工具函数
```

### 核心文件说明

#### 前端核心文件

| 文件                             | 作用                  | 说明                              |
| -------------------------------- | --------------------- | --------------------------------- |
| `useWebSocketByPage.ts`        | 页面级WebSocket管理   | 根据页面配置智能管理WebSocket连接 |
| `WebSocketStatus.tsx`          | 连接状态UI组件        | 显示WebSocket连接状态和控制按钮   |
| `websocket/index.ts`           | WebSocket客户端主入口 | 提供统一的WebSocket客户端接口     |
| `websocket/core/connection.ts` | 连接管理              | 处理WebSocket连接的建立和维护     |
| `websocket/core/reconnect.ts`  | 重连机制              | 实现智能重连和指数退避策略        |
| `chat/api.ts`                   | 聊天API服务          | 提供与后端通信的接口             |
| `chat/state.ts`                 | 聊天状态管理          | 管理聊天相关的全局状态           |

#### 后端核心文件

| 文件                                  | 作用            | 说明                               |
| ------------------------------------- | --------------- | ---------------------------------- |
| `broadcasting_service.py`           | 主要广播服务    | 处理消息广播和离线推送的核心逻辑   |
| `broadcasting_factory.py`           | 服务工厂        | 管理广播服务的创建和依赖注入       |
| `distributed_connection_manager.py` | 分布式连接管理  | 基于Redis的跨实例WebSocket连接管理 |
| `notification_service.py`           | 通知推送服务    | 处理离线推送通知（支持多种提供商） |
| `websocket/websocket_service.py`    | 统一WebSocket服务 | 整合连接管理和消息广播的统一接口   |
| `websocket/websocket_factory.py`    | WebSocket服务工厂 | 统一管理WebSocket服务的创建和依赖注入 |
| `websocket/websocket_handler.py`    | 消息处理器      | 处理WebSocket消息的解析和路由      |
| `websocket_lifecycle.py`            | 生命周期管理    | 处理应用启动和关闭时的服务初始化和清理 |
| `websocket_utils.py`                | 公共工具函数    | 提供WebSocket相关的公共工具函数    |

## 架构组件

### 1. 前端 WebSocket 架构 V2

#### 核心设计原则

- **页面配置驱动**：每个页面的WebSocket需求通过配置文件定义
- **智能生命周期管理**：页面加载 → 配置检查 → 认证验证 → 条件连接
- **功能特性按需加载**：不同页面启用不同的WebSocket功能

#### 页面配置示例

```typescript
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
  }
}
```

#### 功能特性分布

| 页面类型 | 消息传递 | 输入指示器 | 文件上传 | 系统监控 |
| -------- | -------- | ---------- | -------- | -------- |
| 医生聊天 | ✅       | ✅         | ✅       | ❌       |
| 客户聊天 | ✅       | ✅         | ✅       | ❌       |
| 顾问聊天 | ✅       | ✅         | ✅       | ❌       |
| 管理页面 | ❌       | ❌         | ❌       | ✅       |

#### 统一设备配置

所有设备类型使用统一的WebSocket配置，不再区分设备类型：

```typescript
export function getWebSocketDeviceConfig(deviceInfo: DeviceInfo) {
  return {
    connectionTimeout: 20000,    // 20秒连接超时
    heartbeatInterval: 45000,    // 45秒心跳间隔
    reconnectInterval: 2000,     // 2秒重连间隔
    maxReconnectDelay: 30000     // 最大重连延迟30秒
  };
}
```

### 2. 后端广播服务架构

#### 核心组件

- **BroadcastingService**：主要广播服务，处理实时推送和离线通知
- **DistributedConnectionManager**：分布式WebSocket连接管理器（基于Redis）
- **NotificationService**：通知推送服务（当前使用日志记录，支持扩展）

#### 服务依赖关系

```
BroadcastingService
├── DistributedConnectionManager (Redis Pub/Sub)
├── NotificationService (日志记录/Firebase FCM)
└── Database Session (查询会话参与者)
```

### 文件依赖关系图

#### 前端依赖关系

```
页面组件 (page.tsx)
├── useWebSocketByPage.ts
│   ├── WebSocketStatus.tsx
│   └── chat/api.ts
│       └── websocket/index.ts (WebSocketClient)
│           ├── core/connection.ts
│           ├── core/heartbeat.ts
│           ├── core/reconnect.ts
│           ├── core/serializer.ts
│           ├── core/messageQueue.ts
│           ├── adapters/messageAdapter.ts
│           └── handlers/messageEventHandler.ts
├── authService.ts
└── utils.ts (设备检测)
```

#### 后端依赖关系

```
HTTP API 端点
├── broadcasting_factory.py
│   └── broadcasting_service.py
│       ├── distributed_connection_manager.py
│       │   └── redis_client.py
│       ├── notification_service.py
│       └── db/models/chat.py
├── websocket/message_broadcaster.py
│   └── core/events.py
└── api/deps.py (依赖注入)
```

## 使用指南

### 1. 前端页面中使用 WebSocket

```tsx
'use client';

import { useWebSocketByPage } from '@/hooks/useWebSocketByPage';
import { WebSocketStatus } from '@/components/WebSocketStatus';

function ChatPage() {
  const {
    isConnected,
    connectionStatus,
    isEnabled,
    connectionType,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
    config
  } = useWebSocketByPage();

  // 监听消息
  useEffect(() => {
    if (lastMessage?.action === 'new_message') {
      console.log('收到消息:', lastMessage.data);
    }
  }, [lastMessage]);

  return (
    <div>
      <WebSocketStatus 
        isConnected={isConnected}
        connectionStatus={connectionStatus}
        isEnabled={isEnabled}
        connectionType={connectionType}
        connect={connect}
        disconnect={disconnect}
      />
      <div>
        连接状态: {isConnected ? '已连接' : '未连接'}
        {isEnabled && (
          <div>功能特性: {config?.features?.join(', ')}</div>
        )}
      </div>
    </div>
  );
}
```

### 2. 后端广播服务使用

#### 创建服务实例

```python
from app.services.broadcasting_factory import create_broadcasting_service
from app.api.deps import get_db

# 创建服务实例
db = next(get_db())
broadcasting_service = await create_broadcasting_service(db=db)
```

#### 基本消息广播

```python
# 广播聊天消息
await broadcasting_service.broadcast_message(
    conversation_id="conv_123",
    message_data={
        "id": "msg_456",
        "content": "你好，有什么可以帮助您的吗？",
        "sender_id": "consultant_789",
        "message_type": "text"
    },
    exclude_user_id="consultant_789"  # 排除发送者
)
```

#### 顾问回复消息（优化推送策略）

```python
# 在线用户实时推送，离线用户推送通知
await broadcasting_service.broadcast_message(
    conversation_id="conv_123",
    message_data={
        "id": "msg_789",
        "content": "根据您的需求，我推荐以下方案...",
        "sender_id": "consultant_789",
        "sender_type": "consultant",
        "sender_name": "张医生",
        "message_type": "text",
        "is_important": True,
        "extra_metadata": {
            "reply_type": "consultation",
            "consultant_name": "张医生"
        }
    },
    exclude_user_id="consultant_789"  # 排除发送者
)
```

#### 移动端专用通知

```python
# 重要消息推送到所有设备，移动端会收到推送通知
await broadcasting_service.send_direct_message(
    user_id="customer_456",
    message_data={
        "title": "预约提醒",
        "content": "您的预约将在30分钟后开始",
        "type": "appointment_reminder",
        "action": "open_appointment",
        "conversation_id": "conv_123"
    }
)
```

#### 状态广播

```python
# 用户正在输入
await broadcasting_service.broadcast_typing_status(
    conversation_id="conv_123",
    user_id="customer_456",
    is_typing=True
)

# 消息已读状态
await broadcasting_service.broadcast_read_status(
    conversation_id="conv_123",
    user_id="customer_456",
    message_ids=["msg_001", "msg_002", "msg_003"]
)
```

#### 系统通知

```python
# 系统通知广播
await broadcasting_service.broadcast_system_notification(
    conversation_id="conv_123",
    notification_data={
        "title": "系统维护通知",
        "message": "系统将在今晚23:00-01:00进行维护",
        "type": "maintenance"
    }
)
```

#### 直接消息发送

```python
# 向特定用户发送直接消息
await broadcasting_service.send_direct_message(
    user_id="customer_456",
    message_data={
        "title": "个人通知",
        "content": "您的会员等级已升级",
        "type": "membership_upgrade"
    }
)
```

### 3. 在HTTP API中使用依赖注入

```python
from fastapi import APIRouter, Depends
from app.services.broadcasting_factory import get_broadcasting_service_dependency
from app.api.deps import get_db

router = APIRouter()

@router.post("/chat/{conversation_id}/send")
async def send_message(
    conversation_id: str,
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    # 获取广播服务实例（每次创建新实例以支持不同的数据库会话）
    broadcasting_service = await get_broadcasting_service_dependency(db)
  
    # 保存消息到数据库
    saved_message = await save_message_to_db(conversation_id, message)
  
    # 广播消息
    await broadcasting_service.broadcast_message(
        conversation_id=conversation_id,
        message_data=saved_message.dict(),
        exclude_user_id=message.sender_id
    )
  
    return {"status": "sent", "message_id": saved_message.id}
```

### 4. 设备信息查询

```python
# 获取用户的设备连接信息
devices = await broadcasting_service.get_user_device_info("customer_456")
print(f"用户设备: {devices}")
# 输出: [
#   {"connection_id": "xxx", "device_type": "mobile", "connected_at": "..."},
#   {"connection_id": "yyy", "device_type": "desktop", "connected_at": "..."}
# ]
```

## 架构优势

### 性能提升

- **前端**：减少70%无效WebSocket连接，登录页面零连接尝试
- **后端**：Redis分布式架构支持水平扩展，智能推送策略减少无效通知

### 维护性提升

- **前端**：页面级状态隔离，配置驱动的连接管理
- **后端**：模块化设计，支持不同推送服务提供商

### 用户体验提升

- 消除登录页面连接错误
- 更快的页面加载速度
- 精确的连接状态反馈
- 智能的离线推送策略

## 推送通知系统

### 当前实现（日志记录服务）

推送通知将在日志中显示：

```
INFO  📱 推送通知 [mobile] [优先级: high]: customer_456
INFO     标题: 顾问回复
INFO     内容: 根据您的需求，我推荐以下方案...
INFO     [数据: {'conversation_id': 'conv_123', 'action': 'open_conversation'}]

DEBUG 移动端推送通知已排队: user_id=customer_456
INFO  顾问回复广播完成: conversation_id=conv_123, consultant_id=consultant_789
```

### 未来扩展

当需要集成真实推送服务时，只需：

1. 更新环境变量：`NOTIFICATION_PROVIDER=firebase`
2. 添加推送服务配置
3. 实现对应的NotificationProvider
4. 业务代码无需任何修改

支持的推送服务：

- Firebase FCM（待实现）
- Apple APNs（待实现）
- 第三方推送服务（极光推送、友盟等）

## 分布式连接管理

### Redis 架构

- **在线状态管理**：`ws:online_users` Set存储在线用户
- **消息广播**：`ws:broadcast` Channel进行跨实例消息传递
- **状态同步**：`ws:presence` Channel同步用户上下线状态

#### ⚠️ Redis Pub/Sub 重要特性

**关键发现**：Redis Pub/Sub 有一个重要特性：**发布者不会收到自己发布的消息**。

这意味着：
- 如果消息发布到Redis，只有**其他实例**的监听器会收到
- **当前实例**的监听器不会收到自己发布的消息
- 如果目标用户在当前实例有连接，消息会丢失

**解决方案**：在 `DistributedConnectionManager.send_to_user()` 中实现智能路由：
1. **先检查本地连接**：如果目标用户在当前实例有连接，直接发送到本地WebSocket（不经过Redis）
2. **否则通过Redis广播**：如果用户在其他实例，通过Redis广播，其他实例的监听器会接收并发送

```python
async def send_to_user(self, user_id: str, payload: dict):
    """向指定用户发送消息"""
    # Redis Pub/Sub的特性：发布者不会收到自己发布的消息
    # 所以如果用户在当前实例有连接，直接发送；否则通过Redis广播
    is_locally_connected = self.connection_manager.is_user_connected(user_id)
    
    if is_locally_connected:
        # 直接发送到本地连接
        await self._send_to_local_user(user_id, payload)
    else:
        # 通过Redis广播（其他实例的监听器会收到）
        await self.message_router.send_to_user(user_id, payload)
```

### 多设备支持

- 按用户ID组织连接（兼容现有逻辑）
- 按连接ID组织连接（支持多设备区分）
- 设备类型路由（mobile、desktop、tablet）

## 最佳实践

### ✅ 推荐做法

- **前端**：使用页面级连接管理，配置驱动的WebSocket需求定义
- **后端**：
  - 复用数据库会话，使用依赖注入管理服务实例
  - **消息发送优先本地**：如果目标用户在当前实例有连接，直接发送，避免Redis Pub/Sub的局限性
  - **统一连接管理器实例**：确保 `broadcasting_factory` 和 `websocket_factory` 使用同一个 `DistributedConnectionManager` 实例
  - **在线状态检查优化**：先检查本地连接（更可靠），再检查Redis状态
- **推送**：合理使用设备类型过滤，减少不必要的推送
- **错误处理**：提供清晰的连接状态反馈和错误恢复机制

### ❌ 避免做法

- **前端**：手动管理全局连接，在不需要的页面开启WebSocket
- **后端**：
  - 频繁创建广播服务实例，忽视数据库会话管理
  - **避免**：总是通过Redis发送消息，忽略本地连接检查（会导致消息丢失）
  - **避免**：创建多个 `DistributedConnectionManager` 实例（会导致监听器不一致）
  - **避免**：只依赖Redis检查在线状态（可能存在同步延迟）
- **通用**：忽视错误处理，频繁连接断开

## 监控和调试

### 关键日志级别

- `INFO`：推送通知记录、广播完成状态、连接建立/断开
- `DEBUG`：设备连接详情、消息路由信息、本地消息发送
- `WARNING`：推送失败、配置问题、连接异常
- `ERROR`：服务异常、连接错误、Redis通信失败

### 性能指标

通过日志可以监控：

- 消息广播响应时间
- 在线用户数量和分布
- 推送成功率
- 设备连接分布
- Redis发布订阅性能

### 关键日志追踪

系统提供了详细的日志追踪机制，帮助快速定位问题：

#### 后端日志标签

- `[广播]`：消息广播流程（开始、参与者列表、发送统计）
- `[参与者]`：参与者列表获取过程
- `[发送]`：用户在线状态检查、消息发送成功/失败
- `[路由]`：Redis消息发布和路由决策
- `[监听器]`：Redis监听器接收和处理消息
- `[广播处理]`：接收到的广播消息处理
- `[本地发送]`：本地连接检查和发送结果
- `[本地连接]`：WebSocket实际发送到连接的日志
- `[在线状态]`：在线状态检查和管理

#### 前端日志标签

- `[WebSocket]`：原始消息和适配后消息
- `[MessageEventHandler]`：事件处理过程
- `[useWebSocketByPage]`：回调触发和消息设置
- `[page.tsx]`：消息添加到列表的过程

#### 故障排查流程

1. **消息未实时显示**
   - 检查后端 `[广播]` 日志，确认消息是否开始广播
   - 检查 `[发送]` 日志，确认用户在线状态
   - 检查 `[路由]` 日志，确认是否通过Redis或本地发送
   - 检查前端 `[WebSocket]` 日志，确认是否收到消息
   - 检查 `[MessageEventHandler]` 日志，确认事件是否被处理

2. **在线状态不准确**
   - 检查 `[在线状态]` 日志，查看本地连接和Redis状态
   - 确认连接建立时是否调用了 `add_user_to_online`
   - 检查是否有多个连接管理器实例

3. **Redis消息丢失**
   - 确认是否因为Redis Pub/Sub特性导致（发布者收不到自己的消息）
   - 检查是否实现了本地优先发送策略

## 配置文件和环境变量

### 前端配置

#### 环境变量 (.env.local)

```bash
# WebSocket服务URL配置
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# 开发模式配置
NODE_ENV=development
```

#### 主要配置文件

- `web/src/hooks/useWebSocketByPage.ts`: 页面WebSocket配置
- `web/src/service/websocket/index.ts`: WebSocket客户端配置
- `web/src/service/utils.ts`: 设备检测和配置

### 后端配置

#### 环境变量 (.env)

```bash
# Redis配置
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# 通知服务配置
NOTIFICATION_PROVIDER=logging  # logging | firebase

# Firebase配置（可选）
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/dbname

# WebSocket配置
WS_HEARTBEAT_INTERVAL=45000
WS_CONNECTION_TIMEOUT=20000
WS_MAX_RECONNECT_ATTEMPTS=15
```

#### 主要配置文件

- `api/app/core/config.py`: 应用主配置
- `api/app/core/redis_client.py`: Redis连接配置
- `api/app/services/notification_service.py`: 通知服务配置
- `api/alembic.ini`: 数据库迁移配置

## 部署架构

### 开发环境

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js App  │    │   FastAPI App   │    │   Redis Server  │
│   (Port 3000)  │◄──►│   (Port 8000)   │◄──►│   (Port 6379)   │
│                 │    │                 │    │                 │
│  WebSocket      │    │  WebSocket      │    │  Pub/Sub        │
│  Client         │    │  Server         │    │  Connection     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 生产环境

```
┌────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load         │    │   FastAPI       │    │   Redis         │
│   Balancer     │    │   Instances     │    │   (多实例)       │
│   (Nginx)      │    │   (主从复制)     │    │                 │
└────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket    │    │   分布式连接     │    │   消息队列      │
│   连接池       │    │   管理器        │    │   持久化        │
└────────────────┘    └─────────────────┘    └─────────────────┘
```

## 为新页面添加 WebSocket 支持

1. **配置页面**：在 `useWebSocketByPage.ts` 中的 `PAGE_WEBSOCKET_CONFIG` 添加页面配置
2. **使用 Hook**：在页面组件中使用 `useWebSocketByPage()`
3. **添加状态指示器**：使用 `<WebSocketStatus />` 组件
4. **注册消息处理**：根据页面功能特性处理相应的WebSocket消息

## 错误处理和恢复

### 前端错误处理

- 自动重连机制（最多15次重连）
- 指数退避重连策略
- 连接状态实时反馈
- 页面级错误隔离

### 后端错误处理

服务内置了完善的错误处理机制：

```python
try:
    await broadcasting_service.broadcast_message(conversation_id, message_data)
except Exception as e:
    logger.error(f"消息广播失败: {e}")
    # 服务内部会自动记录错误并继续运行
```

## 重要修复经验

### 1. Redis Pub/Sub 消息路由优化（2025-11-27）

**问题**：用户发送消息后，接收方无法实时收到，需要刷新页面才能看到。

**根本原因**：
- Redis Pub/Sub 的特性：发布者不会收到自己发布的消息
- 如果目标用户在当前实例有连接，消息通过Redis发布后，当前实例的监听器收不到
- 导致消息丢失，用户无法实时看到

**解决方案**：
- 在 `DistributedConnectionManager.send_to_user()` 中实现智能路由
- 先检查用户是否在当前实例有连接
- 如果有，直接发送到本地WebSocket连接（不经过Redis）
- 如果没有，通过Redis广播（其他实例的监听器会接收）

**关键代码**：
```python
async def send_to_user(self, user_id: str, payload: dict):
    is_locally_connected = self.connection_manager.is_user_connected(user_id)
    
    if is_locally_connected:
        # 直接发送到本地连接
        await self._send_to_local_user(user_id, payload)
    else:
        # 通过Redis广播
        await self.message_router.send_to_user(user_id, payload)
```

### 2. 在线状态检查优化（2025-11-27）

**问题**：在线状态检查不准确，导致消息被误判为离线推送。

**解决方案**：
- 先检查本地连接（更可靠）
- 如果本地有连接但Redis显示离线，自动更新Redis状态
- 返回本地连接或Redis在线的结果

**关键代码**：
```python
async def is_user_online(self, user_id: str) -> bool:
    # 先检查本地连接（更可靠）
    is_locally_connected = self.connection_manager.is_user_connected(user_id)
    is_redis_online = await self.presence_manager.is_user_online(user_id)
    
    # 如果本地有连接但Redis显示离线，更新Redis状态
    if is_locally_connected and not is_redis_online:
        await self.presence_manager.add_user_to_online(user_id)
        return True
    
    return is_locally_connected or is_redis_online
```

### 3. 连接管理器实例统一（2025-11-27）

**问题**：`broadcasting_factory` 和 `websocket_factory` 各自创建了 `DistributedConnectionManager` 实例，导致监听器不一致。

**解决方案**：
- `broadcasting_factory` 现在使用 `websocket_factory` 的连接管理器实例
- 确保整个应用只有一个 `DistributedConnectionManager` 实例
- 所有服务共享同一个Redis监听器

### 4. sender_type 枚举值简化（2025-11-27）

**问题**：`sender_type` 枚举包含多个角色类型（customer、consultant、doctor等），但实际业务只需要区分智能聊天消息和系统消息。

**解决方案**：
- 将枚举值简化为两种：`'chat'`（智能聊天消息）和 `'system'`（系统消息）
- 所有智能聊天消息统一使用 `sender_type='chat'`
- 系统消息使用 `sender_type='system'`
- 移除了角色映射逻辑，简化了代码

**数据库迁移**：
- 创建迁移文件，将现有数据中的非 `system` 值更新为 `chat`
- 重建枚举类型，只保留 `chat` 和 `system`

### 5. 参与者列表获取优化（2025-11-27）

**问题**：`_get_conversation_participants` 只查询了 `ConversationParticipant` 表，未包含会话的 `owner`。

**解决方案**：
- 同时包含 `owner` 和 `participants`
- 确保所有相关用户都能收到广播消息

**关键代码**：
```python
async def _get_conversation_participants(self, conversation_id: str) -> List[str]:
    # 查询会话信息（获取owner）
    conversation = self.db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    participant_ids = set()
    
    # 添加owner
    if conversation and conversation.owner_id:
        participant_ids.add(str(conversation.owner_id))
    
    # 添加所有参与者
    participants = self.db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.is_active == True
    ).all()
    
    for p in participants:
        if p.user_id:
            participant_ids.add(str(p.user_id))
    
    return list(participant_ids)
```

---

**架构版本**：WebSocket V2 + BroadcastingService V1 + 重构完成
**状态**：重构完成，已完全部署并投入使用
**最后更新**：2025-11-27 - 添加Redis Pub/Sub优化、在线状态检查优化、连接管理器统一等重要修复经验
