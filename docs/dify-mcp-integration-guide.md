## Dify × AnmeiSmart MCP 集成指南（权威版）

本指南覆盖从传输协议、初始化与授权、工具发现与调用、权限与速率限制、安全到故障排除的完整实现细节。实现已与当前代码保持一致：SSE + JSON-RPC、OAuth 授权、sessionToken 会话化、工具参数 Schema 自动生成、会话级速率限制与审计日志脱敏等。

### 目标与适用场景

- 在 Dify 的 Agent/Workflow 中以 MCP 工具的方式访问 AnmeiSmart 系统资源。
- 按“工具分组/权限”对外暴露可用工具；不同分组可配置不同的访问边界。
- 采用 Provider 级 API Key 发起授权，转换为短期 sessionToken 用于后续所有交互。

---

## 架构概览

- 传输与发现

  TODO：
- 初始化与授权

  - 无/无效 API Key：`initialize` 返回 `authorization_required` 或 `reauthorization_required`，并携带 `authorization_url`
  - 有效 API Key：`initialize` 返回 `status=success` 并下发 `sessionToken`
  - OAuth 授权流程将 API Key 转换为短期 `sessionToken`（Redis 持久化，TTL 可配）
- 工具与权限

  - `tools/list`：返回当前会话分组可用工具，包含参数 `inputSchema`
  - `tools/call`：执行工具前做“分组内工具授权 + 速率限制”校验
- 安全与审计

  - API Key 加密存储 + SHA-256 哈希匹配查询
  - 会话级限流（按方法+工具名）
  - 调用日志脱敏 `apiKey/authorization/token/sessionToken`

---

## 端点与协议

### 1) SSE 发现端点

### 2) JSON-RPC 端点

---

## 授权与会话

### API Key → OAuth → sessionToken

1. Dify 读取 SSE `endpoint` 后调用 `initialize`
2. 若未提供或提供了无效 API Key：返回 `authorization_url`
3. 浏览器跳转授权页：
   - `GET /mcp/oauth/authorize?client_id=<dify>&redirect_uri=<cb>&state=<id>&response_type=code`
   - 用户选择“工具分组”并提交（`POST /mcp/oauth/authorize/submit`）
4. 服务器保存授权码映射（Redis，10 分钟 TTL），重定向至 `redirect_uri?code=...`
5. Dify 以 `code` 调 `/mcp/oauth/token` 换取 `access_token`
   - 这里 `access_token` 直接为 `sessionToken`
6. 后续所有 `tools/*` 请求携带 `sessionToken`

### 会话存储（Redis）

- Key: `mcp:session:<sessionToken>`
- Value: `{ group_id, group_name, client, allowed_tools }`
- TTL: `MCP_SESSION_TTL_SECONDS`（默认 3600s，可配）

---

## 工具列表与参数 Schema

### tools/list

- 入参：`{ sessionToken }`
- 返回：当前分组可用工具列表
- 每个工具含 `inputSchema`（依据注册函数签名自动生成）：
  - 基本类型映射：`str→string`、`int→integer`、`bool→boolean`、`float→number`、`list→array`、`dict→object`
  - 必填项：无默认值的参数 → `required`
  - 默认值：填充到 `properties.<param>.default`
  - 复杂类型：如 `list[str]`、`dict[str, any]` 将在后续版本逐步增强（当前以基础类型表示）

### tools/call

- 入参：`{ name, arguments, sessionToken }`
- 返回：
  - 若工具返回结构化结果（dict/list）：`content` 同时包含：
    - `{ type: "json", json: <original> }`
    - `{ type: "text", text: <json.dumps> }`
  - 否则仅返回 `{ type: "text" }`

---

## 速率限制与错误

### 会话级限流（Redis）

- 维度：`group_id + sessionToken + method + tool_name + window`
- 窗口：`MCP_RL_WINDOW_SECONDS`（默认 60s）
- 配额：
  - `tools/list` → `MCP_RL_LIST_LIMIT`（默认 120）
  - `tools/call` → `MCP_RL_CALL_LIMIT`（默认 240）
- 超额行为：
  - 中间件直接返回 `429` 或 JSON-RPC 错误对象（由调用堆栈决定）

### 常见错误码

- `401` Missing Authorization header
- `403` Invalid API Key or OAuth Token
- `429` Rate limit exceeded
- JSON-RPC 错误：
  - `-32602` Authentication required / 参数错误
  - `-32601` Method not found
  - `-32700` Parse error
  - `-32603` Internal error

---

## 安全与合规

- API Key 安全存储：
  - 列：`mcp_tool_groups.api_key`（加密）、`hashed_api_key`（SHA-256，查询用）
  - 迁移：已添加列与索引，提供一次性回填脚本
- 会话安全：
  - `sessionToken` 仅存 Redis，短期有效，可吊销
- 日志脱敏：
  - `Authorization/apiKey/token/sessionToken` 统一掩码

---

## 配置与环境变量

核心配置（均可通过环境变量覆盖）：

```
MCP_PROTOCOL_VERSION=2024-11-05
MCP_SERVER_NAME="AnmeiSmart MCP Server"
MCP_SERVER_IDENTIFIER="anmeismart-mcp-server"
MCP_AUTH_BASE_URL="http://host.docker.internal:8000/mcp/oauth/authorize"
MCP_OAUTH_REDIRECT_URI="http://localhost/console/api/workspaces/current/tool-provider/mcp/oauth/callback"
MCP_SESSION_TTL_SECONDS=3600

MCP_RL_ENABLED=true
MCP_RL_WINDOW_SECONDS=60
MCP_RL_LIST_LIMIT=120
MCP_RL_CALL_LIMIT=240

REDIS_URL=redis://<user>:<password>@<host>:<port>/<db>
DATABASE_URL=postgresql+psycopg2://...
```

Dify 侧连接：

- Server URL: `http://<host>:8000/mcp/v1/sse`
- Protocol: SSE + JSON-RPC（SSE 用于发现端点与心跳，RPC 用于交互）
- 初始化时按提示完成授权（输入 API Key → 换取 sessionToken）

---

## 故障排除（精选）

- 初始化总返回 `authorization_required`：确认分组 API Key 是否正确、未过期，或直接走授权 URL 获取 sessionToken。
- `Authentication required`：`tools/*` 必须带 `sessionToken`，检查请求体 `params.sessionToken`。
- SSE 没有 `endpoint` 事件：核对 `GET /api/v1/mcp/jsonrpc` 请求头与服务实现；确保 Content-Type 与事件格式正确。
- Redis 未连接：检查 `REDIS_URL`，确保网络与鉴权可用。
- Alembic 多 head：已提供合并迁移；若再次出现，执行 `alembic heads` 与 `alembic merge` 处理。
- sessionToken 过期：重新初始化或走授权 URL 刷新会话。

🛠️ 可用工具（9个）

- **用户管理** (user)：
  - `get_user_profile` - 获取用户资料
  - `search_users` - 搜索用户
- **客户分析** (customer)：
  - `analyze_customer` - 客户分析
  - `get_customer_preferences` - 获取客户偏好
- **咨询服务** (consultation)：
  - `get_consultation_history` - 获取咨询历史
  - `create_consultation_summary` - 创建咨询总结
- **治疗方案** (treatment)：
  - `generate_treatment_plan` - 生成治疗方案
  - `optimize_plan` - 优化方案
- **项目管理** (projects)：
  - `get_service_info` - 获取服务信息

## Dify 配置步骤

### 1. 在 Dify 中配置 MCP Server

在 Dify 管理界面中配置：

#### 基本配置：

- **服务端点 URL**: `http://host.docker.internal:8000/api/v1/mcp/jsonrpc`
- **服务器标识符**: `anmeismart-mcp-server`
- **名称**: `AnmeiSmart MCP Server`
- **描述**: `医美智能助手工具集`

> 📋 **重要**：不需要预先输入 API Key，Dify 会在需要时自动引导您完成授权流程！

### 2. 自动授权流程 🚀

#### 第一次配置时：

1. **Dify 自动检测**：Dify 会调用 `initialize` 方法检测服务器
2. **弹出授权窗口**：系统会自动打开美观的授权界面
3. **输入 API 密钥**：在弹出窗口中输入您的 AnmeiSmart API 密钥
4. **完成授权**：验证成功后自动关闭窗口并完成配置

#### API 密钥获取步骤：

当授权窗口弹出时，您可以：

1. 访问 AnmeiSmart 管理后台：`http://localhost:3000/settings`
2. 进入 **MCP配置面板**
3. 创建新的 MCP 分组（如果还没有）
4. 点击 **复制** 按钮获取 API 密钥
5. 返回授权窗口并输入 API 密钥

### 3. 授权状态管理

#### 自动重新授权：

- **API 密钥过期**：系统会自动检测并弹出重新授权窗口
- **密钥无效**：会显示错误提示并允许重新输入
- **会话保持**：授权成功后会保持会话状态，无需重复输入

#### 验证连接成功：

配置完成后，Dify 会显示：

- ✅ 连接状态：正常
- 📊 可用工具：9个工具，5个分类
- 🔐 授权状态：已授权（显示分组名称）
