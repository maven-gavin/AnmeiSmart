# DataHub 数据中台

> 实现细节见代码；表结构见 [database-design.md](./database-design.md)；系统上下文见 [architecture.md](./architecture.md)。

## 背景

系统依赖东方财富、BaoStock、同花顺等外部数据源做板块分析、资金流、个股分析与报告生成。外部接口存在失败、限流、延迟和口径不一致问题，直接调用会导致分析链路不稳定。

DataHub 在现有 **FastAPI + PostgreSQL + MinIO** 架构内建设统一数据层：上层只消费标准化数据，不直接依赖任一外部源。

## 要做什么

**目标**

- 一次性回填近 10 年历史数据，每晚增量更新最近若干交易日。
- 多数据源主备切换、失败重试、MinIO 标准层兜底。
- 保留 raw / normalized / features 分层；外部源故障时分析链路可降级，不整体中断。

**MVP 边界（不做）**

- 复杂 DAG 编排平台、实时流计算、企业级数据目录、多租户计费。
- MVP 验收：核心数据集稳定回填 +  nightly 增量 + 上层可观测降级。

**数据集**（见 `api/app/datahub/catalog.py`）

| 阶段 | 数据集 |
|------|--------|
| 核心 | `trading_calendar`、`security_master`、`market_daily` |
| 扩展 | `money_flow`、`sector_members`、`financial_summary` |

## 怎么做

### 数据流

```text
外部数据源 → Provider（适配/限流/重试）
          → Router（主备切换、熔断、MinIO 兜底）
          → raw（MinIO，保留原始响应）
          → normalize（统一口径）
          → quality（质量门禁）
          → normalized / features（MinIO）
          → PostgreSQL（索引、水位、任务状态）
          → /datahub API / 业务系统
```

### 落地原则

- 模块路径：`api/app/datahub/`，遵循 Controller / Service / Model / Schema / Deps 分层。
- **MinIO** 存 raw / normalized / features（Parquet）；**PostgreSQL** 只存元数据、任务、水位、质量报告。
- **Worker 独立于 API**：回填与增量不阻塞 FastAPI 主进程。
- 写入幂等；单 Provider / 单股票 / 单数据集失败不阻断全局。

### 运行方式

```bash
# 常驻 Worker（轮询 pending job）
api/scripts/start_datahub_worker.sh

# 或直接跑 job 模块
python -m app.datahub.jobs.backfill ...
python -m app.datahub.jobs.daily_incremental
```

API 负责：查询标准数据、触发任务、查看进度与质量状态。

### 读取策略

- 日常分析：**源站优先 → fallback → MinIO 兜底**
- 历史回测：**MinIO 标准层优先 → 源站补洞**

## 与什么有关

| 关联 | 说明 |
|------|------|
| [architecture.md](./architecture.md) | 模块化单体中的 `datahub` 模块与 Worker 隔离原则 |
| [database-design.md](./database-design.md) | `datahub_*` 元数据表 |
| MinIO | bucket `datahub`，路径规范见 `storage/minio_parquet_store.py` |
| 分析 / 报告 / Agent | 经 `/api/v1/datahub` 或内部 Service 读取，不直连外部源 |
| 管理端 | `web/src/app/admin/datahub/`（监控、自选列表） |
| Docker | Worker 可独立容器；MinIO 按环境变量配置 |

## 代码入口

```text
api/app/datahub/
├── catalog.py              # 数据集定义
├── providers/              # 外部源适配（base、baostock、eastmoney…）
├── services/
│   ├── router_service.py   # 主备路由
│   ├── storage_service.py  # MinIO 读写
│   ├── quality_service.py  # 质量检查
│   ├── market_daily_*      # 日线回填/增量/读取
│   └── ...
├── jobs/
│   ├── worker.py           # 常驻任务消费
│   ├── backfill.py
│   └── daily_incremental.py
├── controllers/datahub.py  # REST API
└── normalize.py            # 字段标准化

api/scripts/start_datahub_worker.sh
web/src/app/admin/datahub/
```

## 演进阶段

| 阶段 | 内容 | 状态 |
|------|------|------|
| 一 | 核心三数据集、MinIO 存储、元数据、Router fallback、Backfill / Incremental Job | 已落地 |
| 二 | 扩展数据集、feature store、前端监控看板、更多 Provider | 进行中 |
| 三 | 独立服务化、SDK / SQL 入口、权限审计与编排 | 规划 |
