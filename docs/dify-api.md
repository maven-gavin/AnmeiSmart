# Dify Advanced Chat App API 文档

Chat applications support session persistence, allowing previous chat history to be used as context for responses. This can be applicable for chatbot, customer service AI, etc.

## 目录

- [基础信息](#基础信息)
  - [Base URL](#base-url)
  - [认证](#认证)
- [消息相关 API](#消息相关-api)
  - [发送聊天消息](#发送聊天消息)
  - [停止生成](#停止生成)
  - [获取会话历史消息](#获取会话历史消息)
  - [获取建议问题](#获取建议问题)
  - [消息反馈](#消息反馈)
  - [获取应用反馈列表](#获取应用反馈列表)
- [会话相关 API](#会话相关-api)
  - [获取会话列表](#获取会话列表)
  - [删除会话](#删除会话)
  - [重命名会话](#重命名会话)
  - [获取会话变量](#获取会话变量)
- [文件相关 API](#文件相关-api)
  - [文件上传](#文件上传)
- [语音相关 API](#语音相关-api)
  - [语音转文字](#语音转文字)
  - [文字转语音](#文字转语音)
- [应用信息 API](#应用信息-api)
  - [获取应用基本信息](#获取应用基本信息)
  - [获取应用参数信息](#获取应用参数信息)
  - [获取应用元信息](#获取应用元信息)
  - [获取应用 WebApp 设置](#获取应用-webapp-设置)
- [标注相关 API](#标注相关-api)
  - [获取标注列表](#获取标注列表)
  - [创建标注](#创建标注)
  - [更新标注](#更新标注)
  - [删除标注](#删除标注)
  - [初始化标注回复设置](#初始化标注回复设置)
  - [查询标注回复设置任务状态](#查询标注回复设置任务状态)

---

## 基础信息

### Base URL

```
http://localhost/v1
```

### 认证

Service API 使用 API-Key 认证。强烈建议将 API Key 存储在服务端，不要共享或存储在客户端，以避免 API Key 泄露导致严重后果。

所有 API 请求都需要在 HTTP Header 中包含 API Key：

```
Authorization: Bearer {API_KEY}
```

---

## 消息相关 API

### 发送聊天消息

**POST** `/chat-messages`

发送请求到聊天应用。

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `query` | string | 是 | 用户输入/问题内容 |
| `inputs` | object | 否 | 应用定义的各种变量值。inputs 参数包含多个键值对，每个键对应一个特定变量，每个值是该变量的具体值。如果变量是文件类型，需要指定一个包含以下 files 中描述的键的对象。默认值：`{}` |
| `response_mode` | string | 否 | 响应返回模式：<br>- `streaming`：流式模式（推荐），通过 SSE（Server-Sent Events）实现打字机式输出<br>- `blocking`：阻塞模式，执行完成后返回结果（如果过程较长，请求可能会被中断）。由于 Cloudflare 限制，请求将在 100 秒后中断且无返回 |
| `user` | string | 是 | 用户标识符，用于定义终端用户的身份以进行检索和统计。应在应用程序内由开发者唯一定义。Service API 不共享由 WebApp 创建的对话 |
| `conversation_id` | string | 否 | 会话 ID，要基于之前的聊天记录继续对话，需要传递之前消息的 `conversation_id` |
| `files` | array[object] | 否 | 文件列表，适用于结合文本理解和问答输入文件，仅在模型支持 Vision 能力时可用。文件对象包含：<br>- `type` (string)：支持的类型：<br>  - `document`: 'TXT', 'MD', 'MARKDOWN', 'PDF', 'HTML', 'XLSX', 'XLS', 'DOCX', 'CSV', 'EML', 'MSG', 'PPTX', 'PPT', 'XML', 'EPUB'<br>  - `image`: 'JPG', 'JPEG', 'PNG', 'GIF', 'WEBP', 'SVG'<br>  - `audio`: 'MP3', 'M4A', 'WAV', 'WEBM', 'AMR'<br>  - `video`: 'MP4', 'MOV', 'MPEG', 'MPGA'<br>  - `custom`: 其他文件类型<br>- `transfer_method` (string)：传输方式，`remote_url` 用于图片 URL，`local_file` 用于文件上传<br>- `url` (string)：图片 URL（当传输方式为 `remote_url` 时）<br>- `upload_file_id` (string)：已上传的文件 ID，必须通过文件上传 API 预先上传获得（当传输方式为 `local_file` 时） |
| `auto_generate_name` | bool | 否 | 自动生成标题，默认为 `true`。如果设置为 `false`，可以通过调用会话重命名 API 并设置 `auto_generate` 为 `true` 来实现异步标题生成 |

#### 响应

当 `response_mode` 为 `blocking` 时，返回 `ChatCompletionResponse` 对象。当 `response_mode` 为 `streaming` 时，返回 `ChunkChatCompletionResponse` 流。

##### ChatCompletionResponse

返回完整的应用结果，Content-Type 为 `application/json`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `event` | string | 事件类型，固定为 `message` |
| `task_id` | string | 任务 ID，用于请求跟踪和停止生成 API |
| `id` | string | 唯一 ID |
| `message_id` | string | 唯一消息 ID |
| `conversation_id` | string | 会话 ID |
| `mode` | string | 应用模式，固定为 `chat` |
| `answer` | string | 完整响应内容 |
| `metadata` | object | 元数据 |
| `metadata.usage` | Usage | 模型使用信息 |
| `metadata.retriever_resources` | array[RetrieverResource] | 引用和归属列表 |
| `created_at` | int | 消息创建时间戳，例如：1705395332 |

##### ChunkChatCompletionResponse

返回应用输出的流式数据块，Content-Type 为 `text/event-stream`。每个流式数据块以 `data:` 开头，由两个换行符 `\n\n` 分隔。

流式数据块的结构根据事件类型而变化：

**event: message** - LLM 返回文本块事件，即完整文本以分块方式输出
- `task_id` (string): 任务 ID
- `message_id` (string): 唯一消息 ID
- `conversation_id` (string): 会话 ID
- `answer` (string): LLM 返回的文本块内容
- `created_at` (int): 创建时间戳

**event: message_file** - 消息文件事件，工具创建了新文件
- `id` (string): 文件唯一 ID
- `type` (string): 文件类型，目前仅允许 "image"
- `belongs_to` (string): 归属，这里只会是 'assistant'
- `url` (string): 文件的远程 URL
- `conversation_id` (string): 会话 ID

**event: message_end** - 消息结束事件，接收此事件表示流式传输已结束
- `task_id` (string): 任务 ID
- `message_id` (string): 唯一消息 ID
- `conversation_id` (string): 会话 ID
- `metadata` (object): 元数据
- `metadata.usage` (Usage): 模型使用信息
- `metadata.retriever_resources` (array[RetrieverResource]): 引用和归属列表

**event: tts_message** - TTS 音频流事件，即语音合成输出。内容为 Mp3 格式的音频块，编码为 base64 字符串。播放时，只需解码 base64 并输入播放器（仅在启用自动播放时可用）
- `task_id` (string): 任务 ID
- `message_id` (string): 唯一消息 ID
- `audio` (string): 语音合成后的音频，编码为 base64 文本内容
- `created_at` (int): 创建时间戳

**event: tts_message_end** - TTS 音频流结束事件，接收此事件表示音频流已结束
- `task_id` (string): 任务 ID
- `message_id` (string): 唯一消息 ID
- `audio` (string): 结束事件没有音频，因此为空字符串
- `created_at` (int): 创建时间戳

**event: message_replace** - 消息内容替换事件。当启用输出内容审核时，如果内容被标记，则通过此事件将消息内容替换为预设回复
- `task_id` (string): 任务 ID
- `message_id` (string): 唯一消息 ID
- `conversation_id` (string): 会话 ID
- `answer` (string): 替换内容（直接替换所有 LLM 回复文本）
- `created_at` (int): 创建时间戳

**event: workflow_started** - 工作流开始执行
- `task_id` (string): 任务 ID
- `workflow_run_id` (string): 工作流执行的唯一 ID
- `event` (string): 固定为 `workflow_started`
- `data` (object): 详细信息
  - `id` (string): 工作流执行的唯一 ID
  - `workflow_id` (string): 相关工作流的 ID
  - `created_at` (timestamp): 创建时间戳

**event: node_started** - 节点执行开始
- `task_id` (string): 任务 ID
- `workflow_run_id` (string): 工作流执行的唯一 ID
- `event` (string): 固定为 `node_started`
- `data` (object): 详细信息
  - `id` (string): 工作流执行的唯一 ID
  - `node_id` (string): 节点 ID
  - `node_type` (string): 节点类型
  - `title` (string): 节点名称
  - `index` (int): 执行序号，用于显示追踪节点序列
  - `predecessor_node_id` (string, 可选): 前置节点 ID，用于画布显示执行路径
  - `inputs` (object): 节点中使用的所有前置节点变量的内容
  - `created_at` (timestamp): 开始时间戳

**event: node_finished** - 节点执行结束，成功或失败在同一事件的不同状态中
- `task_id` (string): 任务 ID
- `workflow_run_id` (string): 工作流执行的唯一 ID
- `event` (string): 固定为 `node_finished`
- `data` (object): 详细信息
  - `id` (string): 工作流执行的唯一 ID
  - `node_id` (string): 节点 ID
  - `node_type` (string): 节点类型
  - `title` (string): 节点名称
  - `index` (int): 执行序号
  - `predecessor_node_id` (string, 可选): 前置节点 ID
  - `inputs` (object): 节点中使用的所有前置节点变量的内容
  - `process_data` (json, 可选): 节点处理数据
  - `outputs` (json, 可选): 输出内容
  - `status` (string): 执行状态，`running` / `succeeded` / `failed` / `stopped`
  - `error` (string, 可选): 错误原因
  - `elapsed_time` (float, 可选): 使用的总秒数
  - `execution_metadata` (json): 元数据
  - `total_tokens` (int, 可选): 使用的 tokens
  - `total_price` (decimal, 可选): 总成本
  - `currency` (string, 可选): 货币，例如 USD / RMB
  - `created_at` (timestamp): 开始时间戳

**event: workflow_finished** - 工作流执行结束，成功或失败在同一事件的不同状态中
- `task_id` (string): 任务 ID
- `workflow_run_id` (string): 工作流执行的唯一 ID
- `event` (string): 固定为 `workflow_finished`
- `data` (object): 详细信息
  - `id` (string): 工作流执行的 ID
  - `workflow_id` (string): 相关工作流的 ID
  - `status` (string): 执行状态，`running` / `succeeded` / `failed` / `stopped`
  - `outputs` (json, 可选): 输出内容
  - `error` (string, 可选): 错误原因
  - `elapsed_time` (float, 可选): 使用的总秒数
  - `total_tokens` (int, 可选): 使用的 tokens
  - `total_steps` (int): 默认 0
  - `created_at` (timestamp): 开始时间
  - `finished_at` (timestamp): 结束时间

**event: error** - 流式处理过程中发生的异常将以流事件的形式输出，接收错误事件将结束流
- `task_id` (string): 任务 ID
- `message_id` (string): 唯一消息 ID
- `status` (int): HTTP 状态码
- `code` (string): 错误代码
- `message` (string): 错误消息

**event: ping** - 每 10 秒发送一次 ping 事件以保持连接活跃

#### 错误码

| HTTP 状态码 | 错误代码 | 说明 |
|------------|---------|------|
| 404 | - | 会话不存在 |
| 400 | `invalid_param` | 参数输入异常 |
| 400 | `app_unavailable` | 应用配置不可用 |
| 400 | `provider_not_initialize` | 没有可用的模型凭证配置 |
| 400 | `provider_quota_exceeded` | 模型调用配额不足 |
| 400 | `model_currently_not_support` | 当前模型不可用 |
| 400 | `completion_request_error` | 文本生成失败 |
| 500 | - | 内部服务器错误 |

#### 请求示例

```bash
curl -X POST 'http://localhost/v1/chat-messages' \
  --header 'Authorization: Bearer {api_key}' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "inputs": {},
    "query": "What are the specs of the iPhone 13 Pro Max?",
    "response_mode": "streaming",
    "conversation_id": "",
    "user": "abc-123",
    "files": [
      {
        "type": "image",
        "transfer_method": "remote_url",
        "url": "https://cloud.dify.ai/logo/logo-site.png"
      }
    ]
  }'
```

#### 响应示例

**阻塞模式响应：**

```json
{
  "event": "message",
  "task_id": "c3800678-a077-43df-a102-53f23ed20b88",
  "id": "9da23599-e713-473b-982c-4328d4f5c78a",
  "message_id": "9da23599-e713-473b-982c-4328d4f5c78a",
  "conversation_id": "45701982-8118-4bc5-8e9b-64562b4555f2",
  "mode": "chat",
  "answer": "iPhone 13 Pro Max specs are listed here:...",
  "metadata": {
    "usage": {
      "prompt_tokens": 1033,
      "prompt_unit_price": "0.001",
      "prompt_price_unit": "0.001",
      "prompt_price": "0.0010330",
      "completion_tokens": 128,
      "completion_unit_price": "0.002",
      "completion_price_unit": "0.001",
      "completion_price": "0.0002560",
      "total_tokens": 1161,
      "total_price": "0.0012890",
      "currency": "USD",
      "latency": 0.7682376249867957
    },
    "retriever_resources": [
      {
        "position": 1,
        "dataset_id": "101b4c97-fc2e-463c-90b1-5261a4cdcafb",
        "dataset_name": "iPhone",
        "document_id": "8dd1ad74-0b5f-4175-b735-7d98bbbb4e00",
        "document_name": "iPhone List",
        "segment_id": "ed599c7f-2766-4294-9d1d-e5235a61270a",
        "score": 0.98457545,
        "content": "\"Model\",\"Release Date\",\"Display Size\",\"Resolution\",\"Processor\",\"RAM\",\"Storage\",\"Camera\",\"Battery\",\"Operating System\"\n\"iPhone 13 Pro Max\",\"September 24, 2021\",\"6.7 inch\",\"1284 x 2778\",\"Hexa-core (2x3.23 GHz Avalanche + 4x1.82 GHz Blizzard)\",\"6 GB\",\"128, 256, 512 GB, 1TB\",\"12 MP\",\"4352 mAh\",\"iOS 15\""
      }
    ]
  },
  "created_at": 1705407629
}
```

**流式模式响应：**

```
data: {"event": "workflow_started", "task_id": "5ad4cb98-f0c7-4085-b384-88c403be6290", "workflow_run_id": "5ad498-f0c7-4085-b384-88cbe6290", "data": {"id": "5ad498-f0c7-4085-b384-88cbe6290", "workflow_id": "dfjasklfjdslag", "created_at": 1679586595}}

data: {"event": "node_started", "task_id": "5ad4cb98-f0c7-4085-b384-88c403be6290", "workflow_run_id": "5ad498-f0c7-4085-b384-88cbe6290", "data": {"id": "5ad498-f0c7-4085-b384-88cbe6290", "node_id": "dfjasklfjdslag", "node_type": "start", "title": "Start", "index": 0, "predecessor_node_id": "fdljewklfklgejlglsd", "inputs": {}, "created_at": 1679586595}}

data: {"event": "node_finished", "task_id": "5ad4cb98-f0c7-4085-b384-88c403be6290", "workflow_run_id": "5ad498-f0c7-4085-b384-88cbe6290", "data": {"id": "5ad498-f0c7-4085-b384-88cbe6290", "node_id": "dfjasklfjdslag", "node_type": "start", "title": "Start", "index": 0, "predecessor_node_id": "fdljewklfklgejlglsd", "inputs": {}, "outputs": {}, "status": "succeeded", "elapsed_time": 0.324, "execution_metadata": {"total_tokens": 63127864, "total_price": 2.378, "currency": "USD"}, "created_at": 1679586595}}

data: {"event": "workflow_finished", "task_id": "5ad4cb98-f0c7-4085-b384-88c403be6290", "workflow_run_id": "5ad498-f0c7-4085-b384-88cbe6290", "data": {"id": "5ad498-f0c7-4085-b384-88cbe6290", "workflow_id": "dfjasklfjdslag", "outputs": {}, "status": "succeeded", "elapsed_time": 0.324, "total_tokens": 63127864, "total_steps": "1", "created_at": 1679586595, "finished_at": 1679976595}}

data: {"event": "message", "message_id": "5ad4cb98-f0c7-4085-b384-88c403be6290", "conversation_id": "45701982-8118-4bc5-8e9b-64562b4555f2", "answer": " I", "created_at": 1679586595}

data: {"event": "message", "message_id": "5ad4cb98-f0c7-4085-b384-88c403be6290", "conversation_id": "45701982-8118-4bc5-8e9b-64562b4555f2", "answer": "'m", "created_at": 1679586595}

data: {"event": "message", "message_id": "5ad4cb98-f0c7-4085-b384-88c403be6290", "conversation_id": "45701982-8118-4bc5-8e9b-64562b4555f2", "answer": " glad", "created_at": 1679586595}

data: {"event": "message", "message_id": "5ad4cb98-f0c7-4085-b384-88c403be6290", "conversation_id": "45701982-8118-4bc5-8e9b-64562b4555f2", "answer": " to", "created_at": 1679586595}

data: {"event": "message", "message_id": "5ad4cb98-f0c7-4085-b384-88c403be6290", "conversation_id": "45701982-8118-4bc5-8e9b-64562b4555f2", "answer": " meet", "created_at": 1679586595}

data: {"event": "message", "message_id": "5ad4cb98-f0c7-4085-b384-88c403be6290", "conversation_id": "45701982-8118-4bc5-8e9b-64562b4555f2", "answer": " you", "created_at": 1679586595}

data: {"event": "message_end", "id": "5e52ce04-874b-4d27-9045-b3bc80def685", "conversation_id": "45701982-8118-4bc5-8e9b-64562b4555f2", "metadata": {"usage": {"prompt_tokens": 1033, "prompt_unit_price": "0.001", "prompt_price_unit": "0.001", "prompt_price": "0.0010330", "completion_tokens": 135, "completion_unit_price": "0.002", "completion_price_unit": "0.001", "completion_price": "0.0002700", "total_tokens": 1168, "total_price": "0.0013030", "currency": "USD", "latency": 1.381760165997548}, "retriever_resources": [{"position": 1, "dataset_id": "101b4c97-fc2e-463c-90b1-5261a4cdcafb", "dataset_name": "iPhone", "document_id": "8dd1ad74-0b5f-4175-b735-7d98bbbb4e00", "document_name": "iPhone List", "segment_id": "ed599c7f-2766-4294-9d1d-e5235a61270a", "score": 0.98457545, "content": "\"Model\",\"Release Date\",\"Display Size\",\"Resolution\",\"Processor\",\"RAM\",\"Storage\",\"Camera\",\"Battery\",\"Operating System\"\n\"iPhone 13 Pro Max\",\"September 24, 2021\",\"6.7 inch\",\"1284 x 2778\",\"Hexa-core (2x3.23 GHz Avalanche + 4x1.82 GHz Blizzard)\",\"6 GB\",\"128, 256, 512 GB, 1TB\",\"12 MP\",\"4352 mAh\",\"iOS 15\""}]}}

data: {"event": "tts_message", "conversation_id": "23dd85f3-1a41-4ea0-b7a9-062734ccfaf9", "message_id": "a8bdc41c-13b2-4c18-bfd9-054b9803038c", "created_at": 1721205487, "task_id": "3bf8a0bb-e73b-4690-9e66-4e429bad8ee7", "audio": "qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"}

data: {"event": "tts_message_end", "conversation_id": "23dd85f3-1a41-4ea0-b7a9-062734ccfaf9", "message_id": "a8bdc41c-13b2-4c18-bfd9-054b9803038c", "created_at": 1721205487, "task_id": "3bf8a0bb-e73b-4690-9e66-4e429bad8ee7", "audio": ""}
```

---

### 停止生成

**POST** `/chat-messages/:task_id/stop`

仅支持流式模式。

#### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `task_id` | string | 任务 ID，可从流式数据块返回中获取 |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `user` | string | 是 | 用户标识符，用于定义终端用户的身份，必须与消息发送接口中传递的用户一致。Service API 不共享由 WebApp 创建的对话 |

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | 始终返回 "success" |

#### 请求示例

```bash
curl -X POST 'http://localhost/v1/chat-messages/:task_id/stop' \
  -H 'Authorization: Bearer {api_key}' \
  -H 'Content-Type: application/json' \
  --data-raw '{"user": "abc-123"}'
```

#### 响应示例

```json
{
  "result": "success"
}
```

---

### 获取会话历史消息

**GET** `/messages`

以滚动加载格式返回历史聊天记录，第一页返回最新的 `{limit}` 条消息，即按倒序排列。

#### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `conversation_id` | string | 是 | 会话 ID |
| `user` | string | 是 | 用户标识符，用于定义终端用户的身份以进行检索和统计。应在应用程序内由开发者唯一定义 |
| `first_id` | string | 否 | 当前页第一条聊天记录的 ID，默认为 null |
| `limit` | int | 否 | 一次请求返回多少条聊天历史消息，默认为 20 |

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `data` | array[object] | 消息列表 |
| `data[].id` | string | 消息 ID |
| `data[].conversation_id` | string | 会话 ID |
| `data[].inputs` | object | 用户输入参数 |
| `data[].query` | string | 用户输入/问题内容 |
| `data[].message_files` | array[object] | 消息文件 |
| `data[].message_files[].id` | string | ID |
| `data[].message_files[].type` | string | 文件类型，图片为 image |
| `data[].message_files[].url` | string | 预览图片 URL |
| `data[].message_files[].belongs_to` | string | 归属，user 或 assistant |
| `data[].answer` | string | 响应消息内容 |
| `data[].created_at` | timestamp | 创建时间戳 |
| `data[].feedback` | object | 反馈信息 |
| `data[].feedback.rating` | string | 点赞为 like / 点踩为 dislike |
| `data[].retriever_resources` | array[RetrieverResource] | 引用和归属列表 |
| `has_more` | bool | 是否有下一页 |
| `limit` | int | 返回的项目数，如果输入超过系统限制，返回系统限制数量 |

#### 请求示例

```bash
curl -X GET 'http://localhost/v1/messages?user=abc-123&conversation_id=' \
  --header 'Authorization: Bearer {api_key}'
```

#### 响应示例

```json
{
  "limit": 20,
  "has_more": false,
  "data": [
    {
      "id": "a076a87f-31e5-48dc-b452-0061adbbc922",
      "conversation_id": "cd78daf6-f9e4-4463-9ff2-54257230a0ce",
      "inputs": {
        "name": "dify"
      },
      "query": "iphone 13 pro",
      "answer": "The iPhone 13 Pro, released on September 24, 2021, features a 6.1-inch display with a resolution of 1170 x 2532. It is equipped with a Hexa-core (2x3.23 GHz Avalanche + 4x1.82 GHz Blizzard) processor, 6 GB of RAM, and offers storage options of 128 GB, 256 GB, 512 GB, and 1 TB. The camera is 12 MP, the battery capacity is 3095 mAh, and it runs on iOS 15.",
      "message_files": [],
      "feedback": null,
      "retriever_resources": [
        {
          "position": 1,
          "dataset_id": "101b4c97-fc2e-463c-90b1-5261a4cdcafb",
          "dataset_name": "iPhone",
          "document_id": "8dd1ad74-0b5f-4175-b735-7d98bbbb4e00",
          "document_name": "iPhone List",
          "segment_id": "ed599c7f-2766-4294-9d1d-e5235a61270a",
          "score": 0.98457545,
          "content": "\"Model\",\"Release Date\",\"Display Size\",\"Resolution\",\"Processor\",\"RAM\",\"Storage\",\"Camera\",\"Battery\",\"Operating System\"\n\"iPhone 13 Pro Max\",\"September 24, 2021\",\"6.7 inch\",\"1284 x 2778\",\"Hexa-core (2x3.23 GHz Avalanche + 4x1.82 GHz Blizzard)\",\"6 GB\",\"128, 256, 512 GB, 1TB\",\"12 MP\",\"4352 mAh\",\"iOS 15\""
        }
      ],
      "created_at": 1705569239
    }
  ]
}
```

---

### 获取建议问题

**GET** `/messages/{message_id}/suggested`

获取当前消息的下一个问题建议。

#### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `message_id` | string | 消息 ID |

#### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `user` | string | 是 | 用户标识符，用于定义终端用户的身份以进行检索和统计。应在应用程序内由开发者唯一定义 |

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | 固定为 "success" |
| `data` | array[string] | 建议问题列表 |

#### 请求示例

```bash
curl --location --request GET 'http://localhost/v1/messages/{message_id}/suggested?user=abc-123' \
  --header 'Authorization: Bearer ENTER-YOUR-SECRET-KEY' \
  --header 'Content-Type: application/json'
```

#### 响应示例

```json
{
  "result": "success",
  "data": [
    "a",
    "b",
    "c"
  ]
}
```

---

### 消息反馈

**POST** `/messages/:message_id/feedbacks`

终端用户可以提供反馈消息，帮助应用开发者优化预期输出。

#### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `message_id` | string | 消息 ID |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `rating` | string | 是 | 点赞为 like，点踩为 dislike，撤销点赞为 null |
| `user` | string | 是 | 用户标识符，由开发者规则定义，必须在应用程序内唯一。Service API 不共享由 WebApp 创建的对话 |
| `content` | string | 否 | 消息反馈的具体内容 |

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | 始终返回 "success" |

#### 请求示例

```bash
curl -X POST 'http://localhost/v1/messages/:message_id/feedbacks' \
  --header 'Authorization: Bearer {api_key}' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "rating": "like",
    "user": "abc-123",
    "content": "message feedback information"
  }'
```

#### 响应示例

```json
{
  "result": "success"
}
```

---

### 获取应用反馈列表

**GET** `/app/feedbacks`

获取应用的反馈列表。

#### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `page` | string | 否 | 页码，默认为 1 |
| `limit` | string | 否 | 每页记录数，默认为 20 |

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `data` | List | 应用反馈列表 |

#### 请求示例

```bash
curl -X GET 'http://localhost/v1/app/feedbacks?page=1&limit=20'
```

#### 响应示例

```json
{
  "data": [
    {
      "id": "8c0fbed8-e2f9-49ff-9f0e-15a35bdd0e25",
      "app_id": "f252d396-fe48-450e-94ec-e184218e7346",
      "conversation_id": "2397604b-9deb-430e-b285-4726e51fd62d",
      "message_id": "709c0b0f-0a96-4a4e-91a4-ec0889937b11",
      "rating": "like",
      "content": "message feedback information-3",
      "from_source": "user",
      "from_end_user_id": "74286412-9a1a-42c1-929c-01edb1d381d5",
      "from_account_id": null,
      "created_at": "2025-04-24T09:24:38",
      "updated_at": "2025-04-24T09:24:38"
    }
  ]
}
```

---

## 会话相关 API

### 获取会话列表

**GET** `/conversations`

检索当前用户的会话列表，默认返回最近的 20 条记录。

#### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `user` | string | 是 | 用户标识符，用于定义终端用户的身份以进行检索和统计。应在应用程序内由开发者唯一定义 |
| `last_id` | string | 否 | 当前页最后一条记录的 ID，默认为 null |
| `limit` | int | 否 | 一次请求返回多少条记录，默认为最近的 20 条。最大 100，最小 1 |
| `sort_by` | string | 否 | 排序字段，默认：`-updated_at`（按更新时间降序排列）<br>可用值：`created_at`, `-created_at`, `updated_at`, `-updated_at`<br>字段前的符号表示顺序或反向，"-" 表示反向顺序 |

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `data` | array[object] | 会话列表 |
| `data[].id` | string | 会话 ID |
| `data[].name` | string | 会话名称，默认由 LLM 生成 |
| `data[].inputs` | object | 用户输入参数 |
| `data[].status` | string | 会话状态 |
| `data[].introduction` | string | 介绍 |
| `data[].created_at` | timestamp | 创建时间戳 |
| `data[].updated_at` | timestamp | 更新时间戳 |
| `has_more` | bool | 是否有更多记录 |
| `limit` | int | 返回的条目数，如果输入超过系统限制，返回系统限制数量 |

#### 请求示例

```bash
curl -X GET 'http://localhost/v1/conversations?user=abc-123&last_id=&limit=20' \
  --header 'Authorization: Bearer {api_key}'
```

#### 响应示例

```json
{
  "limit": 20,
  "has_more": false,
  "data": [
    {
      "id": "10799fb8-64f7-4296-bbf7-b42bfbe0ae54",
      "name": "New chat",
      "inputs": {
        "book": "book",
        "myName": "Lucy"
      },
      "status": "normal",
      "created_at": 1679667915,
      "updated_at": 1679667915
    },
    {
      "id": "hSIhXBhNe8X1d8Et"
    }
  ]
}
```

---

### 删除会话

**DELETE** `/conversations/:conversation_id`

删除一个会话。

#### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `conversation_id` | string | 会话 ID |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `user` | string | 是 | 用户标识符，由开发者定义，必须确保在应用程序内唯一 |

#### 响应

HTTP 204 No Content

#### 请求示例

```bash
curl -X DELETE 'http://localhost/v1/conversations/:conversation_id' \
  --header 'Authorization: Bearer {api_key}' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "user": "abc-123"
  }'
```

---

### 重命名会话

**POST** `/conversations/:conversation_id/name`

重命名会话，会话名称用于支持多会话的客户端显示。

#### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `conversation_id` | string | 会话 ID |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `name` | string | 否 | 会话名称。如果 `auto_generate` 设置为 `true`，则可以省略此参数 |
| `auto_generate` | bool | 否 | 自动生成标题，默认为 `false` |
| `user` | string | 是 | 用户标识符，由开发者定义，必须确保在应用程序内唯一 |

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 会话 ID |
| `name` | string | 会话名称 |
| `inputs` | object | 用户输入参数 |
| `status` | string | 会话状态 |
| `introduction` | string | 介绍 |
| `created_at` | timestamp | 创建时间戳 |
| `updated_at` | timestamp | 更新时间戳 |

#### 请求示例

```bash
curl -X POST 'http://localhost/v1/conversations/:conversation_id/name' \
  --header 'Authorization: Bearer {api_key}' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "name": "",
    "auto_generate": true,
    "user": "abc-123"
  }'
```

#### 响应示例

```json
{
  "id": "cd78daf6-f9e4-4463-9ff2-54257230a0ce",
  "name": "Chat vs AI",
  "inputs": {},
  "status": "normal",
  "introduction": "",
  "created_at": 1705569238,
  "updated_at": 1705569238
}
```

---

### 获取会话变量

**GET** `/conversations/:conversation_id/variables`

从特定会话中检索变量。此端点对于提取在会话期间捕获的结构化数据很有用。

#### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `conversation_id` | string | 要检索变量的会话 ID |

#### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `user` | string | 是 | 用户标识符，由开发者定义，必须确保在应用程序内唯一 |
| `last_id` | string | 否 | 当前页最后一条记录的 ID，默认为 null |
| `limit` | int | 否 | 一次请求返回多少条记录，默认为最近的 20 条。最大 100，最小 1 |

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `limit` | int | 每页项目数 |
| `has_more` | bool | 是否有下一页 |
| `data` | array[object] | 变量列表 |
| `data[].id` | string | 变量 ID |
| `data[].name` | string | 变量名称 |
| `data[].value_type` | string | 变量类型（string, number, object 等） |
| `data[].value` | string | 变量值 |
| `data[].description` | string | 变量描述 |
| `data[].created_at` | int | 创建时间戳 |
| `data[].updated_at` | int | 最后更新时间戳 |

#### 错误码

| HTTP 状态码 | 错误代码 | 说明 |
|------------|---------|------|
| 404 | `conversation_not_exists` | 会话未找到 |

#### 请求示例

```bash
curl -X GET 'http://localhost/v1/conversations/{conversation_id}/variables?user=abc-123' \
  --header 'Authorization: Bearer {api_key}'
```

**带变量名过滤的请求：**

```bash
curl -X GET '${props.appDetail.api_base_url}/conversations/{conversation_id}/variables?user=abc-123&variable_name=customer_name' \
  --header 'Authorization: Bearer {api_key}'
```

#### 响应示例

```json
{
  "limit": 100,
  "has_more": false,
  "data": [
    {
      "id": "variable-uuid-1",
      "name": "customer_name",
      "value_type": "string",
      "value": "John Doe",
      "description": "Customer name extracted from the conversation",
      "created_at": 1650000000000,
      "updated_at": 1650000000000
    },
    {
      "id": "variable-uuid-2",
      "name": "order_details",
      "value_type": "json",
      "value": "{\"product\":\"Widget\",\"quantity\":5,\"price\":19.99}",
      "description": "Order details from the customer",
      "created_at": 1650000000000,
      "updated_at": 1650000000000
    }
  ]
}
```

---

## 文件相关 API

### 文件上传

**POST** `/files/upload`

上传文件以供发送消息时使用，支持图像和文本的多模态理解。支持应用程序支持的任何格式。上传的文件仅供当前终端用户使用。

#### 请求参数

此接口需要 `multipart/form-data` 请求。

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `file` | File | 是 | 要上传的文件 |
| `user` | string | 是 | 用户标识符，由开发者规则定义，必须在应用程序内唯一。Service API 不共享由 WebApp 创建的对话 |

#### 响应

上传成功后，服务器将返回文件的 ID 和相关信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | uuid | ID |
| `name` | string | 文件名 |
| `size` | int | 文件大小（字节） |
| `extension` | string | 文件扩展名 |
| `mime_type` | string | 文件 MIME 类型 |
| `created_by` | uuid | 终端用户 ID |
| `created_at` | timestamp | 创建时间戳 |

#### 错误码

| HTTP 状态码 | 错误代码 | 说明 |
|------------|---------|------|
| 400 | `no_file_uploaded` | 必须提供文件 |
| 400 | `too_many_files` | 目前只接受一个文件 |
| 400 | `unsupported_preview` | 文件不支持预览 |
| 400 | `unsupported_estimate` | 文件不支持估算 |
| 413 | `file_too_large` | 文件太大 |
| 415 | `unsupported_file_type` | 不支持的扩展名，目前只接受文档文件 |
| 503 | `s3_connection_failed` | 无法连接到 S3 服务 |
| 503 | `s3_permission_denied` | 没有上传文件到 S3 的权限 |
| 503 | `s3_file_too_large` | 文件超过 S3 大小限制 |
| 500 | - | 内部服务器错误 |

#### 请求示例

```bash
curl -X POST 'http://localhost/v1/files/upload' \
  --header 'Authorization: Bearer {api_key}' \
  --form 'file=@localfile;type=image/[png|jpeg|jpg|webp|gif]' \
  --form 'user=abc-123'
```

#### 响应示例

```json
{
  "id": "72fa9618-8f89-4a37-9b33-7e1178a24a67",
  "name": "example.png",
  "size": 1024,
  "extension": "png",
  "mime_type": "image/png",
  "created_by": "6ad1ab0a-73ff-4ac1-b9e4-cdb312f71f13",
  "created_at": 1577836800
}
```

---

## 语音相关 API

### 语音转文字

**POST** `/audio-to-text`

此接口需要 `multipart/form-data` 请求。

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `file` | file | 是 | 音频文件。支持的格式：['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']。文件大小限制：15MB |
| `user` | string | 是 | 用户标识符，由开发者规则定义，必须在应用程序内唯一 |

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | string | 输出文本 |

#### 请求示例

```bash
curl -X POST 'http://localhost/v1/audio-to-text' \
  --header 'Authorization: Bearer {api_key}' \
  --form 'file=@localfile;type=audio/[mp3|mp4|mpeg|mpga|m4a|wav|webm]'
```

#### 响应示例

```json
{
  "text": ""
}
```

---

### 文字转语音

**POST** `/text-to-audio`

文字转语音。

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `message_id` | str | 否 | 对于 Dify 生成的文本消息，直接传递生成的消息 ID。后端将使用消息 ID 查找相应内容并直接合成语音信息。如果同时提供 `message_id` 和 `text`，则优先使用 `message_id` |
| `text` | str | 否 | 语音生成内容 |
| `user` | string | 是 | 用户标识符，由开发者定义，必须确保在应用程序内唯一 |

#### 响应

响应头：
```
Content-Type: audio/wav
```

响应体为音频文件流。

#### 请求示例

```bash
curl -o text-to-audio.mp3 -X POST 'http://localhost/v1/text-to-audio' \
  --header 'Authorization: Bearer {api_key}' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "message_id": "5ad4cb98-f0c7-4085-b384-88c403be6290",
    "text": "Hello Dify",
    "user": "abc-123"
  }'
```

---

## 应用信息 API

### 获取应用基本信息

**GET** `/info`

用于获取此应用的基本信息。

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 应用名称 |
| `description` | string | 应用描述 |
| `tags` | array[string] | 应用标签 |
| `mode` | string | 应用模式 |
| `author_name` | string | 应用作者名称 |

#### 请求示例

```bash
curl -X GET 'http://localhost/v1/info' \
  -H 'Authorization: Bearer {api_key}'
```

#### 响应示例

```json
{
  "name": "My App",
  "description": "This is my app.",
  "tags": [
    "tag1",
    "tag2"
  ],
  "mode": "advanced-chat",
  "author_name": "Dify"
}
```

---

### 获取应用参数信息

**GET** `/parameters`

用于在进入页面开始时获取功能、输入参数名称、类型和默认值等信息。

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `opening_statement` | string | 开场白 |
| `suggested_questions` | array[string] | 开场建议问题列表 |
| `suggested_questions_after_answer` | object | 启用答案后的建议问题 |
| `suggested_questions_after_answer.enabled` | bool | 是否启用 |
| `speech_to_text` | object | 语音转文字 |
| `speech_to_text.enabled` | bool | 是否启用 |
| `text_to_speech` | object | 文字转语音 |
| `text_to_speech.enabled` | bool | 是否启用 |
| `text_to_speech.voice` | string | 语音类型 |
| `text_to_speech.language` | string | 语言 |
| `text_to_speech.autoPlay` | string | 自动播放，`enabled` 或 `disabled` |
| `retriever_resource` | object | 引用和归属 |
| `retriever_resource.enabled` | bool | 是否启用 |
| `annotation_reply` | object | 标注回复 |
| `annotation_reply.enabled` | bool | 是否启用 |
| `user_input_form` | array[object] | 用户输入表单配置 |
| `user_input_form[].text-input` | object | 文本输入控件 |
| `user_input_form[].text-input.label` | string | 变量显示标签名称 |
| `user_input_form[].text-input.variable` | string | 变量 ID |
| `user_input_form[].text-input.required` | bool | 是否必填 |
| `user_input_form[].text-input.default` | string | 默认值 |
| `user_input_form[].paragraph` | object | 段落文本输入控件 |
| `user_input_form[].paragraph.label` | string | 变量显示标签名称 |
| `user_input_form[].paragraph.variable` | string | 变量 ID |
| `user_input_form[].paragraph.required` | bool | 是否必填 |
| `user_input_form[].paragraph.default` | string | 默认值 |
| `user_input_form[].select` | object | 下拉控件 |
| `user_input_form[].select.label` | string | 变量显示标签名称 |
| `user_input_form[].select.variable` | string | 变量 ID |
| `user_input_form[].select.required` | bool | 是否必填 |
| `user_input_form[].select.default` | string | 默认值 |
| `user_input_form[].select.options` | array[string] | 选项值 |
| `file_upload` | object | 文件上传配置 |
| `file_upload.image` | object | 图片设置，目前仅支持图片类型：png, jpg, jpeg, webp, gif |
| `file_upload.image.enabled` | bool | 是否启用 |
| `file_upload.image.number_limits` | int | 图片数量限制，默认为 3 |
| `file_upload.image.transfer_methods` | array[string] | 传输方法列表，`remote_url`, `local_file`，必须选择一个 |
| `system_parameters` | object | 系统参数 |
| `system_parameters.file_size_limit` | int | 文档上传大小限制（MB） |
| `system_parameters.image_file_size_limit` | int | 图片文件上传大小限制（MB） |
| `system_parameters.audio_file_size_limit` | int | 音频文件上传大小限制（MB） |
| `system_parameters.video_file_size_limit` | int | 视频文件上传大小限制（MB） |

#### 请求示例

```bash
curl -X GET 'http://localhost/v1/parameters'
```

#### 响应示例

```json
{
  "opening_statement": "Hello!",
  "suggested_questions_after_answer": {
    "enabled": true
  },
  "speech_to_text": {
    "enabled": true
  },
  "text_to_speech": {
    "enabled": true,
    "voice": "sambert-zhinan-v1",
    "language": "zh-Hans",
    "autoPlay": "disabled"
  },
  "retriever_resource": {
    "enabled": true
  },
  "annotation_reply": {
    "enabled": true
  },
  "user_input_form": [
    {
      "paragraph": {
        "label": "Query",
        "variable": "query",
        "required": true,
        "default": ""
      }
    }
  ],
  "file_upload": {
    "image": {
      "enabled": false,
      "number_limits": 3,
      "detail": "high",
      "transfer_methods": [
        "remote_url",
        "local_file"
      ]
    }
  },
  "system_parameters": {
    "file_size_limit": 15,
    "image_file_size_limit": 10,
    "audio_file_size_limit": 50,
    "video_file_size_limit": 100
  }
}
```

---

### 获取应用元信息

**GET** `/meta`

用于获取此应用中工具的图标。

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `tool_icons` | object[string] | 工具图标 |
| `tool_icons.{tool_name}` | string\|object | 工具名称对应的图标 |
| `tool_icons.{tool_name}` (object) | object | 图标对象 |
| `tool_icons.{tool_name}.background` | string | 背景颜色（十六进制格式） |
| `tool_icons.{tool_name}.content` | string | emoji |
| `tool_icons.{tool_name}` (string) | string | 图标 URL |

#### 请求示例

```bash
curl -X GET 'http://localhost/v1/meta' \
  -H 'Authorization: Bearer {api_key}'
```

#### 响应示例

```json
{
  "tool_icons": {
    "dalle2": "https://cloud.dify.ai/console/api/workspaces/current/tool-provider/builtin/dalle/icon",
    "api_tool": {
      "background": "#252525",
      "content": "😁"
    }
  }
}
```

---

### 获取应用 WebApp 设置

**GET** `/site`

用于获取应用的 WebApp 设置。

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | WebApp 名称 |
| `chat_color_theme` | string | 聊天颜色主题（十六进制格式） |
| `chat_color_theme_inverted` | bool | 聊天颜色主题是否反转 |
| `icon_type` | string | 图标类型，`emoji` - emoji，`image` - 图片 |
| `icon` | string | 图标。如果是 emoji 类型，则为 emoji 符号；如果是 image 类型，则为图片 URL |
| `icon_background` | string | 背景颜色（十六进制格式） |
| `icon_url` | string | 图标 URL |
| `description` | string | 描述 |
| `copyright` | string | 版权信息 |
| `privacy_policy` | string | 隐私政策链接 |
| `custom_disclaimer` | string | 自定义免责声明 |
| `default_language` | string | 默认语言 |
| `show_workflow_steps` | bool | 是否显示工作流详情 |
| `use_icon_as_answer_icon` | bool | 是否用 WebApp 图标替换聊天中的 🤖 |

#### 请求示例

```bash
curl -X GET 'http://localhost/v1/site' \
  -H 'Authorization: Bearer {api_key}'
```

#### 响应示例

```json
{
  "title": "My App",
  "chat_color_theme": "#ff4a4a",
  "chat_color_theme_inverted": false,
  "icon_type": "emoji",
  "icon": "😄",
  "icon_background": "#FFEAD5",
  "icon_url": null,
  "description": "This is my app.",
  "copyright": "all rights reserved",
  "privacy_policy": "",
  "custom_disclaimer": "All generated by AI",
  "default_language": "en-US",
  "show_workflow_steps": false,
  "use_icon_as_answer_icon": false
}
```

---

## 标注相关 API

### 获取标注列表

**GET** `/apps/annotations`

#### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `page` | string | 否 | 页码 |
| `limit` | string | 否 | 返回的项目数，默认 20，范围 1-100 |

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `data` | array[object] | 标注列表 |
| `data[].id` | string | 标注 ID |
| `data[].question` | string | 问题 |
| `data[].answer` | string | 答案 |
| `data[].hit_count` | int | 命中次数 |
| `data[].created_at` | int | 创建时间戳 |
| `has_more` | bool | 是否有更多记录 |
| `limit` | int | 返回的项目数 |
| `total` | int | 总数 |
| `page` | int | 页码 |

#### 请求示例

```bash
curl --location --request GET 'undefined/apps/annotations?page=1&limit=20' \
  --header 'Authorization: Bearer {api_key}'
```

#### 响应示例

```json
{
  "data": [
    {
      "id": "69d48372-ad81-4c75-9c46-2ce197b4d402",
      "question": "What is your name?",
      "answer": "I am Dify.",
      "hit_count": 0,
      "created_at": 1735625869
    }
  ],
  "has_more": false,
  "limit": 20,
  "total": 1,
  "page": 1
}
```

---

### 创建标注

**POST** `/apps/annotations`

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `question` | string | 是 | 问题 |
| `answer` | string | 是 | 答案 |

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 标注 ID |
| `question` | string | 问题 |
| `answer` | string | 答案 |
| `hit_count` | int | 命中次数 |
| `created_at` | int | 创建时间戳 |

#### 请求示例

```bash
curl --location --request POST 'undefined/apps/annotations' \
  --header 'Authorization: Bearer {api_key}' \
  --header 'Content-Type: application/json' \
  --data-raw '{"question": "What is your name?","answer": "I am Dify."}'
```

#### 响应示例

```json
{
  "id": "69d48372-ad81-4c75-9c46-2ce197b4d402",
  "question": "What is your name?",
  "answer": "I am Dify.",
  "hit_count": 0,
  "created_at": 1735625869
}
```

---

### 更新标注

**PUT** `/apps/annotations/{annotation_id}`

#### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `annotation_id` | string | 标注 ID |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `question` | string | 是 | 问题 |
| `answer` | string | 是 | 答案 |

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 标注 ID |
| `question` | string | 问题 |
| `answer` | string | 答案 |
| `hit_count` | int | 命中次数 |
| `created_at` | int | 创建时间戳 |

#### 请求示例

```bash
curl --location --request PUT 'undefined/apps/annotations/{annotation_id}' \
  --header 'Authorization: Bearer {api_key}' \
  --header 'Content-Type: application/json' \
  --data-raw '{"question": "What is your name?","answer": "I am Dify."}'
```

#### 响应示例

```json
{
  "id": "69d48372-ad81-4c75-9c46-2ce197b4d402",
  "question": "What is your name?",
  "answer": "I am Dify.",
  "hit_count": 0,
  "created_at": 1735625869
}
```

---

### 删除标注

**DELETE** `/apps/annotations/{annotation_id}`

#### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `annotation_id` | string | 标注 ID |

#### 响应

HTTP 204 No Content

#### 请求示例

```bash
curl --location --request DELETE 'undefined/apps/annotations/{annotation_id}' \
  --header 'Authorization: Bearer {api_key}' \
  --header 'Content-Type: application/json'
```

---

### 初始化标注回复设置

**POST** `/apps/annotation-reply/{action}`

#### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `action` | string | 操作，只能是 'enable' 或 'disable' |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `embedding_provider_name` | string | 否 | 指定的嵌入模型提供商，必须先在系统中设置，对应于 provider 字段 |
| `embedding_model_name` | string | 否 | 指定的嵌入模型，对应于 model 字段 |
| `score_threshold` | number | 否 | 匹配标注回复的相似度阈值。只有分数高于此阈值的标注才会被召回 |

> **注意**：嵌入模型的提供商和模型名称可以通过以下接口获取：`v1/workspaces/current/models/model-types/text-embedding`。具体说明请参见：通过 API 维护知识库。使用的 Authorization 是 Dataset API Token。

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `job_id` | string | 任务 ID |
| `job_status` | string | 任务状态 |

> **注意**：此接口异步执行，因此会返回 `job_id`。您可以通过查询任务状态接口获取最终执行结果。

#### 请求示例

```bash
curl --location --request POST 'undefined/apps/annotation-reply/{action}' \
  --header 'Authorization: Bearer {api_key}' \
  --header 'Content-Type: application/json' \
  --data-raw '{"score_threshold": 0.9, "embedding_provider_name": "zhipu", "embedding_model_name": "embedding_3"}'
```

#### 响应示例

```json
{
  "job_id": "b15c8f68-1cf4-4877-bf21-ed7cf2011802",
  "job_status": "waiting"
}
```

---

### 查询标注回复设置任务状态

**GET** `/apps/annotation-reply/{action}/status/{job_id}`

#### 路径参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `action` | string | 操作，只能是 'enable' 或 'disable'，必须与初始化标注回复设置接口中的 action 相同 |
| `job_id` | string | 任务 ID，从初始化标注回复设置接口获取 |

#### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `job_id` | string | 任务 ID |
| `job_status` | string | 任务状态 |
| `error_msg` | string | 错误消息 |

#### 请求示例

```bash
curl --location --request GET 'undefined/apps/annotation-reply/{action}/status/{job_id}' \
  --header 'Authorization: Bearer {api_key}'
```

#### 响应示例

```json
{
  "job_id": "b15c8f68-1cf4-4877-bf21-ed7cf2011802",
  "job_status": "waiting",
  "error_msg": ""
}
```
