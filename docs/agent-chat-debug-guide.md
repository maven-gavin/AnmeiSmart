# Agent 对话功能 - 调试指南

> 问题：发送消息后没有 AI 回复

---

## 🔍 问题诊断清单

### 1. 前端检查

**打开浏览器开发者工具**（F12 或 Cmd+Option+I）

#### 1.1 网络请求检查
- 打开 **Network** 标签
- 发送一条消息
- 查看是否有请求发送到 `/api/v1/agent/{agent_config_id}/chat`

**检查点**：
- ✅ 请求是否发送？
- ✅ 请求状态码是多少？（200、500、404？）
- ✅ 请求头是否包含认证信息？
- ✅ 请求体是否正确？

#### 1.2 控制台错误检查
- 打开 **Console** 标签
- 查看是否有 JavaScript 错误
- 特别关注红色错误信息

---

### 2. 后端检查

#### 2.1 Agent 配置检查

**检查 Agent 配置是否正确**：

```sql
-- 在数据库中查询
SELECT 
    id,
    app_name,
    base_url,
    enabled,
    LENGTH(api_key) as api_key_length
FROM agent_configs
WHERE id = 'age_9374272152da464c93aece9b9c1c54ca';
```

**必须确认**：
- ✅ `enabled = true`
- ✅ `base_url` 不为空（例如：`https://api.dify.ai/v1`）
- ✅ `api_key` 不为空（已加密存储）

#### 2.2 后端日志检查

**查看后端终端输出**，寻找以下关键信息：

```
INFO:app.ai.infrastructure.dify_agent_client:开始流式对话: user=user_xxx
ERROR:app.ai.infrastructure.dify_agent_client:流式对话失败
ERROR:app.ai.application.agent_chat_service:Agent 对话失败
```

---

## 🔧 常见问题和解决方案

### 问题 1：Agent 配置未启用或 API Key 为空

**症状**：
```
ValueError: Agent 配置不存在或未启用: age_xxx
ValueError: Agent 配置缺少 API Key: age_xxx
```

**解决方案**：
1. 进入 Agent 管理页面
2. 编辑 Agent 配置
3. 确保：
   - 状态为"启用"
   - API Key 已填写
   - Base URL 正确（如：`https://api.dify.ai/v1`）
4. 保存配置

---

### 问题 2：Dify API URL 不正确

**症状**：
```
httpx.HTTPError: 404 Not Found
```

**检查 Base URL 格式**：

正确格式：
```
✅ https://api.dify.ai/v1
✅ https://your-dify-server.com/v1
✅ http://localhost:5001/v1
```

错误格式：
```
❌ https://api.dify.ai/v1/chat-messages  （不要包含端点）
❌ https://api.dify.ai  （缺少版本号）
❌ api.dify.ai/v1  （缺少协议）
```

**代码中的 URL 构建**：
```python
# dify_agent_client.py 第 76 行
f"{self.base_url}/chat-messages"

# 如果 base_url = "https://api.dify.ai/v1"
# 完整 URL = "https://api.dify.ai/v1/chat-messages"  ✅
```

---

### 问题 3：Dify API Key 无效

**症状**：
```
httpx.HTTPError: 401 Unauthorized
```

**解决方案**：
1. 登录 Dify 控制台
2. 找到对应的应用
3. 复制正确的 API Key
4. 在 Agent 配置中更新 API Key

**API Key 格式**：
```
app-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### 问题 4：网络连接问题

**症状**：
```
httpx.ConnectError: Connection refused
httpx.TimeoutException: Request timeout
```

**检查**：
1. Dify 服务是否运行？
2. 网络是否可达？
3. 防火墙是否阻止？

**测试连接**：
```bash
# 测试 Dify API 是否可访问
curl -X POST "https://api.dify.ai/v1/chat-messages" \
  -H "Authorization: Bearer app-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {},
    "query": "Hello",
    "user": "test-user",
    "response_mode": "blocking"
  }'
```

---

### 问题 5：前端未正确调用 API

**检查前端代码**：

`service/agentChatService.ts` 应该调用：
```typescript
await ssePost(
  `/agent/${agentConfigId}/chat`,  // ✅ 正确路径
  {
    body: {
      message,
      conversation_id: conversationId,
      response_mode: 'streaming'
    }
  },
  callbacks
);
```

**检查 `apiClient` 配置**：
```typescript
// 确保 baseURL 正确配置
const apiClient = axios.create({
  baseURL: '/api/v1',  // 或完整 URL
  // ...
});
```

---

## 🧪 快速测试步骤

### 步骤 1：测试 API 端点是否存在

**使用 curl 测试**：
```bash
# 测试端点是否存在（应该返回 401 Unauthorized，说明端点存在）
curl -v http://localhost:8000/api/v1/agent/age_9374272152da464c93aece9b9c1c54ca/chat
```

### 步骤 2：测试完整的 API 调用

**获取认证 Token**（从浏览器开发者工具复制）：
1. 打开浏览器开发者工具
2. Network 标签
3. 查看任意一个 API 请求
4. 复制 Authorization header 的值

**测试调用**：
```bash
curl -X POST "http://localhost:8000/api/v1/agent/age_9374272152da464c93aece9b9c1c54ca/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "测试消息",
    "conversation_id": null,
    "response_mode": "streaming"
  }'
```

### 步骤 3：检查数据库中的消息

**查询是否保存了用户消息**：
```sql
SELECT 
    id,
    conversation_id,
    content,
    sender_type,
    timestamp
FROM messages
ORDER BY timestamp DESC
LIMIT 5;
```

---

## 📝 调试日志增强

**临时添加更多日志**，在 `agent_chat_service.py` 中：

```python
async def stream_chat(self, ...):
    try:
        logger.info(f"========== 开始 Agent 对话 ==========")
        logger.info(f"agent_config_id: {agent_config_id}")
        logger.info(f"user_id: {user_id}")
        logger.info(f"message: {message[:50]}...")
        
        # 1. 创建客户端
        dify_client = self.dify_client_factory.create_client_from_db(...)
        logger.info(f"✅ Dify 客户端创建成功")
        logger.info(f"   base_url: {dify_client.base_url}")
        
        # 4. 调用 Dify
        logger.info(f"🚀 开始调用 Dify API...")
        async for chunk in dify_client.stream_chat(...):
            logger.debug(f"📦 收到 chunk: {chunk[:100] if isinstance(chunk, bytes) else str(chunk)[:100]}")
            yield chunk
        
        logger.info(f"========== Agent 对话完成 ==========")
```

---

## 🎯 最可能的问题

根据经验，最常见的问题是：

1. **Agent 配置的 Base URL 格式不正确** ⭐⭐⭐⭐⭐
2. **Agent 配置的 API Key 为空或无效** ⭐⭐⭐⭐
3. **Agent 配置未启用** ⭐⭐⭐
4. **Dify 服务不可访问** ⭐⭐
5. **前端认证 Token 过期** ⭐

---

## ✅ 验证修复

**修复后，应该看到**：

1. **浏览器 Network 标签**：
   - POST 请求到 `/api/v1/agent/.../chat`
   - 状态码：200
   - Type: eventsource 或 text/event-stream
   - 响应中可以看到 SSE 数据流

2. **UI 界面**：
   - 用户消息立即显示
   - AI 消息逐字显示（流式效果）
   - 可能显示思考过程

3. **后端日志**：
   ```
   INFO: 开始流式对话: user=user_xxx
   INFO: Dify Agent 客户端已初始化: https://api.dify.ai/v1
   INFO: Agent 对话完成: conversation_id=conv_xxx
   ```

---

**需要帮助？** 请提供：
1. 浏览器 Network 标签的截图
2. 浏览器 Console 的错误信息
3. 后端终端的日志输出
4. Agent 配置的 Base URL（脱敏后）

