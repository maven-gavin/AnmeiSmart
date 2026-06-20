# WebSocket 广播

> 系统上下文见 [architecture.md](./architecture.md)。

## 背景

业务需要会话消息、任务状态等实时推送。若每页独立建连，连接数与重连逻辑难以维护。

## 方案

**应用级单连接 + 全局 Context 分发**（前端）+ **BroadcastingService**（后端经 Redis 广播）。

```text
页面组件 ──useWebSocket──▶ WebSocketContext（单长连接）
                              │
后端 BroadcastingService ◀──┘ /api/v1/ws
         │
         Redis pub/sub ──▶ 多实例 / 多客户端
```

## 怎么用

**前端**：在布局层挂载 `WebSocketProvider`，业务页用 `useWebSocket` 订阅事件，勿各页自建连接。

**后端**：业务 Service 注入 `BroadcastingService`，按用户/会话/房间发事件；离线走 `notification_service`（如已实现）。

## 代码入口

```text
web/src/contexts/WebSocketContext.tsx
web/src/hooks/useAppWebSocket.ts
web/src/service/websocket/

api/app/websocket/
├── broadcasting_service.py
├── websocket_service.py
├── websocket_handler.py
└── controllers/websocket.py
```

## 约定

- 心跳保活 + 指数退避重连（见 `web/src/service/websocket/core/`）
- 消息类型与 payload 见 `web/src/service/websocket/types.ts`、`api/app/websocket/schemas/`
- 环境变量：见 `api/.env` 中 Redis / WS 相关配置
