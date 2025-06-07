# 广播服务使用指南

## 概述

BroadcastingService是AnmeiSmart系统的核心消息推送服务，支持WebSocket实时通信和离线推送通知。

## 快速开始

### 1. 创建广播服务实例

```python
from app.services.broadcasting_factory import create_broadcasting_service
from app.api.deps import get_db

# 创建服务实例
db = next(get_db())
broadcasting_service = await create_broadcasting_service(db=db)
```

### 2. 基本消息广播

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

### 3. 特殊场景使用

#### 顾问回复消息

```python
# 优化的顾问回复推送（在线实时，离线移动端推送）
await broadcasting_service.broadcast_consultation_reply(
    conversation_id="conv_123",
    reply_data={
        "content": "根据您的需求，我推荐以下方案...",
        "consultant_name": "张医生",
        "reply_type": "consultation"
    },
    consultant_id="consultant_789"
)
```

#### 移动端专用通知

```python
# 重要消息只推送到移动设备
await broadcasting_service.send_mobile_only_notification(
    conversation_id="conv_123",
    message_data={
        "title": "预约提醒",
        "content": "您的预约将在30分钟后开始",
        "action": "open_appointment"
    }
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

### 4. 状态广播

#### 输入状态

```python
# 用户正在输入
await broadcasting_service.broadcast_typing_status(
    conversation_id="conv_123",
    user_id="customer_456",
    is_typing=True
)

# 用户停止输入
await broadcasting_service.broadcast_typing_status(
    conversation_id="conv_123",
    user_id="customer_456",
    is_typing=False
)
```

#### 消息已读状态

```python
# 标记消息为已读
await broadcasting_service.broadcast_read_status(
    conversation_id="conv_123",
    user_id="customer_456",
    message_ids=["msg_001", "msg_002", "msg_003"]
)
```

### 5. 直接消息发送

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

## 高级功能

### 1. 设备信息查询

```python
# 获取用户的设备连接信息
devices = await broadcasting_service.get_user_device_info("customer_456")
print(f"用户设备: {devices}")
# 输出: [
#   {"connection_id": "xxx", "device_type": "mobile", "connected_at": "..."},
#   {"connection_id": "yyy", "device_type": "desktop", "connected_at": "..."}
# ]
```

### 2. 在HTTP API中使用

```python
from fastapi import APIRouter, Depends
from app.services.broadcasting_factory import get_broadcasting_service_dependency

router = APIRouter()

@router.post("/chat/{conversation_id}/send")
async def send_message(
    conversation_id: str,
    message: MessageCreate,
    broadcasting_service = Depends(get_broadcasting_service_dependency)
):
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

## 推送通知日志

当前使用日志记录服务，推送通知将在日志中显示：

```
INFO  📱 推送通知 [mobile] [优先级: high]: customer_456
INFO     标题: 顾问回复
INFO     内容: 根据您的需求，我推荐以下方案...
INFO     [数据: {'conversation_id': 'conv_123', 'action': 'open_conversation'}]

DEBUG 移动端推送通知已排队: user_id=customer_456
INFO  顾问回复广播完成: conversation_id=conv_123, consultant_id=consultant_789
```

## 错误处理

服务内置了完善的错误处理机制：

```python
try:
    await broadcasting_service.broadcast_message(conversation_id, message_data)
except Exception as e:
    logger.error(f"消息广播失败: {e}")
    # 服务内部会自动记录错误并继续运行
```

## 性能优化建议

1. **批量操作**：对于大量用户的通知，考虑使用批量接口
2. **数据库连接**：复用数据库会话，避免频繁创建连接
3. **消息大小**：控制消息内容大小，避免影响WebSocket性能
4. **设备特定推送**：合理使用设备类型过滤，减少不必要的推送

## 监控和调试

### 关键日志级别

- `INFO`：推送通知记录、广播完成状态
- `DEBUG`：设备连接详情、消息路由信息
- `WARNING`：推送失败、配置问题
- `ERROR`：服务异常、连接错误

### 性能指标

通过日志可以监控：
- 消息广播响应时间
- 在线用户数量
- 推送成功率
- 设备连接分布

## 未来扩展

当需要集成真实推送服务时，只需：

1. 更新环境变量：`NOTIFICATION_PROVIDER=firebase`
2. 添加推送服务配置
3. 实现对应的NotificationProvider
4. 业务代码无需任何修改

这样的设计确保了系统的可扩展性和向后兼容性。 