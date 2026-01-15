# Agent Chat API 使用指南

## 概述

本文档提供 Agent Chat API 的完整使用指南，包括所有端点的详细说明、请求示例和响应格式。

## 基础信息

- **基础路径**: `/api/v1/agent`
- **认证方式**: Bearer Token（JWT）
- **内容类型**: `application/json`（除文件上传外）

## 认证

所有 API 端点都需要认证。在请求头中添加 Bearer Token：

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## API 端点清单

### 1. 对话管理

#### 1.1 流式对话

**端点**: `POST /agent/{agent_config_id}/chat`

**描述**: 与 AI Agent 进行流式对话

**请求参数**:

```json
{
  "message": "你好，我想咨询美容方案",
  "conversation_id": "conv-123",  // 可选，不传则创建新会话
  "response_mode": "streaming",   // streaming 或 blocking
  "inputs": {}                     // 额外输入参数
}
```

**响应**: Server-Sent Events (SSE) 流

```
data: {"event": "message", "answer": "您好", "conversation_id": "conv-123"}

data: {"event": "message", "answer": "，很高兴为您服务"}

data: {"event": "message_end", "metadata": {...}}
```

#### 1.2 获取会话列表

**端点**: `GET /agent/{agent_config_id}/conversations`

**描述**: 获取用户的所有 Agent 会话

**响应**:

```json
[
  {
    "id": "conv-123",
    "agent_config_id": "agent-1",
    "title": "美容咨询",
    "created_at": "2025-10-03T10:00:00Z",
    "updated_at": "2025-10-03T10:30:00Z",
    "message_count": 15,
    "last_message": "感谢您的咨询"
  }
]
```

#### 1.3 创建新会话

**端点**: `POST /agent/{agent_config_id}/conversations`

**请求参数**:

```json
{
  "title": "护肤咨询"  // 可选
}
```

**响应**:

```json
{
  "id": "conv-456",
  "agent_config_id": "agent-1",
  "title": "护肤咨询",
  "created_at": "2025-10-03T11:00:00Z",
  "updated_at": "2025-10-03T11:00:00Z",
  "message_count": 0,
  "last_message": null
}
```

#### 1.4 获取会话消息历史

**端点**: `GET /agent/{agent_config_id}/conversations/{conversation_id}/messages`

**查询参数**:

- `limit`: 返回数量限制（默认 50）

**响应**:

```json
[
  {
    "id": "msg-123",
    "conversation_id": "conv-123",
    "content": "你好，我想咨询美容方案",
    "is_answer": false,
    "timestamp": "2025-10-03T10:00:00Z",
    "agent_thoughts": null,
    "files": null,
    "is_error": false
  },
  {
    "id": "msg-124",
    "conversation_id": "conv-123",
    "content": "您好，我可以为您推荐...",
    "is_answer": true,
    "timestamp": "2025-10-03T10:00:05Z",
    "agent_thoughts": [...],
    "files": null,
    "is_error": false
  }
]
```

#### 1.5 更新会话

**端点**: `PUT /agent/{agent_config_id}/conversations/{conversation_id}`

**请求参数**:

```json
{
  "title": "新的会话标题"
}
```

**响应**: 同创建会话

#### 1.6 删除会话

**端点**: `DELETE /agent/{agent_config_id}/conversations/{conversation_id}`

**响应**: 204 No Content

---

### 2. 对话增强

#### 2.1 提交消息反馈

**端点**: `POST /agent/{agent_config_id}/feedback`

**描述**: 对 AI 回复进行点赞或点踩

**请求参数**:

```json
{
  "message_id": "msg-124",
  "rating": "like"  // "like" 或 "dislike"
}
```

**响应**:

```json
{
  "success": true,
  "message": "反馈提交成功"
}
```

**cURL 示例**:

```bash
curl -X POST "http://localhost:8000/api/v1/agent/agent-1/feedback" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "msg-124",
    "rating": "like"
  }'
```

#### 2.2 获取建议问题

**端点**: `GET /agent/{agent_config_id}/messages/{message_id}/suggested`

**描述**: 基于对话上下文获取 AI 建议的后续问题

**响应**:

```json
{
  "questions": [
    "如何选择适合我的护肤方案？",
    "这个项目的恢复期需要多久？",
    "价格范围是多少？"
  ]
}
```

**cURL 示例**:

```bash
curl -X GET "http://localhost:8000/api/v1/agent/agent-1/messages/msg-124/suggested" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 2.3 停止消息生成

**端点**: `POST /agent/{agent_config_id}/stop`

**描述**: 中断正在进行的 AI 回复生成

**请求参数**:

```json
{
  "task_id": "task-789"
}
```

**响应**:

```json
{
  "success": true,
  "message": "已停止消息生成"
}
```

**cURL 示例**:

```bash
curl -X POST "http://localhost:8000/api/v1/agent/agent-1/stop" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task-789"
  }'
```

---

### 3. 媒体处理

#### 3.1 语音转文字

**端点**: `POST /agent/{agent_config_id}/audio-to-text`

**描述**: 上传音频文件，转换为文本

**请求**: `multipart/form-data`

- `file`: 音频文件（支持 mp3, wav, m4a 等格式）

**响应**:

```json
{
  "text": "这是从音频中识别出的文本内容"
}
```

**cURL 示例**:

```bash
curl -X POST "http://localhost:8000/api/v1/agent/agent-1/audio-to-text" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/audio.mp3"
```

**JavaScript 示例**:

```javascript
const formData = new FormData();
formData.append('file', audioFile);

const response = await fetch('/api/v1/agent/agent-1/audio-to-text', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const result = await response.json();
console.log('识别文本:', result.text);
```

#### 3.2 文字转语音

**端点**: `POST /agent/{agent_config_id}/text-to-audio`

**描述**: 将文本转换为语音

**请求参数**:

```json
{
  "text": "要转换成语音的文本内容",
  "streaming": false  // 是否流式返回
}
```

**响应**: 音频数据（JSON 格式）

```json
{
  "audio_url": "http://example.com/audio/xxx.mp3",
  "duration": 3.5,
  "format": "mp3"
}
```

**cURL 示例**:

```bash
curl -X POST "http://localhost:8000/api/v1/agent/agent-1/text-to-audio" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，欢迎使用AI助手",
    "streaming": false
  }'
```

**JavaScript 示例**:

```javascript
const response = await fetch('/api/v1/agent/agent-1/text-to-audio', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    text: '你好，欢迎使用AI助手',
    streaming: false
  })
});

const result = await response.json();
const audio = new Audio(result.audio_url);
audio.play();
```

#### 3.3 文件上传

**端点**: `POST /agent/{agent_config_id}/upload`

**描述**: 上传文件到 Dify，用于后续对话中引用

**请求**: `multipart/form-data`

- `file`: 文件（支持 pdf, docx, txt, xlsx 等格式）

**响应**:

```json
{
  "id": "file-abc123",
  "name": "document.pdf",
  "size": 102400,
  "mime_type": "application/pdf",
  "created_at": "2025-10-03T10:00:00Z"
}
```

**cURL 示例**:

```bash
curl -X POST "http://localhost:8000/api/v1/agent/agent-1/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

**JavaScript 示例**:

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('/api/v1/agent/agent-1/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const result = await response.json();
console.log('文件上传成功:', result.id);

// 在对话中引用上传的文件
const chatResponse = await fetch('/api/v1/agent/agent-1/chat', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: '请分析这份文档',
    files: [{ id: result.id, type: 'document' }]
  })
});
```

---

### 4. 应用配置

#### 4.1 获取应用参数

**端点**: `GET /agent/{agent_config_id}/parameters`

**描述**: 获取应用的配置参数，包括用户输入表单、文件上传配置、系统参数等

**响应**:

```json
{
  "user_input_form": [
    {
      "paragraph": {
        "label": "客户需求",
        "variable": "customer_requirement",
        "required": true,
        "default": ""
      }
    }
  ],
  "file_upload": {
    "enabled": true,
    "allowed_file_types": ["pdf", "docx", "txt"],
    "number_limits": 3
  },
  "system_parameters": {
    "max_tokens": 2000,
    "temperature": 0.7
  },
  "opening_statement": "您好，我是您的客服助手，有什么可以帮您的？",
  "suggested_questions": [
    "如何选择适合的护肤方案？",
    "面部护理的注意事项有哪些？"
  ],
  "speech_to_text": {
    "enabled": true
  },
  "text_to_speech": {
    "enabled": true,
    "voice": "zh-CN-XiaoxiaoNeural"
  }
}
```

**cURL 示例**:

```bash
curl -X GET "http://localhost:8000/api/v1/agent/agent-1/parameters" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**使用场景**:

- 前端初始化时获取应用配置
- 动态渲染用户输入表单
- 检查文件上传限制
- 显示开场白和建议问题

#### 4.2 获取应用元数据

**端点**: `GET /agent/{agent_config_id}/meta`

**描述**: 获取应用的元数据信息，如工具图标等

**响应**:

```json
{
  "tool_icons": {
    "dalle2": {
      "icon": {
        "background": "#fff",
        "content": "🎨"
      }
    },
    "web_reader": {
      "icon": {
        "background": "#E3F2FD",
        "content": "🌐"
      }
    }
  }
}
```

**cURL 示例**:

```bash
curl -X GET "http://localhost:8000/api/v1/agent/agent-1/meta" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**使用场景**:

- 在 Agent 思考过程中显示工具图标
- 美化 UI 展示效果

---

## 错误处理

### 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "detail": "错误描述信息"
}
```

### HTTP 状态码

- **200 OK**: 请求成功
- **201 Created**: 资源创建成功
- **204 No Content**: 删除成功（无响应体）
- **400 Bad Request**: 请求参数错误
- **401 Unauthorized**: 未认证或认证失败
- **403 Forbidden**: 无权限访问
- **404 Not Found**: 资源不存在
- **500 Internal Server Error**: 服务器内部错误

### 常见错误

#### 1. 认证失败

```json
{
  "detail": "Could not validate credentials"
}
```

**解决方案**: 检查 Token 是否正确，是否已过期

#### 2. 参数验证错误

```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**解决方案**: 检查必填参数是否提供

#### 3. Agent 配置不存在

```json
{
  "detail": "Agent 配置不存在或未启用: agent-999"
}
```

**解决方案**: 检查 `agent_config_id` 是否正确

#### 4. 会话不存在

```json
{
  "detail": "会话不存在: conv-999"
}
```

**解决方案**: 检查 `conversation_id` 是否正确

---

## 完整使用流程示例

### 场景：用户与 AI 进行美容咨询

```javascript
// 1. 获取访问令牌（登录）
const loginResponse = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: 'username=user@example.com&password=password123'
});
const { access_token } = await loginResponse.json();

// 2. 创建新会话
const createConvResponse = await fetch('/api/v1/agent/agent-1/conversations', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ title: '美容咨询' })
});
const conversation = await createConvResponse.json();
console.log('会话ID:', conversation.id);

// 3. 发起对话
const chatResponse = await fetch('/api/v1/agent/agent-1/chat', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: '我想了解面部护理方案',
    conversation_id: conversation.id
  })
});

// 处理流式响应
const reader = chatResponse.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      if (data.event === 'message') {
        console.log('AI回复:', data.answer);
        // 显示回复内容
        displayMessage(data.answer);
      }
    }
  }
}

// 4. 提交反馈（点赞）
await fetch('/api/v1/agent/agent-1/feedback', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message_id: 'msg-123',
    rating: 'like'
  })
});

// 5. 获取建议问题
const suggestedResponse = await fetch(
  '/api/v1/agent/agent-1/messages/msg-123/suggested',
  {
    headers: { 'Authorization': `Bearer ${access_token}` }
  }
);
const { questions } = await suggestedResponse.json();
console.log('建议问题:', questions);

// 6. 上传相关文档
const formData = new FormData();
formData.append('file', documentFile);

const uploadResponse = await fetch('/api/v1/agent/agent-1/upload', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${access_token}` },
  body: formData
});
const uploadResult = await uploadResponse.json();
console.log('文件ID:', uploadResult.id);

// 7. 引用文档继续对话
await fetch('/api/v1/agent/agent-1/chat', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: '请根据我上传的文档提供建议',
    conversation_id: conversation.id,
    files: [{ id: uploadResult.id }]
  })
});
```

---

## 最佳实践

### 1. 认证管理

- 使用 Token 刷新机制，避免频繁登录
- 安全存储 Token（使用 httpOnly Cookie 或安全的本地存储）
- Token 过期时自动重新登录

### 2. 流式响应处理

- 使用 Server-Sent Events 或 Fetch API 的 ReadableStream
- 实现断线重连机制
- 显示加载状态和进度

### 3. 文件上传

- 限制文件大小和类型
- 显示上传进度
- 处理上传失败情况
- 提供取消上传功能

### 4. 错误处理

- 实现全局错误处理器
- 向用户显示友好的错误信息
- 记录错误日志用于调试
- 提供重试机制

### 5. 性能优化

- 使用分页加载会话列表和消息历史
- 缓存常用数据
- 使用防抖和节流优化搜索和输入
- 压缩上传文件

---

## SDK 示例

### Python SDK

```python
import httpx
from typing import Optional, List, Dict, Any

class AgentChatClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}
  
    async def chat(
        self,
        agent_id: str,
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """发起对话"""
        url = f"{self.base_url}/agent/{agent_id}/chat"
        data = {
            "message": message,
            "conversation_id": conversation_id
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
  
    async def submit_feedback(
        self,
        agent_id: str,
        message_id: str,
        rating: str
    ) -> Dict[str, Any]:
        """提交反馈"""
        url = f"{self.base_url}/agent/{agent_id}/feedback"
        data = {"message_id": message_id, "rating": rating}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
  
    async def get_suggested_questions(
        self,
        agent_id: str,
        message_id: str
    ) -> List[str]:
        """获取建议问题"""
        url = f"{self.base_url}/agent/{agent_id}/messages/{message_id}/suggested"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()["questions"]
  
    async def upload_file(
        self,
        agent_id: str,
        file_path: str
    ) -> Dict[str, Any]:
        """上传文件"""
        url = f"{self.base_url}/agent/{agent_id}/upload"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            async with httpx.AsyncClient() as client:
                response = await client.post(url, files=files, headers=self.headers)
                response.raise_for_status()
                return response.json()

# 使用示例
client = AgentChatClient(
    base_url="http://localhost:8000/api/v1",
    token="YOUR_ACCESS_TOKEN"
)

# 发起对话
result = await client.chat("agent-1", "你好")

# 提交反馈
await client.submit_feedback("agent-1", "msg-123", "like")

# 获取建议
questions = await client.get_suggested_questions("agent-1", "msg-123")
```

---

## 相关文档

---

## 技术支持

如有问题或建议，请联系：

- 邮箱: support@example.com
- 文档更新：2025-10-03
