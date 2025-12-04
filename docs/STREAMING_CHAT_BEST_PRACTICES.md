# AI 流式对话与打字机效果最佳实践

## 概述

本文档总结了 AI 流式对话（Streaming Chat）和前端打字机效果（Typewriter Effect）的前后端实现经验，适用于 FastAPI + React/Next.js 技术栈。这些实践可以应用到其他项目中，确保流式响应的流畅性和用户体验。

---

## 一、后端实现标准（FastAPI）

### 1.1 协议选择

**必须使用 Server-Sent Events (SSE) 标准**，而不是 WebSocket。SSE 更适合单向数据流场景，实现简单且兼容性好。

### 1.2 响应格式规范

#### 1.2.1 SSE 数据格式

严格遵循 SSE 标准格式：`data: <JSON_STRING>\n\n`

```python
# ✅ 正确格式
data = f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
yield data

# ❌ 错误格式
yield json.dumps(chunk)  # 缺少 "data: " 前缀和 "\n\n" 后缀
```

#### 1.2.2 数据结构定义

定义清晰的流式响应数据结构：

```python
from typing import Optional, Dict, Any
from pydantic import BaseModel

class StreamChunkData(BaseModel):
    """流式响应数据块"""
    text: Optional[str] = None  # 增量文本内容
    files: Optional[Dict[str, Any]] = None  # 文件信息（如需要）
    metadata: Optional[Dict[str, Any]] = None  # 元数据

class StreamChatResponse(BaseModel):
    """流式响应完整结构"""
    event: str  # 事件类型：'message', 'error', 'finish', 'file_generated' 等
    data: StreamChunkData
    conversation_id: Optional[str] = None
    is_complete: bool = False
```

### 1.3 关键响应头配置

**这是最容易被忽略但最关键的部分**。如果缺少这些响应头，流式响应会被反向代理（如 Nginx）缓冲，导致前端看起来像"卡顿"而不是"流畅打字"。

```python
from fastapi.responses import StreamingResponse

return StreamingResponse(
    generate(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",  # 禁用缓存
        "Connection": "keep-alive",    # 保持连接
        "Access-Control-Allow-Origin": "*",  # CORS（根据实际情况调整）
        "Access-Control-Allow-Headers": "Content-Type",
        "X-Accel-Buffering": "no",    # ⚠️ 关键：禁用 Nginx 缓冲
        "Transfer-Encoding": "chunked",  # 确保分块传输
    }
)
```

**关键响应头说明**：

- `X-Accel-Buffering: "no"`：**必须设置**。告诉 Nginx 不要缓冲响应，立即转发给客户端。缺少此头会导致流式响应被缓存成块，前端体验差。
- `Cache-Control: "no-cache"`：防止浏览器缓存流式响应。
- `Connection: "keep-alive"`：保持 HTTP 连接打开。
- `Transfer-Encoding: "chunked"`：启用分块传输编码。

### 1.4 异常处理策略

**核心原则**：必须在生成器（generator）内部捕获异常，而不是只在 View 函数外层捕获。

#### 1.4.1 为什么要在生成器内部捕获异常？

一旦流开始传输，HTTP 200 状态码已经发送给客户端。如果此时在生成器外部抛出异常，会导致：
- 前端连接直接断开（Network Error）
- 用户看到"连接中断"而不是友好的错误提示
- 无法优雅地处理错误

#### 1.4.2 正确的异常处理模式

```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.core.api import BusinessException, SystemException
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    流式对话接口
    
    支持 SSE (Server-Sent Events) 流式响应
    """
    try:
        async def generate():
            """生成器函数：在内部捕获异常"""
            try:
                async for chunk in chat_service.chat_stream(
                    query=request.query,
                    conversation_id=request.conversation_id,
                    user=request.user
                ):
                    # 发送服务器端事件格式的数据，立即刷新
                    data = f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    yield data
                    
            except BusinessException as e:
                # 业务异常：在流中发送错误事件
                error_chunk = {
                    "event": "error",
                    "data": {
                        "text": e.message,
                        "metadata": {}
                    },
                    "conversation_id": request.conversation_id or "",
                    "is_complete": True
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                # 系统异常：记录日志并发送错误事件
                logger.error(f"流式响应异常: {e}", exc_info=True)
                error_chunk = {
                    "event": "error",
                    "data": {
                        "text": "系统错误，请稍后重试",
                        "metadata": {}
                    },
                    "conversation_id": request.conversation_id or "",
                    "is_complete": True
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Transfer-Encoding": "chunked",
            }
        )
        
    except BusinessException:
        # 流启动前的业务异常直接抛出，由全局异常处理器处理
        raise
    except Exception as e:
        # 流启动前的系统异常转换为 SystemException
        logger.error(f"启动流式对话失败: {e}", exc_info=True)
        raise SystemException("启动流式对话失败")
```

#### 1.4.3 错误事件格式

错误事件必须遵循与正常事件相同的格式，前端才能统一处理：

```python
error_chunk = {
    "event": "error",  # 事件类型标识
    "data": {
        "text": "错误信息",  # 错误描述
        "metadata": {}  # 可选的错误详情
    },
    "conversation_id": request.conversation_id or "",
    "is_complete": True  # 标记流已结束
}
```

### 1.5 Service 层实现

Service 层负责实际的流式数据生成：

```python
class ChatService:
    def __init__(self, db: Session):
        self.db = db
    
    async def chat_stream(
        self,
        query: str,
        conversation_id: Optional[str],
        user: str
    ) -> AsyncIterator[StreamChatResponse]:
        """
        流式生成对话响应
        
        使用 async generator 逐步 yield 数据块
        """
        # 初始化对话
        conversation = await self._get_or_create_conversation(conversation_id, user)
        
        # 调用 AI 模型（示例：假设使用 OpenAI 或其他流式 API）
        async for chunk in self._call_ai_model_stream(query, conversation.id):
            # 转换并 yield 数据块
            yield StreamChatResponse(
                event="message",
                data=StreamChunkData(text=chunk.text),
                conversation_id=conversation.id,
                is_complete=False
            )
        
        # 流结束标记
        yield StreamChatResponse(
            event="finish",
            data=StreamChunkData(),
            conversation_id=conversation.id,
            is_complete=True
        )
```

### 1.6 流式缓冲区（StreamBuffer）模式

**核心问题**：在流式响应中，特殊标签（如 `<CAXAGroupTreeResult>...</CAXAGroupTreeResult>` 或 Dify 的 `<think>...</think>`、`<think>...</think>`）可能被分割到多个 chunk 中，导致无法正确解析和过滤。

**解决方案**：使用 `StreamBuffer` 类来缓冲和重组被分割的标签内容。

#### 1.6.1 StreamBuffer 实现

```python
from typing import Tuple, List
import json
import logging

logger = logging.getLogger(__name__)

class StreamBuffer:
    """流式缓冲区，用于处理被分割的特殊标签"""
    
    def __init__(self, tag_start: str = "<CAXAGroupTreeResult>", tag_end: str = "</CAXAGroupTreeResult>"):
        self.buffer = ""
        self.in_tag = False  # 是否正在标签内部
        self.tag_start = tag_start
        self.tag_end = tag_end
        self.tag_start_lower = tag_start.lower()
        self.tag_end_lower = tag_end.lower()
        
    def process(self, chunk: str) -> Tuple[str, List[dict]]:
        """
        处理新的文本块
        
        Returns:
            tuple: (safe_text, extracted_data_list)
            - safe_text: 可以安全发送给前端的文本（不包含完整或部分的标签）
            - extracted_data_list: 从完整标签中提取的JSON数据列表
        """
        self.buffer += chunk
        text_to_yield = ""
        found_jsons = []
        
        while True:
            # Case 1: 正在录制标签内容
            if self.in_tag:
                # 查找结束标签
                end_idx = self.buffer.lower().find(self.tag_end_lower)
                if end_idx != -1:
                    # 找到结束标签，提取内容
                    json_content = self.buffer[:end_idx]
                    try:
                        json_content = json_content.strip()
                        if json_content:
                            data = json.loads(json_content)
                            found_jsons.append(data)
                            logger.info(f"[标签] 成功提取并解析 JSON 数据")
                    except json.JSONDecodeError as e:
                        logger.error(f"[标签] JSON 解析失败: {e}")
                    
                    # 移除内容和结束标签，重置状态
                    self.buffer = self.buffer[end_idx + len(self.tag_end):]
                    self.in_tag = False
                    continue
                else:
                    # 没找到结束标签，保留所有内容在缓冲区，等待更多数据
                    break
            
            # Case 2: 正常文本模式
            else:
                # 查找开始标签
                start_idx = self.buffer.lower().find(self.tag_start_lower)
                if start_idx != -1:
                    # 找到开始标签，标签前的内容是安全的
                    text_to_yield += self.buffer[:start_idx]
                    self.buffer = self.buffer[start_idx + len(self.tag_start):]
                    self.in_tag = True
                    continue
                else:
                    # 检查缓冲区末尾是否有被截断的开始标签
                    potential_start_idx = -1
                    search_pos = 0
                    while True:
                        idx = self.buffer.find('<', search_pos)
                        if idx == -1:
                            break
                        suffix = self.buffer[idx:]
                        if self.tag_start_lower.startswith(suffix.lower()):
                            potential_start_idx = idx
                            break
                        search_pos = idx + 1
                    
                    if potential_start_idx != -1:
                        # 发现潜在的标签头，将它之前的内容发送
                        text_to_yield += self.buffer[:potential_start_idx]
                        self.buffer = self.buffer[potential_start_idx:]
                        break
                    else:
                        # 没有任何潜在标签，全部发送
                        text_to_yield += self.buffer
                        self.buffer = ""
                        break
                        
        return text_to_yield, found_jsons

    def flush(self) -> str:
        """
        强制清空缓冲区（用于流结束时）
        如果仍在 in_tag 状态，说明标签未闭合，将原始内容作为文本返回
        """
        remaining = self.buffer
        if self.in_tag:
            # 如果流结束了还在标签内，补上开始标签让用户看到
            remaining = self.tag_start + remaining
            logger.warning("[标签] 流结束但标签未闭合")
        
        self.buffer = ""
        self.in_tag = False
        return remaining
```

#### 1.6.2 在 Service 中使用 StreamBuffer

```python
class ChatService:
    async def chat_stream(
        self,
        query: str,
        conversation_id: Optional[str],
        user: str
    ) -> AsyncGenerator[dict, None]:
        # 初始化流式缓冲区
        stream_buffer = StreamBuffer()
        full_content = ""
        
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:]
                data = json.loads(data_str)
                event = data.get("event")
                
                if event == "message" or event == "agent_message":
                    answer = data.get("answer", "")
                    if not answer:
                        continue
                    
                    # 使用 Buffer 处理 Chunk
                    safe_text, extracted_jsons = stream_buffer.process(answer)
                    
                    # 1. 发送安全的文本（过滤掉了标签）
                    if safe_text:
                        full_content += safe_text
                        yield {
                            "event": "agent_message",
                            "content": safe_text,
                            "full_content": full_content,
                            "conversation_id": conversation_id,
                            "is_complete": False
                        }
                    
                    # 2. 处理提取到的 JSON 数据（如 CAXA 装配数据）
                    if extracted_jsons:
                        for json_data in extracted_jsons:
                            # 触发后续处理逻辑（如模型装配）
                            await self._handle_extracted_data(json_data)
                
                elif event == "message_end":
                    # 结束事件前，先清空缓冲区
                    remaining_text = stream_buffer.flush()
                    if remaining_text:
                        full_content += remaining_text
                        yield {
                            "event": "agent_message",
                            "content": remaining_text,
                            "full_content": full_content,
                            "conversation_id": conversation_id,
                            "is_complete": False
                        }
                    
                    yield {
                        "event": "message_end",
                        "conversation_id": conversation_id,
                        "is_complete": True
                    }
```

#### 1.6.3 处理 Dify 的 `<think>` 和 `<think>` 标签

对于 Dify 的思考过程标签（如 `<think>...</think>` 或 `<think>...</think>`），可以使用类似的模式：

```python
class DifyStreamBuffer:
    """专门处理 Dify 的思考标签，支持多个标签类型"""
    
    def __init__(self):
        # 使用多个 StreamBuffer 实例分别处理不同的标签
        self.think_buffer = StreamBuffer(
            tag_start="<think>",
            tag_end="</think>"
        )
        self.reasoning_buffer = StreamBuffer(
            tag_start="<think>",
            tag_end="</think>"
        )
    
    def process(self, chunk: str) -> Tuple[str, List[str]]:
        """
        处理 chunk，过滤掉思考过程标签
        
        Returns:
            tuple: (safe_text, reasoning_texts)
            - safe_text: 过滤后的安全文本
            - reasoning_texts: 提取的思考过程（可选，用于调试）
        """
        # 先处理 think 标签
        safe_text, _ = self.think_buffer.process(chunk)
        
        # 再处理 reasoning 标签
        final_text, reasoning_list = self.reasoning_buffer.process(safe_text)
        
        return final_text, reasoning_list
    
    def flush(self) -> str:
        """清空所有缓冲区"""
        remaining1 = self.think_buffer.flush()
        remaining2 = self.reasoning_buffer.flush()
        return remaining1 + remaining2
```

**注意**：实际标签名称可能因 Dify 版本而异，请根据实际情况调整 `tag_start` 和 `tag_end`。

#### 1.6.4 StreamBuffer 的关键优势

1. **处理标签分割**：当标签被分割到多个 chunk 时，能够正确重组。
2. **状态管理**：通过 `in_tag` 标志跟踪当前是否在标签内部。
3. **边界检测**：智能检测被截断的标签开头，避免误判。
4. **流结束处理**：通过 `flush()` 方法处理流结束时未闭合的标签。
5. **多标签支持**：可以扩展支持多个不同的标签类型。

#### 1.6.5 使用场景

- **过滤敏感内容**：如 Dify 的 `<think>`、`<think>` 标签，不应显示给用户。
- **提取结构化数据**：如 `<CAXAGroupTreeResult>` 中的 JSON 数据，需要解析并触发后续流程。
- **清理历史消息**：在获取历史消息时，使用正则表达式清理已存储的标签内容。

---

## 二、前端实现标准（React/Next.js）

### 2.1 流式读取实现

#### 2.1.1 API 客户端实现

使用 `fetch` + `ReadableStream` 读取流式响应：

```typescript
class ApiClient {
  /**
   * 流式请求（SSE）
   * @param url 请求地址
   * @param body 请求体
   * @param onChunk 数据块回调
   * @param onError 错误回调
   * @param signal 可选的 AbortSignal，用于取消请求
   */
  async stream<T>(
    url: string,
    body?: unknown,
    onChunk?: (chunk: T) => void,
    onError?: (error: Error) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const fullUrl = `${this.baseUrl}${url}`
    
    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
        signal, // 支持取消请求
      })

      if (!response.ok) {
        throw new Error(`流式请求失败: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('无法获取响应流')
      }

      let buffer = ''

      while (true) {
        // 检查是否已取消
        if (signal?.aborted) {
          reader.cancel()
          break
        }

        const { done, value } = await reader.read()

        if (done) break

        // 解码并累积到缓冲区
        buffer += decoder.decode(value, { stream: true })
        
        // 按行分割（SSE 格式以 \n 分隔）
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''  // 保留最后不完整的行

        for (const line of lines) {
          // SSE 格式：data: <JSON>
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)  // 移除 "data: " 前缀
            if (dataStr.trim()) {
              try {
                const chunk = JSON.parse(dataStr) as T
                onChunk?.(chunk)
              } catch (e) {
                console.error('解析流式数据失败:', e, '原始数据:', dataStr)
              }
            }
          }
        }
      }
    } catch (error) {
      // 处理取消请求
      if (error instanceof Error && error.name === 'AbortError') {
        return
      }
      
      // 处理其他错误
      onError?.(error instanceof Error ? error : new Error('流式请求失败'))
      throw error
    }
  }
}
```

#### 2.1.2 关键实现细节

1. **缓冲区管理**：使用 `buffer` 变量累积不完整的行，避免数据截断。
2. **SSE 格式解析**：只处理以 `data: ` 开头的行，忽略其他 SSE 控制行（如 `event:`, `id:` 等）。
3. **错误处理**：区分取消请求（AbortError）和其他错误。
4. **取消支持**：通过 `AbortSignal` 支持取消正在进行的流式请求。

### 2.2 打字机效果实现

#### 2.2.1 状态管理

使用 React Hooks 管理流式消息状态：

```typescript
import { useState, useRef } from 'react'

function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streamingMessageId, setStreamingMessageId] = useState<string>()
  const streamingContentRef = useRef<string>('')  // 使用 ref 存储累加内容
  
  // ...
}
```

**为什么使用 `useRef` 而不是 `useState`？**

- `useRef` 不会触发重新渲染，适合存储累加内容。
- 每次接收到新 chunk 时，只需要更新一次 `messages` 状态，避免频繁渲染。

#### 2.2.2 流式消息处理

```typescript
const sendStreamChat = async (userContent: string) => {
  // 1. 添加用户消息
  const userMessage: ChatMessage = {
    id: Date.now().toString(),
    role: 'user',
    content: userContent,
    timestamp: new Date(),
  }
  setMessages((prev) => [...prev, userMessage])

  // 2. 创建 AI 消息占位符
  const aiMessageId = `ai-${Date.now()}`
  const aiMessage: ChatMessage = {
    id: aiMessageId,
    role: 'assistant',
    content: '',
    timestamp: new Date(),
  }
  setMessages((prev) => [...prev, aiMessage])
  setStreamingMessageId(aiMessageId)
  streamingContentRef.current = ''  // 重置累加内容

  try {
    await chatService.streamChat(
      request,
      (chunk: StreamChatResponse) => {
        // 3. 处理不同类型的流式事件
        
        if (chunk.event === 'message' || chunk.event === 'agent_message') {
          // 累加文本内容
          const textContent = chunk.data?.text
          if (textContent) {
            streamingContentRef.current += textContent
            
            // 更新消息内容，触发 UI 重绘
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === aiMessageId
                  ? { ...msg, content: streamingContentRef.current }
                  : msg
              )
            )
          }
        }

        if (chunk.event === 'finish' || chunk.event === 'message_end') {
          // 流式传输完成
          setStreamingMessageId(undefined)
        }

        if (chunk.event === 'error') {
          // 错误处理：显示错误信息
          setStreamingMessageId(undefined)
          const errorText = chunk.data?.text || '请求失败'
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === aiMessageId
                ? { ...msg, content: msg.content + '\n\n[错误] ' + errorText }
                : msg
            )
          )
        }
      },
      (error) => {
        // 网络错误或其他错误
        setStreamingMessageId(undefined)
        console.error('聊天请求失败:', error)
        // 显示错误提示
      }
    )
  } catch (error) {
    setStreamingMessageId(undefined)
    // 错误处理
  }
}
```

#### 2.2.3 优化建议

1. **防抖/节流**：如果后端发送频率过高，可以考虑对 UI 更新进行节流：

```typescript
import { throttle } from 'lodash'

const updateMessage = throttle((messageId: string, content: string) => {
  setMessages((prev) =>
    prev.map((msg) =>
      msg.id === messageId ? { ...msg, content } : msg
    )
  )
}, 50)  // 每 50ms 最多更新一次
```

2. **支持完整内容替换**：如果后端同时返回 `full_content`，优先使用：

```typescript
if (chunk.event === 'message') {
  const fullContent = (chunk as any).full_content
  const textContent = chunk.data?.text
  
  if (fullContent) {
    // 后端返回了完整内容，直接替换
    streamingContentRef.current = fullContent
  } else if (textContent) {
    // 否则累加增量内容
    streamingContentRef.current += textContent
  }
  
  setMessages((prev) =>
    prev.map((msg) =>
      msg.id === aiMessageId
        ? { ...msg, content: streamingContentRef.current }
        : msg
    )
  )
}
```

### 2.3 UI 渲染优化

#### 2.3.1 流式消息标识

在 UI 中标识正在流式传输的消息，可以显示加载动画或特殊样式：

```typescript
function ChatPanel({ messages, streamingMessageId }: Props) {
  return (
    <div className="chat-messages">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message ${message.role} ${
            message.id === streamingMessageId ? 'streaming' : ''
          }`}
        >
          <div className="content">{message.content}</div>
          {message.id === streamingMessageId && (
            <span className="streaming-indicator">▋</span>  // 打字机光标
          )}
        </div>
      ))}
    </div>
  )
}
```

#### 2.3.2 自动滚动

流式消息更新时，自动滚动到底部：

```typescript
import { useEffect, useRef } from 'react'

function ChatPanel({ messages, streamingMessageId }: Props) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // 当消息更新或流式消息 ID 变化时，滚动到底部
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingMessageId])

  return (
    <div className="chat-messages">
      {messages.map((message) => (
        <div key={message.id}>{message.content}</div>
      ))}
      <div ref={messagesEndRef} />  {/* 滚动锚点 */}
    </div>
  )
}
```

### 2.4 取消请求支持

支持用户取消正在进行的流式请求：

```typescript
const [abortController, setAbortController] = useState<AbortController>()

const sendStreamChat = async (userContent: string) => {
  // 创建新的 AbortController
  const controller = new AbortController()
  setAbortController(controller)

  try {
    await chatService.streamChat(
      request,
      onChunk,
      onError,
      controller.signal  // 传递 signal
    )
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.log('请求已取消')
    }
  } finally {
    setAbortController(undefined)
  }
}

// 取消请求
const cancelRequest = () => {
  abortController?.abort()
  setAbortController(undefined)
  setStreamingMessageId(undefined)
}
```

---

## 三、Nginx 配置（生产环境）

如果使用 Nginx 作为反向代理，必须配置以下参数以确保流式响应正常工作：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://backend:8000;
        
        # 关键配置：禁用缓冲
        proxy_buffering off;
        proxy_cache off;
        
        # 保持连接
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        
        # 流式响应超时设置
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        
        # CORS（如果需要）
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Headers "Content-Type";
    }
}
```

**关键配置说明**：

- `proxy_buffering off`：禁用 Nginx 缓冲，立即转发响应。
- `proxy_cache off`：禁用缓存。
- `proxy_http_version 1.1`：使用 HTTP/1.1 以支持分块传输。
- `proxy_read_timeout`：设置较长的读取超时（根据实际需求调整）。

---

## 四、常见问题与解决方案

### 4.1 问题：流式响应被缓冲，前端看起来像"卡顿"

**原因**：缺少 `X-Accel-Buffering: "no"` 响应头，或 Nginx 配置了缓冲。

**解决方案**：
1. 后端添加 `X-Accel-Buffering: "no"` 响应头。
2. Nginx 配置 `proxy_buffering off`。

### 4.2 问题：前端连接突然断开

**原因**：生成器内部抛出未捕获的异常。

**解决方案**：在生成器内部使用 `try-except` 捕获异常，并 yield 错误事件。

### 4.3 问题：前端解析 SSE 数据失败

**原因**：后端数据格式不符合 SSE 标准（缺少 `data: ` 前缀或 `\n\n` 后缀）。

**解决方案**：严格遵循 SSE 格式：`data: <JSON>\n\n`。

### 4.4 问题：打字机效果不流畅

**原因**：UI 更新频率过高，导致性能问题。

**解决方案**：
1. 使用 `useRef` 存储累加内容，减少状态更新。
2. 对 UI 更新进行节流（throttle）。

### 4.5 问题：流式响应超时

**原因**：Nginx 或后端超时设置过短。

**解决方案**：
1. Nginx 设置 `proxy_read_timeout 300s`。
2. 后端检查超时配置。

### 4.6 问题：特殊标签被分割，无法正确解析或过滤

**原因**：流式响应中，标签（如 `<CAXAGroupTreeResult>...</CAXAGroupTreeResult>` 或 Dify 的 `<think>...</think>`）可能被分割到多个 chunk 中，导致：
- 无法正确识别标签边界
- JSON 解析失败
- 敏感内容（如思考过程）泄露给前端

**解决方案**：使用 `StreamBuffer` 模式：
1. 维护一个缓冲区累积不完整的 chunk。
2. 使用状态标志（`in_tag`）跟踪是否在标签内部。
3. 智能检测被截断的标签开头。
4. 流结束时通过 `flush()` 处理未闭合的标签。

**示例场景**：
- Dify 返回：`chunk1="<think>", chunk2="思考内容", chunk3="</think>"`
- 不使用 StreamBuffer：无法识别完整标签，思考内容会泄露。
- 使用 StreamBuffer：正确识别并过滤，只发送安全文本。

---

## 五、最佳实践总结

### 5.1 后端最佳实践

1. ✅ **使用 SSE 标准**：严格遵循 `data: <JSON>\n\n` 格式。
2. ✅ **设置关键响应头**：特别是 `X-Accel-Buffering: "no"`。
3. ✅ **生成器内部异常处理**：在生成器内部捕获异常并 yield 错误事件。
4. ✅ **定义清晰的数据结构**：使用 Pydantic 模型定义流式响应格式。
5. ✅ **使用 StreamBuffer 处理标签分割**：当流式响应中包含特殊标签（如 `<think>`、`<CAXAGroupTreeResult>`）时，使用 `StreamBuffer` 正确处理被分割的标签，避免内容泄露和解析失败。
6. ✅ **日志记录**：记录流式响应过程中的关键信息。

### 5.2 前端最佳实践

1. ✅ **使用 ReadableStream**：通过 `fetch` + `ReadableStream` 读取流。
2. ✅ **缓冲区管理**：正确处理不完整的 SSE 行。
3. ✅ **使用 useRef 存储累加内容**：减少不必要的重新渲染。
4. ✅ **支持取消请求**：通过 `AbortSignal` 支持用户取消。
5. ✅ **错误处理**：区分网络错误、业务错误和取消请求。
6. ✅ **UI 优化**：自动滚动、流式消息标识、打字机光标。

### 5.3 部署最佳实践

1. ✅ **Nginx 配置**：禁用缓冲和缓存。
2. ✅ **超时设置**：设置合理的超时时间。
3. ✅ **监控和日志**：监控流式响应的成功率和错误率。

---

## 六、核心模式总结

### 6.1 后端核心模式

**流式接口模式**：
1. 使用 `StreamingResponse` 包装异步生成器
2. 设置关键响应头（特别是 `X-Accel-Buffering: "no"`）
3. 在生成器内部捕获异常并 yield 错误事件
4. 使用 `StreamBuffer` 处理被分割的特殊标签

**StreamBuffer 模式**：
1. 维护缓冲区累积不完整的 chunk
2. 使用状态标志跟踪标签边界
3. 智能检测被截断的标签开头
4. 流结束时清空缓冲区

### 6.2 前端核心模式

**流式读取模式**：
1. 使用 `fetch` + `ReadableStream` 读取流
2. 维护缓冲区处理不完整的 SSE 行
3. 解析 `data: <JSON>\n\n` 格式
4. 支持 `AbortSignal` 取消请求

**打字机效果模式**：
1. 使用 `useRef` 存储累加内容
2. 通过 `setState` 触发 UI 更新
3. 处理不同事件类型（message, error, finish）
4. 自动滚动和流式消息标识

---

## 七、总结

遵循本文档的最佳实践，可以确保：

- ✅ **流畅的用户体验**：打字机效果流畅自然
- ✅ **可靠的错误处理**：优雅处理各种异常情况
- ✅ **良好的性能**：避免不必要的重新渲染和网络开销
- ✅ **易于维护**：代码结构清晰，易于理解和扩展

**所有新代码必须遵循此规范，旧代码应逐步迁移。**

