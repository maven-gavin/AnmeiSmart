# 新消息模型使用指南

## 概述

新的统一消息模型支持三种主要类型的消息：
- **text**: 纯文本消息
- **media**: 媒体文件消息（图片、语音、视频、文档等）
- **system**: 系统事件消息（如视频通话状态等）

## 数据库结构变更

### 主要变更

1. `content` 字段从 `Text` 改为 `JSON`，支持结构化内容
2. `type` 枚举更新为 `("text", "media", "system")`
3. 新增字段：
   - `reply_to_message_id`: 支持消息回复
   - `reactions`: 支持表情回应
   - `extra_metadata`: 存储附加元数据

### 迁移说明

执行以下命令应用数据库变更：
```bash
cd api
source venv/bin/activate
alembic upgrade head
```

## 使用示例

### 1. 创建文本消息

```python
from app.schemas.chat import create_text_message_content, MessageCreate

# 创建文本消息内容
content = create_text_message_content("您好，我想咨询皮肤护理的问题。")

# 创建消息请求
message_create = MessageCreate(
    content=content,
    type="text",
    conversation_id="conv_123456",
    sender_id="usr_123456",
    sender_type="customer"
)
```

### 2. 创建媒体消息

```python
from app.schemas.chat import create_media_message_content, MessageCreate

# 创建媒体消息内容
content = create_media_message_content(
    media_url="http://example.com/images/skin-photo.jpg",
    media_name="skin_photo_001.jpg",
    mime_type="image/jpeg",
    size_bytes=125440,
    text="这是我的皮肤照片，请您看一下",  # 可选的附带文字
    metadata={"width": 800, "height": 600}
)

# 创建消息请求
message_create = MessageCreate(
    content=content,
    type="media",
    conversation_id="conv_123456",
    sender_id="usr_123456",
    sender_type="customer",
    extra_metadata={"upload_method": "file_picker"}
)
```

### 3. 创建语音消息

```python
# 语音消息也是媒体类型
content = create_media_message_content(
    media_url="http://example.com/audio/voice_message.m4a",
    media_name="voice_message_001.m4a",
    mime_type="audio/mp4",
    size_bytes=58240,
    text=None,  # 语音消息通常没有附带文字
    metadata={"duration_seconds": 35.2}
)

message_create = MessageCreate(
    content=content,
    type="media",
    conversation_id="conv_123456",
    sender_id="usr_123456",
    sender_type="customer",
    extra_metadata={"upload_method": "voice_recorder"}
)
```

### 4. 创建系统事件消息

```python
from app.schemas.chat import create_system_event_content, MessageCreate

# 视频通话结束事件
content = create_system_event_content(
    event_type="video_call_status",
    status="ended",
    call_id="vc_call_abc123",
    duration_seconds=303,
    participants=["usr_123456", "usr_789012"]
)

message_create = MessageCreate(
    content=content,
    type="system",
    conversation_id="conv_123456",
    sender_id="usr_123456",
    sender_type="customer"
)
```

### 5. 处理消息回复

```python
# 回复某条消息
reply_content = create_text_message_content("谢谢您的建议！")

reply_message = MessageCreate(
    content=reply_content,
    type="text",
    conversation_id="conv_123456",
    sender_id="usr_123456",
    sender_type="customer",
    reply_to_message_id="msg_original_123"  # 被回复的消息ID
)
```

### 6. 添加表情回应

```python
# 在消息服务中处理表情回应
def add_reaction(message_id: str, user_id: str, emoji: str):
    # 从数据库获取消息
    message = get_message_by_id(message_id)
    
    # 更新reactions字段
    if not message.reactions:
        message.reactions = {}
    
    if emoji not in message.reactions:
        message.reactions[emoji] = []
    
    if user_id not in message.reactions[emoji]:
        message.reactions[emoji].append(user_id)
    
    # 保存到数据库
    save_message(message)
```

## 向后兼容性

新模型提供了完整的向后兼容性：

1. **自动转换**: `MessageInfo.from_model()` 方法会自动将旧格式的消息转换为新格式
2. **便利属性**: 提供 `text_content` 和 `media_info` 属性用于向后兼容
3. **渐进式迁移**: 可以在现有系统运行的同时逐步迁移到新格式

## 前端适配

前端需要根据消息的 `type` 字段来渲染不同类型的消息：

```typescript
// 示例：React组件中的消息渲染
function MessageComponent({ message }: { message: MessageInfo }) {
  switch (message.type) {
    case 'text':
      return <TextMessage content={message.content.text} />;
    case 'media':
      return <MediaMessage mediaInfo={message.content.media_info} text={message.content.text} />;
    case 'system':
      return <SystemMessage event={message.content} />;
    default:
      return null;
  }
}
```

## 最佳实践

1. **一致性**: 始终使用提供的便利函数创建消息内容
2. **验证**: 在创建消息前验证内容结构的完整性
3. **错误处理**: 妥善处理内容解析可能出现的异常
4. **性能**: 利用数据库索引优化查询性能
5. **安全性**: 对用户上传的媒体文件进行适当的安全检查

## 未来扩展

新模型为未来功能预留了扩展空间：

- **消息编辑**: 可在 `extra_metadata` 中记录编辑历史
- **消息加密**: 可在 `extra_metadata` 中存储加密相关信息
- **富文本**: 可扩展 `text` 内容支持Markdown或其他格式
- **消息状态**: 可扩展支持更多状态（如"正在输入"、"已撤回"等） 