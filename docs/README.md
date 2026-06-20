# AnmeiSmart 文档

企业 AI 门户。**先读 [architecture.md](./architecture.md)**，再按需查专题。

## 快速运行

```bash
# 后端
cd api && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && uvicorn app.main:app --reload

# 前端
cd web && npm install && npm run dev

# DataHub Worker（可选）
api/scripts/start_datahub_worker.sh
```

环境变量见 `api/env.example`。Docker：`docker-compose.yml`。

## 文档地图


| 读什么              | 文档                                                                                 | 何时读          |
| ---------------- | ---------------------------------------------------------------------------------- | ------------ |
| 系统是什么、模块怎么串      | [architecture.md](./architecture.md)                                               | 新人 / 改架构     |
| 表在哪个模块           | [database-design.md](./database-design.md)                                         | 写 SQL / 迁移   |
| 错误怎么处理           | [ERROR_HANDLING_STANDARD.md](./ERROR_HANDLING_STANDARD.md)                         | 写 API / 前端请求 |
| DataHub 为什么有、怎么跑 | [datahub-architecture-plan.md](./datahub-architecture-plan.md)                     | 数据中台相关       |
| WebSocket 推送     | [websocket-broadcasting-architecture.md](./websocket-broadcasting-architecture.md) | 实时消息         |
| 文件上传             | [file-upload-readme.md](./file-upload-readme.md)                                   | 上传 / MinIO   |


**字段、接口、样式细节以代码为准**（Model、OpenAPI `/docs`、`.cursor/rules/`）。

## 项目结构

```text
AnmeiSmart/
├── api/app/          # 后端业务域（路由聚合于 api/app/api.py）
├── web/src/          # Next.js 前端
├── docs/             # 本目录
└── docker-compose.yml
```

## 协作

- 分支：`main` / `dev` / `feature/*` / `hotfix/*`
- 提交：`feat` / `fix` / `docs` / `chore` + 描述
- 规范：`.cursor/rules/`（含 UI 设计系统、后端分层、错误处理）

