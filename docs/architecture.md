# AnmeiSmart 系统架构

> 表结构索引见 [database-design.md](./database-design.md)；专题见文末索引。

## 定位

**模块化单体**：本仓库包含业务 API、权限、会话、任务、MCP、AI Gateway / Agent 运行时、DataHub、实时通信，前后端均在本仓库内交付。

## 原则

1. 业务域拆分 `api/app/*`，路由在 `api/app/api.py` 聚合
2. 能力对外：MCP 工具协议；模型经 AI Gateway 统一路由
3. 实时双通道：**SSE** 流式对话；**WebSocket** 事件推送
4. JWT + RBAC；DataHub 重任务走独立 Worker

## 技术栈

| 层级 | 选型 |
|------|------|
| 前端 | Next.js、TypeScript、Tailwind、Shadcn |
| 后端 | FastAPI、SQLAlchemy、Alembic |
| 存储 | PostgreSQL 16 + pgvector、Redis 7、MinIO |
| AI | AI Gateway + LangGraph Agent 运行时 + RAG（pgvector） |
| 部署 | Docker Compose（postgres / redis / api / web） |

## 分层

```text
web ──HTTP/SSE/WS──▶ api (/api/v1)
                      ├── identity_access / chat / customer / tasks / ...
                      ├── ai (Gateway, Agent 运行时, RAG)
                      ├── mcp / datahub / websocket / common(files)
                      └── PostgreSQL / Redis / MinIO
```

## 后端模块

| 模块 | 前缀 | 职责 |
|------|------|------|
| identity_access | `/auth`, `/users`, `/roles`, … | 用户、租户、RBAC |
| chat | `/chat` | 会话与消息 |
| customer | `/customers` | 客户画像 |
| digital_humans | `/digital-humans` | 数字人 |
| tasks | `/tasks` | 任务治理 |
| ai | `/ai-gateway`, `/agent` | Gateway、Agent 流式对话、RAG |
| mcp | `/mcp`, `/oauth` | MCP 工具 |
| datahub | `/datahub` | 标准化行情/财务数据 |
| websocket | `/ws` | 实时广播 |
| common | `/files` | 文件上传 |

遗留：`api/app/channels/` 骨架在，路由未注册。

## 关键链路

| 场景 | 路径 |
|------|------|
| 流式对话 | 前端 SSE → `/agent/*` → Agent 运行时（LangGraph）→ LLM / MCP / RAG（见 `api/app/ai/`、`web/src/service/apiClient.ts`） |
| MCP 工具 | Client → `/mcp/server/{code}/mcp` → 鉴权 → `tools/call` |
| 实时推送 | WS `/ws` → Redis 广播（见 [WebSocket 文档](./websocket-broadcasting-architecture.md)） |
| DataHub | Worker → Provider → MinIO → `/datahub`（见 [DataHub 文档](./datahub-architecture-plan.md)） |
| 文件上传 | 前端 → `/files` → MinIO（见 [文件上传文档](./file-upload-readme.md)） |

## 非功能

- 错误码：[ERROR_HANDLING_STANDARD.md](./ERROR_HANDLING_STANDARD.md)
- 安全：敏感字段加密；生产 HTTPS/WSS
- 性能参考：API P95 < 500ms（不含 LLM）

## 专题索引

| 文档 | 内容 |
|------|------|
| [datahub-architecture-plan.md](./datahub-architecture-plan.md) | DataHub |
| [websocket-broadcasting-architecture.md](./websocket-broadcasting-architecture.md) | WebSocket |
| [file-upload-readme.md](./file-upload-readme.md) | 文件上传 |
| [database-design.md](./database-design.md) | 数据库模块索引 |
| [ERROR_HANDLING_STANDARD.md](./ERROR_HANDLING_STANDARD.md) | 错误处理 |

UI 规范：`.cursor/rules/ui/ui-design-system.mdc`（不必另读 docs 副本）。
