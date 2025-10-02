# Dify 通信调试指南

## 📋 概述

本文档说明了与 Dify Agent API 通信的调试方法和已完成的优化。

更新时间: 2025-10-02

---

## 🔧 已完成的优化

### 1. ✅ 修复 SSE 格式问题

**问题**: SSE 事件格式不完整，缺少双换行符 `\n\n`，导致前端可能无法正确解析事件。

**解决方案**: 
- 文件: `api/app/ai/infrastructure/dify_agent_client.py`
- 修改: 使用 buffer 模式正确处理 SSE 格式，确保每个事件以 `\n\n` 结束
- 代码行: 99-124

**影响**: 
- ✅ 前端可以正确解析所有 SSE 事件
- ✅ 打字机效果更流畅

---

### 2. ✅ 实现 conversation_id 持久化

**问题**: 每次对话都传入 `conversation_id=None`，导致无法利用历史上下文，多轮对话失败。

**解决方案**:
- 文件: `api/app/ai/application/agent_chat_service.py`
- 修改:
  1. 从会话 `extra_metadata` 读取 `dify_conversation_id`（代码行: 117-120）
  2. 传递给 Dify API（代码行: 131）
  3. 保存 Dify 返回的 `conversation_id`（代码行: 185-191）

**影响**:
- ✅ 支持多轮对话
- ✅ AI 可以记住之前的对话内容
- ✅ 会话上下文得以保持

---

### 3. ✅ 增强错误处理和日志

**问题**: HTTP 错误时没有记录完整的响应体，难以定位问题。

**解决方案**:
- 文件: `api/app/ai/infrastructure/dify_agent_client.py`
- 修改: 分类处理不同类型的异常（代码行: 126-167）
  - `HTTPStatusError`: 4xx/5xx 状态码错误
  - `RequestError`: 网络连接失败、超时等
  - `Exception`: 其他未预期错误

**影响**:
- ✅ 详细的错误日志（状态码、URL、响应体）
- ✅ 更容易定位问题根源
- ✅ 前端可以收到结构化的错误信息

---

### 4. ✅ 添加调试工具

创建了两个测试脚本用于验证 Dify 通信：

#### 脚本 1: `test_dify_raw.py` - 原始请求测试

**用途**: 最底层的 API 调试，不依赖任何封装

**使用方法**:
```bash
cd /Users/gavin/workspace/AnmeiSmart/api
python scripts/test_dify_raw.py
```

然后根据提示输入：
- Base URL (例: `http://localhost/v1`)
- API Key
- 测试消息（可选）

**输出内容**:
- 完整的 HTTP 请求详情
- 逐行 SSE 响应
- Token 使用统计
- conversation_id

---

#### 脚本 2: `test_dify_connection.py` - 封装层测试

**用途**: 测试通过系统封装的 Dify 客户端

**使用方法**:

1. **从数据库加载配置**:
```bash
python scripts/test_dify_connection.py --agent-id <agent_config_id>
```

2. **直接连接模式**:
```bash
python scripts/test_dify_connection.py --direct \
  --api-key "app-xxx" \
  --base-url "http://localhost/v1"
```

**输出内容**:
- Agent 配置信息
- 流式对话过程
- conversation_id
- 完整回复内容

---

## 🧪 调试流程

### 步骤 1: 测试原始 API 连接

```bash
python scripts/test_dify_raw.py
```

**检查点**:
- [ ] HTTP 状态码是否为 200
- [ ] 是否收到 SSE 流
- [ ] 是否有 `conversation_id`
- [ ] 是否有完整的回复内容
- [ ] 是否有 `message_end` 事件

### 步骤 2: 测试系统封装

```bash
python scripts/test_dify_connection.py --agent-id <agent_config_id>
```

**检查点**:
- [ ] Agent 配置是否正确加载
- [ ] API Key 是否正确解密
- [ ] 流式响应是否正常
- [ ] 消息是否正确解析

### 步骤 3: 查看详细日志

启动 API 服务后，日志会显示详细的调试信息：

```bash
cd /Users/gavin/workspace/AnmeiSmart/api
python run_dev.py
```

**关键日志标识**:
- `🚀 开始 Agent 对话` - 对话开始
- `📝 步骤 1-6` - 各步骤执行
- `📦 收到第 N 个 chunk` - SSE 数据流
- `✅ Agent 对话完成` - 对话成功
- `❌ Agent 对话失败` - 对话失败

### 步骤 4: 检查常见问题

#### 问题 A: 状态码 401 Unauthorized

**可能原因**:
- API Key 错误
- API Key 未正确加密/解密

**解决方法**:
```bash
# 检查数据库中的 Agent 配置
SELECT id, name, base_url, enabled FROM agent_configs;

# 验证 API Key 是否正确
python scripts/test_dify_raw.py
```

#### 问题 B: 状态码 404 Not Found

**可能原因**:
- Base URL 错误
- Dify 服务未启动
- 端点路径错误

**解决方法**:
```bash
# 检查 Base URL 格式
# 正确: http://localhost/v1 或 https://api.dify.ai/v1
# 错误: http://localhost/v1/ (多余的斜杠)
# 错误: http://localhost (缺少 /v1)
```

#### 问题 C: 超时或连接失败

**可能原因**:
- Dify 服务未运行
- 网络不可达
- 防火墙拦截

**解决方法**:
```bash
# 测试网络连通性
curl -v http://localhost/v1/info \
  -H "Authorization: Bearer YOUR_API_KEY"

# 检查 Dify 服务状态
docker ps | grep dify
```

#### 问题 D: 收到数据但无法解析

**可能原因**:
- SSE 格式不正确
- JSON 解析失败

**解决方法**:
```bash
# 使用原始测试脚本查看完整数据
python scripts/test_dify_raw.py

# 检查前几行输出的格式
# 正确格式: data: {"event": "message", ...}\n\n
```

---

## 📊 Dify API 事件类型

根据 Dify 文档，流式响应包含以下事件类型：

| 事件类型 | 说明 | 关键字段 |
|---------|------|---------|
| `message` | LLM 文本块 | `answer`, `message_id` |
| `message_file` | 消息文件 | `type`, `url` |
| `message_end` | 消息结束 | `metadata.usage` |
| `message_replace` | 内容审核替换 | `answer` |
| `workflow_started` | 工作流开始 | `workflow_run_id` |
| `node_started` | 节点开始 | `node_id`, `node_type` |
| `node_finished` | 节点结束 | `status`, `outputs` |
| `workflow_finished` | 工作流结束 | `status`, `outputs` |
| `tts_message` | TTS 音频流 | `audio` (base64) |
| `tts_message_end` | TTS 结束 | - |
| `error` | 错误 | `status`, `code`, `message` |
| `ping` | 保持连接 | 每 10 秒 |

---

## 🔍 日志分析示例

### 成功的对话日志

```
================================================================================
🚀 开始 Agent 对话
   agent_config_id: abc123
   user_id: user123
   message: 你好
   conversation_id: conv456
📝 步骤 1: 创建 Dify 客户端...
✅ Dify 客户端创建成功
   base_url: http://localhost/v1
   api_key: ********************...12345678
📝 步骤 2: 获取或创建会话...
✅ 使用现有会话: conv456
📝 步骤 3: 保存用户消息...
✅ 用户消息已保存: msg789
📝 步骤 4: 调用 Dify API 流式对话...
   完整 URL: http://localhost/v1/chat-messages
   user_identifier: user_user123
   dify_conversation_id: dify_conv_abc
🌐 准备发送 HTTP 请求到 Dify:
   URL: http://localhost/v1/chat-messages
   Method: POST
   Headers: Authorization=Bearer ***...12345678
   Body: {"inputs":{},"query":"你好","user":"user_user123","response_mode":"streaming","conversation_id":"dify_conv_abc"}...
🚀 开始发送请求...
📡 收到响应: status_code=200
✅ 响应状态正常，开始读取流式数据...
📦 第 1 行原始数据: [data: {"event":"message","task_id":"...","message_id":"...","answer":"你","created_at":1696234567}]
✅ 发送 SSE 事件: data: {"event":"message",...}...
📦 第 2 行原始数据: []
📦 第 3 行原始数据: [data: {"event":"message","task_id":"...","message_id":"...","answer":"好","created_at":1696234567}]
...
✅ 流式读取完成，共 50 行
✅ AI 消息已保存: msg790
✅ 已保存 Dify conversation_id: dify_conv_abc
✅ Agent 对话完成
   conversation_id: conv456
   ai_message_id: msg790
   内容长度: 15 字符
   总 chunks: 25
================================================================================
```

### 失败的对话日志

```
================================================================================
❌ Agent 对话失败: ...
❌ Dify API 返回错误状态码
   状态码: 401
   URL: http://localhost/v1/chat-messages
   请求方法: POST
   响应体: {"code":"unauthorized","message":"Invalid API key"}
   错误详情: {
     "code": "unauthorized",
     "message": "Invalid API key"
   }
================================================================================
```

---

## 📝 关键代码位置

### Dify 客户端
- **文件**: `api/app/ai/infrastructure/dify_agent_client.py`
- **类**: `DifyAgentClient`
- **核心方法**: `stream_chat()` (第 43-167 行)

### 应用服务
- **文件**: `api/app/ai/application/agent_chat_service.py`
- **类**: `AgentChatApplicationService`
- **核心方法**: `stream_chat()` (第 46-212 行)

### API 端点
- **文件**: `api/app/ai/endpoints/agent_chat.py`
- **路由**: `POST /api/v1/agent/chat/stream`

---

## 🎯 下一步优化建议

1. **性能监控**: 添加 Token 使用统计和响应时间监控
2. **重试机制**: 对临时性网络错误实现自动重试
3. **缓存机制**: 缓存常用的 Agent 配置
4. **速率限制**: 防止过度调用 Dify API
5. **安全审计**: 记录所有 API 调用，便于审计

---

## 📚 参考资料

- [Dify Advanced Chat App API 文档](https://docs.dify.ai/guides/api-reference/chat-api)
- [Server-Sent Events (SSE) 规范](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [httpx 文档 - Streaming Responses](https://www.python-httpx.org/quickstart/#streaming-responses)

---

## 🆘 获取帮助

如果遇到问题:

1. 首先运行 `python scripts/test_dify_raw.py` 测试原始连接
2. 查看详细日志（启用 DEBUG 级别）
3. 检查 Dify 服务状态
4. 验证 API Key 和 Base URL
5. 查阅本文档的常见问题部分

---

**文档维护**: 请在修改相关代码后及时更新本文档

