# 测试用例迁移指南

## 概述

根据消息模型重构，原有测试用例需要进行相应的更新以适配新的JSON结构化内容格式。本指南详细说明了需要修改的地方和新增的测试覆盖。

## 主要问题分析

### 1. 数据创建问题

**问题**：测试中直接创建Message对象时使用旧的字符串格式

```python
# ❌ 旧格式
Message(
    content="测试消息内容",  # 字符串格式
    type="text"
)

# ✅ 新格式
Message(
    content={"text": "测试消息内容"},  # JSON格式
    type="text"
)
```

### 2. 消息类型问题

**问题**：使用了已废弃的消息类型

```python
# ❌ 旧类型
type="image"  # 不再支持

# ✅ 新类型
type="media"  # 统一的媒体类型
```

### 3. HTTP接口测试格式

**问题**：发送消息的payload格式需要更新

```python
# ❌ 旧格式
data = {
    "content": "HTTP消息内容",
    "type": "text"
}

# ✅ 新格式
data = {
    "content": {"text": "HTTP消息内容"},
    "type": "text"
}
```

### 4. 断言更新

**问题**：对消息内容的断言需要适配JSON结构

```python
# ❌ 旧断言
assert result["content"] == "消息内容"

# ✅ 新断言
assert result["content"]["text"] == "消息内容"
```

## 修改策略

### 1. 使用便利函数创建内容

推荐使用Schema提供的便利函数：

```python
from app.schemas.chat import (
    create_text_message_content,
    create_media_message_content,
    create_system_event_content
)

# 文本消息
text_content = create_text_message_content("您好，我需要咨询")

# 媒体消息
media_content = create_media_message_content(
    media_url="http://example.com/photo.jpg",
    media_name="photo.jpg",
    mime_type="image/jpeg",
    size_bytes=125440,
    text="照片说明",
    metadata={"width": 800, "height": 600}
)

# 系统事件
system_content = create_system_event_content(
    system_event_type="takeover",
    status="completed",
    details={"from": "ai", "to": "consultant"}
)
```

### 2. 更新Message对象创建

```python
# 文本消息
text_message = Message(
    id="msg_text_123",
    conversation_id=conversation.id,
    content=create_text_message_content("消息内容"),
    type="text",
    sender_id=user.id,
    sender_type="customer",
    timestamp=datetime.now()
)

# 媒体消息
media_message = Message(
    id="msg_media_123",
    conversation_id=conversation.id,
    content=create_media_message_content(
        media_url="http://example.com/file.jpg",
        media_name="file.jpg",
        mime_type="image/jpeg",
        size_bytes=123456
    ),
    type="media",
    sender_id=user.id,
    sender_type="customer",
    timestamp=datetime.now()
)
```

### 3. 使用便利属性进行断言

```python
# 使用MessageInfo的便利属性
message_info = MessageInfo.from_model(db_message)
assert message_info.text_content == "期望的文本内容"
assert message_info.media_info["url"] == "期望的URL"
```

## 新增测试覆盖

### 1. 消息类型覆盖测试

需要添加以下新的测试用例：

- **文本消息测试**：基础文本消息的创建、发送、接收
- **媒体消息测试**：图片、语音、视频、文档等媒体类型
- **系统事件测试**：用户加入/离开、接管、视频通话等

### 2. Schema转换测试

```python
def test_message_info_convenience_properties():
    """测试MessageInfo便利属性"""
    # 测试文本消息
    text_message = create_message_with_text_content("文本内容")
    info = MessageInfo.from_model(text_message)
    assert info.text_content == "文本内容"
    assert info.media_info is None
  
    # 测试媒体消息
    media_message = create_message_with_media_content(...)
    info = MessageInfo.from_model(media_message)
    assert info.text_content == "附带文字"
    assert info.media_info is not None
```

### 3. 新字段测试

```python
def test_new_message_fields():
    """测试新增的消息字段"""
    message = Message(
        content=create_text_message_content("测试消息"),
        type="text",
        reply_to_message_id="original_msg_123",  # 回复功能
        reactions={"👍": ["user1", "user2"]},     # 表情回应
        extra_metadata={"upload_method": "paste"} # 额外元数据
    )
  
    assert message.reply_to_message_id == "original_msg_123"
    assert "👍" in message.reactions
    assert message.extra_metadata["upload_method"] == "paste"
```

### 4. 多文件上传场景测试

```python
@pytest.mark.asyncio
async def test_multiple_file_upload_scenario():
    """测试多文件上传场景（一文件一消息原则）"""
    files = [
        {"url": "file1.jpg", "type": "image/jpeg"},
        {"url": "file2.pdf", "type": "application/pdf"},
        {"url": "file3.mp4", "type": "video/mp4"}
    ]
  
    # 连续发送多条消息
    for file_info in files:
        content = create_media_message_content(
            media_url=file_info["url"],
            media_name=file_info["url"].split("/")[-1],
            mime_type=file_info["type"],
            size_bytes=123456
        )
        # 发送消息逻辑
        ...
  
    # 验证生成了独立的消息
    messages = get_recent_messages(conversation_id)
    assert len(messages) == 3
    for msg in messages:
        assert msg.type == "media"
```

### 5. 错误处理测试

```python
def test_invalid_content_structure():
    """测试无效的内容结构"""
    # 发送旧格式的内容应该被拒绝或转换
    invalid_data = {
        "content": "这是旧格式",  # 字符串而非JSON
        "type": "text"
    }
  
    response = send_message(invalid_data)
    assert response.status_code in [400, 422]  # 应该返回错误
```

## 文件结构建议

```
api/tests/
├── api/v1/
│   ├── test_chat_updated.py     # 更新后的主要功能测试
│   └── test_chat_legacy.py      # 保留部分原有测试（重命名）
├── schemas/
│   ├── test_message_schemas.py  # Schema转换和便利函数测试
│   └── test_chat_models.py      # 数据模型测试
├── services/
│   ├── test_message_service.py  # 消息服务测试
│   └── test_chat_scenarios.py   # 复杂场景测试
└── fixtures/
    └── message_fixtures.py      # 消息测试数据夹具
```

## 迁移步骤

### 第一阶段：修复现有测试

1. 更新所有Message对象的创建，使用新的content格式
2. 修复所有断言，适配JSON结构
3. 更新HTTP接口测试的payload格式

### 第二阶段：添加新功能测试

1. 添加媒体消息测试
2. 添加系统事件测试
3. 添加新字段（reply、reactions、metadata）测试

### 第三阶段：完善场景测试

1. 多文件上传场景
2. 视频通话事件场景
3. 复杂消息链和回复场景

### 第四阶段：性能和边界测试

1. 大文件处理测试
2. 并发消息发送测试
3. 异常情况处理测试

## 运行测试

```bash
# 运行所有聊天相关测试
pytest api/tests/api/v1/test_chat_updated.py -v

# 运行Schema测试
pytest api/tests/schemas/test_message_schemas.py -v

# 运行特定测试类
pytest api/tests/api/v1/test_chat_updated.py::TestMessageContentCreators -v

# 运行带覆盖率的测试
pytest api/tests/ --cov=app.schemas.chat --cov=app.services.chat
```

## 注意事项

1. **向后兼容性**：虽然新模型移除了向后兼容代码，但测试应该确保新格式完全正常工作
2. **数据库事务**：在测试中注意数据库事务的处理，避免测试之间的数据污染
3. **Mock策略**：对于复杂的依赖（如AI服务、WebSocket），使用Mock来隔离测试
4. **异步测试**：WebSocket和事件相关的测试需要正确处理异步操作

## 总结

通过以上修改，测试用例将能够：

- 完全适配新的消息模型结构
- 提供更好的测试覆盖率
- 确保新功能的正确性
- 保持测试的可维护性和可读性

建议优先修复现有测试，然后逐步添加新的测试用例，确保系统的稳定性和功能完整性。
