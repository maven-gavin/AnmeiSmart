# Dify 容器网络配置（AnmeiSmart 对接）

## 目标
- `anmei-smart-api`（本项目）需要调用 Dify Service API（推荐走 Dify 自带的 Nginx 反代）。

## 生产 / 容器内运行（推荐）
### 1) 打通 Docker Network
本项目 `docker-compose.yml` 已将 `anmei-smart-api` 加入 Dify 的 `docker_default` 网络（external network）。

前提：
- 先启动 Dify 的 docker compose（会创建 `docker_default` network）

### 2) Agent 配置（后台管理里填）
- **baseUrl**: `http://docker-nginx-1/v1`

说明：
- `docker-nginx-1` 是容器名（`docker ps` 可见），只在 Docker 网络内可解析。

## 本地调试 / 宿主机直接运行
如果你不通过容器运行 `anmei-smart-api`（例如 `python run_dev.py` 在宿主机启动），则不要使用 `docker-nginx-1`：

- **baseUrl**: `http://localhost/v1`（或 `http://127.0.0.1/v1`）

## 常见现象
- `GET /v1/info` 返回 **401**：正常（未携带 `Authorization: Bearer {API_KEY}`）。


