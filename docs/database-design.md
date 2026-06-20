# 数据库设计

> 架构见 [architecture.md](./architecture.md)。**字段、约束、索引以 Model 与 Alembic migration 为准**（`/docs` OpenAPI 可辅助查阅）。

## 原则

- 带前缀 UUID 主键、`created_at` / `updated_at`
- 用户-角色-扩展表分离；状态字段软删除
- JSON 扩展复杂结构；API Key 等敏感字段 Fernet 加密
- 按业务域分模块，Model 与 `api/app/{module}/models/` 一一对应

## 模块与 Model 对照

| 业务域 | 主要表/主题 | Model 路径 |
|--------|------------|------------|
| 身份权限 | users, roles, tenants, permissions, … | `api/app/identity_access/models/` |
| 聊天 | conversations, messages, attachments | `api/app/chat/models/` |
| 客户 | customers, preferences | `api/app/customer/models/` |
| 通讯录 | friendships, groups, tags | `api/app/contacts/models/` |
| 数字人 | digital_humans, agent_configs | `api/app/digital_humans/models/` |
| 任务 | tasks, routing_rules, task_events | `api/app/tasks/models/` |
| AI / Agent | agent_configs, conversations, knowledge_bases | `api/app/ai/models/` |
| MCP | tool_groups, tools, call_logs | `api/app/mcp/models/` |
| 文件 | files, upload_sessions, chunks | `api/app/common/models/` |
| DataHub | jobs, datasets, object_index, quality_reports, … | `api/app/datahub/models/` |
| 系统 | system_settings | `api/app/system/models/` |

迁移脚本：`api/migrations/versions/`。

## 关系概图

```text
users ←→ user_roles ←→ roles
  ├── customers / operators / admins / digital_humans

conversations ←→ messages ←→ message_attachments
  └── participants    upload_sessions ←→ upload_chunks ←→ files

digital_humans ←→ digital_human_agent_configs

mcp_tool_groups ←→ mcp_tools ←→ mcp_call_logs

agent_configs ←→ agent_conversations ←→ agent_messages

datahub_job_runs ←→ datahub_job_tasks
datahub_object_index / datahub_dataset_watermarks / datahub_quality_reports
```

## 枚举

各模块枚举见对应 `enums.py` 或 Model 内 `Enum` 定义，例如：

- 聊天：`message_type`、`sender_type` → `api/app/chat/models/`
- 任务：任务状态、优先级 → `api/app/tasks/models/`
- DataHub：数据集、任务状态 → `api/app/datahub/enums.py`

## 维护

- 改表：先改 Model，再 `alembic revision --autogenerate`
- 备份：PostgreSQL 定期快照；MinIO 对象与 DB 索引分开备份
