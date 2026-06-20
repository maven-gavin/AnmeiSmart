# 文件上传

> 系统上下文见 [architecture.md](./architecture.md)。

## 背景

聊天、Agent、数字人等场景需上传图片/文档/音频。文件存 MinIO，元数据存 PostgreSQL，大文件支持分片与断点续传。

## 要做什么

- 通用上传：`POST /api/v1/files/upload`（及分片相关端点）
- Agent 场景：上传后由 `/agent/*` 或消息附件引用 `file_id`（多模态对话）
- 统一 `files` 表索引，业务表引用 `file_id` 而非重复存 URL

## 数据流

```text
前端 FileSelector / MessageInput
  → /files/upload（或分片 init/chunk/complete）
  → FileService → MinIO + files 表
  → 业务（消息附件、Agent file_upload 等）
```

## 代码入口

```text
api/app/common/controllers/files.py    # REST 端点
api/app/common/services/file_service.py
api/app/common/models/file.py
api/app/common/models/upload.py

web/src/components/...                 # 上传与预览组件（按业务目录搜索 FileSelector）
```

## 配置

MinIO 与 bucket 见 `api/.env` / `env.example`（与 DataHub 可共用 MinIO 实例、不同 bucket 前缀）。

## 相关

- 错误处理：[ERROR_HANDLING_STANDARD.md](./ERROR_HANDLING_STANDARD.md)
