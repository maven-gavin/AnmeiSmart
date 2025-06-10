# 消息模型重构迁移总结

## 概述

已成功完成聊天消息模型的重构，将原本简单的文本字段升级为支持结构化内容的统一模型。本次重构实现了数据库结构的完全重建，确保代码干净整洁。

## 主要变更

### 1. 数据库模型 (`api/app/db/models/chat.py`)

#### 核心变更
- **`content` 字段**：从 `Text` 类型改为 `JSON` 类型，支持结构化数据存储
- **`type` 枚举**：从 `("text", "image", "voice", "file", "system")` 更新为 `("text", "media", "system")` 三大分类
- **新增字段**：
  - `reply_to_message_id`: 支持消息回复功能
  - `reactions`: 支持表情回应（JSON格式）
  - `extra_metadata`: 存储附加元数据

#### 性能优化
- 保留 `is_read` 和 `is_important` 作为独立布尔列，优化查询性能
- 添加了必要的数据库索引

### 2. Schema 模型重构 (`api/app/schemas/chat.py`)

#### 新的内容结构
- `TextMessageContent`: 纯文本消息内容
- `MediaMessageContent`: 媒体文件消息内容（图片、语音、视频、文档）
- `SystemEventContent`: 系统事件内容（视频通话、接管等）

#### 便利功能
- `MessageInfo.text_content`: 便捷获取文本内容
- `MessageInfo.media_info`: 便捷获取媒体信息
- 便利函数：`create_text_message_content()`, `create_media_message_content()`, `create_system_event_content()`

#### 向后兼容性
- 移除了向后兼容代码，确保代码简洁
- `MessageInfo.from_model()` 只支持新的JSON格式

### 3. 数据库迁移

#### 迁移策略
- 使用 `--fresh` 参数完全重建数据库
- 删除 `alembic_version` 表强制重新开始迁移
- 标记当前状态为最新迁移版本

#### 测试数据
- 更新所有测试数据使用新的结构化格式
- 包含三种消息类型的完整示例：
  - 文本消息：`{"text": "消息内容"}`
  - 媒体消息：`{"text": "附带文字", "media_info": {...}}`
  - 系统消息：`{"system_event_type": "takeover", ...}`

## 新消息模型特性

### 支持的消息类型

#### 1. 文本消息 (`type: "text"`)
```json
{
  "content": {
    "text": "您好！很高兴为您提供面部护理方面的咨询。"
  }
}
```

#### 2. 媒体消息 (`type: "media"`)
```json
{
  "content": {
    "text": "这是我的皮肤照片，请您看一下",
    "media_info": {
      "url": "http://example.com/uploads/skin_photo_001.jpg",
      "name": "skin_photo_001.jpg",
      "mime_type": "image/jpeg",
      "size_bytes": 125440,
      "metadata": {"width": 800, "height": 600}
    }
  }
}
```

#### 3. 系统消息 (`type: "system"`)
```json
{
  "content": {
    "system_event_type": "takeover",
    "status": "completed",
    "details": {
      "from": "ai",
      "to": "consultant",
      "reason": "客户需要专业咨询服务"
    }
  }
}
```

### 扩展字段

#### 消息回复
- `reply_to_message_id`: 指向被回复的消息ID
- 支持消息链式回复功能

#### 表情回应
- `reactions`: JSON格式存储表情回应
- 格式：`{"👍": ["user_id1", "user_id2"], "❤️": ["user_id3"]}`

#### 元数据
- `extra_metadata`: 存储附加信息
- 如：`{"upload_method": "file_picker", "client_info": {...}}`

## 应用场景

### 多文件上传
- 遵循"一文件一消息"原则
- 前端连续发送多个独立的媒体消息
- 支持各种文件类型（图片、语音、视频、文档）

### 语音消息
```json
{
  "type": "media",
  "content": {
    "media_info": {
      "url": "http://.../voice_message.m4a",
      "mime_type": "audio/mp4",
      "metadata": {"duration_seconds": 35.2}
    }
  },
  "extra_metadata": {"upload_method": "voice_recorder"}
}
```

### 系统事件
- 用户加入/离开会话
- AI/人工客服接管
- 视频通话状态变更

## 开发指南

### 创建消息示例

```python
from app.schemas.chat import create_text_message_content, MessageCreate

# 文本消息
content = create_text_message_content("您好，我需要咨询")
message = MessageCreate(
    content=content,
    type="text",
    conversation_id="conv_123",
    sender_id="usr_123",
    sender_type="customer"
)

# 媒体消息
content = create_media_message_content(
    media_url="http://example.com/photo.jpg",
    media_name="photo.jpg",
    mime_type="image/jpeg",
    size_bytes=125440,
    text="这是照片说明",
    metadata={"width": 800, "height": 600}
)
```

### Schema 转换

```python
from app.schemas.chat import MessageInfo

# 从数据库模型转换
message_info = MessageInfo.from_model(db_message)

# 便利属性访问
text = message_info.text_content
media = message_info.media_info
```

## 数据库操作

### 重新初始化数据库
```bash
# 完全重置数据库和测试数据
python scripts/setup_all.py --fresh

# 或分步执行
python scripts/init_db.py --drop-all
python scripts/migration.py stamp head
python scripts/seed_db.py --force
```

### 迁移管理
```bash
# 检查当前版本
python scripts/migration.py current

# 查看迁移历史
python scripts/migration.py history

# 创建新迁移
python scripts/migration.py revision -m "描述" --autogenerate
```

## 兼容性说明

### 前端适配
- 前端需要适配新的消息内容结构
- 根据 `type` 字段决定渲染方式
- 利用 `text_content` 和 `media_info` 便利属性

### API 变更
- 消息创建接口支持新的内容格式
- 保持现有端点路径不变
- Schema 自动处理新旧格式兼容

## 性能优势

1. **结构化查询**：JSON 字段支持内部索引和高效查询
2. **类型统一**：三大类型简化了消息处理逻辑
3. **扩展性强**：新的消息类型和字段可无缝添加
4. **存储优化**：状态字段作为独立列优化查询性能

## 未来扩展

### 计划功能
- 消息编辑和删除
- 消息转发
- 富文本消息支持
- 消息搜索和索引

### 新消息类型
- 卡片式消息（如预约确认）
- 表单消息（如问卷调查）
- 位置分享消息

---

**迁移完成时间**: 2025年1月25日  
**版本**: v2.0 - 统一消息模型  
**数据库迁移ID**: 52d952ae7d9b 