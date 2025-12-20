## 部署指南（生产环境）

本项目包含后端 API（FastAPI）与前端 Web（Next.js）的 Docker 化部署方案。

### 1. 前置条件

- 已安装 Docker 与 Docker Compose
- 服务器已准备好域名与 HTTPS（推荐）
- 生产可用的 Postgres / Redis / MinIO（可复用宿主机或其他 Compose 项目里的服务）

### 2. 目录结构说明

- `api/`：后端 FastAPI
- `web/`：前端 Next.js
- `docker-compose.yml`：本项目的编排文件（本地/单机可用）
- `scripts/deploy.sh`：按环境文件自动化部署脚本（推荐生产使用）
- `env.example`：环境变量模板

### 3. 生产部署前必须理解的 3 个坑

- **(1) 容器内不要用 `localhost` 访问外部服务**：容器里的 `localhost` 指向容器自身，不是宿主机，也不是其它容器。
- **(2) Next.js 的 `NEXT_PUBLIC_*` 是“构建期变量”**：修改 `.env` 后，必须重新构建 `web` 镜像才会生效。
- **(3) 反向代理/跨域**：手机微信访问时如果前端仍请求 `http://localhost:8000`，请求会打到手机自己，后端自然看不到日志。生产环境必须用真实域名或同域反代。

### 4. 环境变量文件准备（推荐 `.env.prod`）

复制模板：

```bash
cp env.example .env.prod
```

然后编辑 `.env.prod`（示例字段如下，请按你的实际环境填写）：

- **数据库**
  - `DATABASE_URL=postgresql://user:pass@host:5432/anmeismart`
  - 如果数据库在宿主机：
    - macOS/Windows：`host.docker.internal`
    - Linux：推荐使用宿主机 IP 或者把数据库也纳入 compose 并走服务名

- **Redis**
  - `REDIS_URL=redis://:pass@host:6379`

- **MinIO（文件上传/预览）**
  - `MINIO_ENDPOINT=host:9000`
  - `MINIO_ACCESS_KEY=...`
  - `MINIO_SECRET_KEY=...`
  - `MINIO_BUCKET_NAME=chat-files`
  - 说明：如果你复用宿主机/其它项目的 MinIO，请不要在容器内写 `localhost:9000`，否则会连接到 API 容器自己并报 `Connection refused`。

- **前端公共配置（构建期，必须正确）**
  - `NEXT_PUBLIC_API_URL=https://anmei-api.jibu.club`
  - `NEXT_PUBLIC_WS_URL=wss://anmei-api.jibu.club/api/v1/ws`
  - 说明：`NEXT_PUBLIC_API_URL` 用于拼接 API 调用地址；`NEXT_PUBLIC_WS_URL` 用于 WebSocket。手机微信访问失败且后端无日志，通常就是这里仍指向 `localhost`。

### 5. 生产部署方式 A：使用脚本（推荐）

脚本会读取 `.env.<environment>` 并完成构建/运行。

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh prod
```

脚本做的事情：

- 读取 `.env.prod`
- 构建 `api` 镜像
- 构建 `web` 镜像（会把 `NEXT_PUBLIC_*` 变量 bake 进产物）
- 创建独立网络并启动容器

### 6. 生产部署方式 B：直接用 docker compose（单机）

如果你偏向手动：

```bash
# 让 docker compose 读取 .env（根目录）
cp .env.prod .env
docker compose up -d --build
```

只重建前端（常见于更新 `NEXT_PUBLIC_*`）：

```bash
docker compose up -d --build web
```

### 7. 数据库迁移说明（Alembic）

- API 容器启动时会自动执行迁移（`api/entrypoint.sh`）
- 迁移会重试等待数据库可用（默认 30 次，每次 2 秒）
- 可选配置：
  - `DB_MIGRATION_MAX_RETRIES`：最大重试次数
  - `DB_MIGRATION_RETRY_INTERVAL`：重试间隔（秒）
  - `SKIP_DB_MIGRATION=true`：跳过迁移（不推荐生产）

说明：迁移读取的数据库地址以 `DATABASE_URL` 为准（Docker/CI 环境更稳定）。

### 8. 反向代理与域名建议（生产必做）

推荐使用 Nginx：

- 前端域名：`https://anmei.jibu.club` -> 代理到 `web:3000`
- API 域名：`https://anmei-api.jibu.club` -> 代理到 `api:8000`
- WebSocket：`/api/v1/ws` 需要开启 `upgrade` 相关头

### 9. 部署后验证清单（一步步）

1. **容器状态**

```bash
docker compose ps
```

2. **API 健康检查**

- `GET https://anmei-api.jibu.club/api/v1/system/health`（或你实际的健康检查路径）

3. **前端登录**

- 手机微信里打开 `https://anmei.jibu.club` 登录
- 如果登录失败且后端无日志，优先检查 `NEXT_PUBLIC_API_URL / NEXT_PUBLIC_WS_URL` 是否仍指向 `localhost`

4. **文件上传/预览**

- 若出现 `localhost:9000 Connection refused`，说明 MinIO 地址配置仍在容器内指向了 `localhost`，应改为宿主机/服务名。

### 10. 常见问题排查

- **dockerproxy 镜像源 500**
  - 这是镜像代理服务不可用导致的拉取失败，可稍后重试或切换回官方镜像源。

- **改了 `.env` 但手机仍失败**
  - 多数情况是没有重建 `web`（Next 的构建期变量仍是旧的）
  - 执行：`docker compose up -d --build web`


