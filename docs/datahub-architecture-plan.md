# DataHub 数据中台开发说明（AnmeiSmart 落地版）

## 背景

当前系统同时依赖东方财富、BaoStock、同花顺等数据源。外部接口偶发失败、字段口径不一致、接口限流或数据延迟，会直接影响板块分析、资金流分析、个股分析和报告生成。

本方案目标是在 AnmeiSmart 当前 FastAPI + PostgreSQL + MinIO 架构内，建设一个可被多个分析系统复用的 DataHub。上层系统只消费 DataHub 提供的标准化数据，不直接依赖任一外部数据源。

## 建设目标

- 支持一次性获取近 10 年历史数据。
- 支持每晚定时增量更新当日及最近若干交易日数据。
- 支持多数据源主备切换、失败重试和 MinIO 标准数据兜底。
- 保留原始数据、标准化数据、质量报告和特征数据。
- 为量化分析、回测系统、选股系统、监控系统、报告系统提供统一数据入口。
- 外部数据源失败时，分析链路可以降级运行，而不是整体中断。

## 范围边界（避免第一阶段失焦）

第一阶段聚焦“稳定供数”而不是“全能平台”，以下能力明确不在 MVP 范围内：

- 不做复杂可视化编排平台（如 Airflow UI 级别 DAG 管理）。
- 不做实时流式计算（分钟级 Tick 或 Kafka 流处理）。
- 不做全量数据血缘图谱和企业级数据目录门户。
- 不做多租户计费与配额系统。

MVP 成功标准是：核心数据集稳定回填 + 每晚增量稳定 + 上层系统可观测降级。

## 当前项目落地原则

- DataHub 第一阶段作为 `api/app/datahub` 后端模块实现，遵循当前项目 Controller / Service / Model / Schema / Deps 分层规范。
- 元数据、任务状态、质量报告、Provider 健康状态使用现有 PostgreSQL，不额外引入 `metadata.sqlite`。
- 原始数据、标准化数据、特征数据统一存入 MinIO，PostgreSQL 只保存索引、状态和必要的查询元数据。
- 调度任务独立于 API 请求链路运行，避免历史回填或每日增量阻塞 FastAPI 主服务。
- 初期只实现最小可用闭环，不一次性接入过多数据源和复杂编排系统。

## 总体架构

```text
外部数据源
东方财富 / BaoStock / 同花顺 / AkShare / Tushare / 交易所 / 自建爬虫
        ↓
Provider Layer
数据源适配器、登录态、限流、重试、反爬处理
        ↓
Router Layer
主备源选择、失败切换、超时、熔断、MinIO 标准数据兜底
        ↓
Raw Data Lake
原始响应写入 MinIO，保留数据源原始字段
        ↓
Normalize Layer
统一股票代码、日期、字段、类型、币种、频率、复权口径
        ↓
Quality Layer
完整性、异常值、缺失值、时效性、跨源校验
        ↓
Canonical Store
标准化数据写入 MinIO，PostgreSQL 保存索引和水位
        ↓
Feature Layer
技术指标、资金流因子、板块因子、财务因子、情绪因子
        ↓
Data API
FastAPI / Python Service / CLI / DuckDB 临时查询
        ↓
业务系统
量化分析 / 回测 / 选股 / 监控 / 报告
```

## 核心模块

### 1. Provider Layer

每个外部数据源实现一个 Provider：

- `EastMoneyProvider`
- `BaoStockProvider`
- `TongHuaShunProvider`
- `AkShareProvider`
- `TushareProvider`

Provider 只负责获取原始数据，不做业务分析。

建议统一接口：

```python
get_daily_bars(symbol, start_date, end_date)
get_money_flow(symbol, start_date, end_date)
get_sector_list()
get_sector_members(sector_code, asof_date=None)
get_financial_statement(symbol, start_date, end_date)
get_index_constituents(index_code, asof_date=None)
get_security_master()
```

### 2. Router Layer

Router 决定某类数据从哪个数据源获取。

示例配置：

```yaml
market_daily:
  primary: baostock
  fallback:
    - eastmoney
    - minio_cache

money_flow:
  primary: eastmoney
  fallback:
    - tonghuashun
    - minio_cache

sector:
  primary: eastmoney
  fallback:
    - tonghuashun
    - minio_cache

financial:
  primary: baostock
  fallback:
    - eastmoney
    - minio_cache
```

Router 必须支持：

- 超时控制
- 自动重试
- 主备源切换
- provider 健康状态记录
- 熔断机制
- MinIO 标准层优先或源站优先策略
- 部分失败不影响全局任务

建议补充默认路由策略（便于工程实现一致）：

```text
单次请求超时：10s（可按数据集覆盖）
重试次数：2 次（指数退避 1s / 2s）
熔断阈值：最近 1 分钟失败率 > 50% 且样本数 >= 20
熔断恢复：30s 半开探测，成功后关闭熔断
```

读取优先级建议按场景固定，避免策略漂移：

- T+1 日常分析：`源站优先 -> fallback -> MinIO 兜底`
- 历史回测/重跑：`MinIO 标准层优先 -> 源站补洞`

### 3. Storage Layer

当前项目已有 MinIO，因此第一阶段直接使用：

```text
MinIO + Parquet + PostgreSQL metadata
```

MinIO bucket 建议：

```text
datahub
```

对象路径建议：

```text
raw/provider=baostock/dataset=market_daily/year=2024/month=01/batch_id=xxx.parquet
normalized/dataset=market_daily/year=2024/month=01/part-xxx.parquet
features/dataset=technical_features/year=2024/month=01/part-xxx.parquet
quality/dataset=market_daily/year=2024/month=01/report-xxx.json
```

`raw` 层保留外部接口原始字段，只补充元数据：

- `provider`
- `dataset`
- `api_name`
- `request_params`
- `request_start`
- `request_end`
- `ingest_time`
- `batch_id`
- `source_status`

`normalized` 层统一字段、类型和主键。

`features` 层存储供分析系统直接使用的指标和因子。

本地磁盘只作为临时工作目录，不作为长期数据源。Docker 部署时只需保证临时目录可写；长期数据以 MinIO 为准。

PostgreSQL 保存 MinIO 对象索引，例如：

```text
object_key
bucket
dataset
layer
provider
symbol
start_date
end_date
row_count
schema_version
content_hash
created_at
```

后续如果需要 SQL 分析，可以通过 DuckDB 临时读取 MinIO Parquet，不把 DuckDB 作为核心状态库。

### 4. Metadata Store

元数据使用当前项目 PostgreSQL，通过 SQLAlchemy Model + Alembic migration 管理。

建议表：

```text
datahub_job_runs
datahub_job_tasks
datahub_dataset_watermarks
datahub_provider_health
datahub_quality_reports
datahub_dataset_catalog
datahub_object_index
```

`datahub_job_tasks` 记录历史回填和增量任务：

```text
task_id
job_id
dataset
symbol
start_date
end_date
status
attempts
last_error
locked_at
created_at
updated_at
```

`datahub_dataset_watermarks` 记录每个数据集的最新成功位置：

```text
dataset
symbol
last_success_date
last_quality_score
last_object_key
updated_at
```

`datahub_provider_health` 记录数据源健康状态：

```text
provider
dataset
status
success_count
failure_count
last_success_at
last_failure_at
last_error
cooldown_until
updated_at
```

## 服务等级目标（SLO）

建议在方案中明确可验收的时效与可用性目标：

- 每晚增量任务：交易日 `T+1 06:30` 前完成核心数据集（`trading_calendar`、`security_master`、`market_daily`）更新。
- 数据可用性：核心数据集日级查询成功率 >= 99.5%（按周统计）。
- 降级可用性：任一主 Provider 故障时，核心接口 5 分钟内自动切换到 fallback。
- 质量门禁：核心数据集质量分低于阈值时禁止覆盖标准层，保留上一版可用快照。

质量阈值建议：

```text
core dataset（market_daily / security_master / trading_calendar）：quality_score >= 95
extended dataset（money_flow / sector_members / financial）：quality_score >= 90
```

### 5. Security Master 与交易日历

DataHub 不能只存行情和资金流，必须先建立证券主数据和交易日历，否则后续回填、增量、质量检查都会缺少基准。

证券主数据建议包含：

```text
symbol
exchange
name
list_date
delist_date
status
industry
source_provider
updated_at
```

交易日历建议包含：

```text
exchange
trade_date
is_open
previous_trade_date
next_trade_date
updated_at
```

代码映射建议单独维护：

```text
canonical_symbol
provider
provider_symbol
exchange
updated_at
```

复权和公司行为后续可独立成数据集：

```text
adjust_factors
dividends
splits
name_changes
```

## Schema 版本与兼容策略

当前文档提到 `schema_version`，但未定义升级规则。建议增加以下约束：

- 每个数据集维护 `major.minor` 版本（如 `1.2`）。
- `minor`：仅新增可空字段或扩展枚举，不破坏旧消费者。
- `major`：主键变化、字段语义变化或字段删除，需提供迁移说明。
- `normalized` 层对象路径包含 `schema_version`，避免新旧口径互相覆盖。
- API 默认返回当前稳定版本，可通过参数显式请求旧版本（保留窗口建议 >= 90 天）。

## 数据分层

### raw

保存原始接口返回到 MinIO，便于追溯和重放。raw 层不强制统一字段，只补充采集元数据和批次信息。

### normalized

保存项目统一口径的数据。

行情标准字段：

```text
symbol
trade_date
open
high
low
close
volume
amount
turnover_rate
adjust_type
source_provider
raw_object_key
updated_at
```

资金流标准字段：

```text
symbol
trade_date
main_net_inflow
large_net_inflow
medium_net_inflow
small_net_inflow
source_provider
raw_object_key
updated_at
```

板块成分标准字段：

```text
sector_code
sector_name
symbol
member_name
asof_date
source_provider
raw_object_key
updated_at
```

财务数据标准字段：

```text
symbol
report_date
pub_date
metric_name
metric_value
metric_group
source_provider
raw_object_key
updated_at
```

### features

保存分析系统可直接使用的特征。

示例：

- `ma5`
- `ma20`
- `rsi`
- `macd`
- `main_inflow_5d`
- `sector_rank_20d`
- `pe_percentile`
- `revenue_growth_yoy`

## 历史回填设计

历史回填用于一次性获取近 10 年数据。

不要一次性按全市场全时间拉取，应按数据域、股票、时间窗口切片。

示例任务：

```text
dataset=market_daily, symbol=000001.SZ, start=2016-01-01, end=2016-12-31
dataset=money_flow, symbol=000001.SZ, start=2024-01-01, end=2024-03-31
dataset=financial, symbol=000001.SZ, start=2016-01-01, end=2025-12-31
```

回填任务要求：

- 支持断点续跑。
- 支持失败重试。
- 支持分批限速。
- 已存在且质量合格的数据可以跳过。
- 每个数据集独立回填。
- 单只股票失败不影响其他股票。
- 每个任务的状态、错误和重试次数必须持久化。

建议先回填：

1. 交易日历
2. 股票基础信息和代码映射
3. 日线行情
4. 财务摘要
5. 板块列表和板块成分
6. 资金流

## 每晚增量设计

每日增量任务每晚定时运行。

不要只拉当天数据，建议覆盖最近若干交易日，用于处理外部数据延迟和修正。

推荐窗口：

```text
行情日线：最近 7 个交易日
资金流：最近 7 个交易日
板块成分：每日全量快照
财务数据：最近 2 个报告期
新闻/公告：最近 3 天
指数成分：每周或每月更新
```

写入必须是幂等的。

主键建议：

```text
raw 层：provider + dataset + symbol + date + batch_id
normalized 层：dataset + symbol + date + adjust_type/schema_version
```

normalized 层不把 `provider` 作为主键的一部分，否则同一天同一证券会产生多份标准数据。采用哪个数据源应通过 `source_provider`、`raw_object_key` 和质量报告追踪。

如果同一标准主键数据已存在，则覆盖更新；不存在则插入。

为避免“覆盖更新”误伤，建议补充发布机制：

- 新批次先写入 `staging` 对象并完成质量检查。
- 质量通过后再原子更新 `latest` 指针（或 manifest）。
- 查询层默认读取 `latest`，失败时可回滚到上一稳定版本。

## 调度设计

当前项目以 Docker 部署为主，初期推荐新增独立 worker/scheduler，而不是把重任务放进 FastAPI 主进程。

```text
docker compose
  ↓
datahub-worker
  ↓
python -m app.datahub.jobs.daily_incremental
```

历史回填也由 worker 执行：

```text
python -m app.datahub.jobs.backfill --dataset market_daily --start 2016-01-01
```

API 服务只负责查询数据状态、触发任务、展示任务进度和读取标准数据。

`docker-compose.yml` 后续建议增加：

```text
datahub-worker:
  build: ./api
  env_file:
    - .env
  command: python -m app.datahub.jobs.daily_incremental
```

如果需要常驻调度，可以先使用容器内轻量循环或宿主机 cron 触发一次性 worker；任务依赖复杂后再引入专业编排工具。

后续如果任务依赖复杂，再升级到：

- Prefect
- Dagster
- Airflow

小团队或个人阶段不建议一开始使用 Airflow，维护成本偏高。

## 最小依赖建议

第一阶段只引入实现 MVP 必需的依赖，避免 API 镜像过度膨胀。

建议新增：

```text
pandas
pyarrow
duckdb
baostock
```

暂缓新增：

```text
akshare
tushare
prefect
dagster
airflow
```

等 `market_daily`、`security_master`、`trading_calendar` 跑通后，再按数据源和任务复杂度逐步增加。

## 质量检查

每次入库后执行质量检查。

基础规则：

- 日期是否连续。
- 必填字段是否缺失。
- 价格是否小于等于 0。
- 成交量是否异常。
- 今日数据是否过期。
- 板块成分是否为空。
- 财报期是否重复。
- 多数据源价格差异是否过大。
- MinIO 对象是否存在。
- 对象行数、日期范围和 PostgreSQL 索引是否一致。

质量结果写入 `datahub_quality_reports`：

```text
dataset
symbol
date
quality_score
issues
severity
object_key
checked_at
```

上层分析系统应能读取质量状态，并根据质量结果决定是否降级。

建议新增跨表一致性检查（当前文档未覆盖）：

- `security_master.status=active` 的证券，在交易日应有对应行情或明确停牌标记。
- `sector_members.symbol` 必须能映射到有效 `security_master.symbol`。
- 财务数据 `pub_date >= report_date`，并符合报告期枚举约束。
- 同证券同交易日成交额与成交量、收盘价的关系不出现数量级异常。

建议统一质量问题等级，便于自动化处置：

```text
P0: 核心主键冲突 / 日期错位 / 大面积缺失（阻断发布）
P1: 局部缺失或跨源偏差超阈值（允许降级发布）
P2: 非关键字段异常（告警并继续）
```

## 安全与审计

当前方案缺少权限和审计约束，建议补充：

- DataHub 写接口仅允许 worker 身份调用，业务 API 默认为只读。
- MinIO 按前缀分权限：`raw/` 写权限最小化，`normalized/` 只允许发布流程写入。
- PostgreSQL 元数据表记录操作者与来源（`created_by`、`trigger_source`）。
- 所有手工重跑、回滚、强制发布都必须写审计日志。
- 敏感配置（第三方 token、账号）只存 `.env` / 密钥管理，不落库不入日志。

## 可观测性与告警

建议将“可观察”落到可执行指标：

- 任务指标：成功率、失败率、重试次数、任务耗时 P50/P95。
- 数据指标：当日覆盖率、缺失率、质量分分布、延迟分钟数。
- Provider 指标：调用成功率、429/5xx 占比、平均响应时间。
- 存储指标：MinIO 对象写入失败率、对象-索引不一致数。

告警建议：

- 连续 2 次每日增量失败 -> 立即告警。
- 核心数据集延迟超过 SLA 30 分钟 -> 告警。
- Provider 熔断持续超过 15 分钟 -> 告警。

## 降级策略

DataHub 不应因为单个数据源失败导致整体失败。

建议规则：

- 行情失败：优先读 MinIO 中最近一次质量合格的标准数据。
- 资金流失败：标记资金流缺失，继续生成其他分析。
- 板块数据失败：使用最近一次成功的板块快照。
- 财务数据失败：读取 MinIO 中最近一期质量合格数据。
- 新闻或公告失败：跳过该因子。

分析报告中应明确标记缺失数据，而不是静默忽略。

## 当前项目落地路径

第一阶段先在当前项目内实现：

```text
api/app/datahub/
├── __init__.py
├── controllers/
│   ├── __init__.py
│   └── datahub.py
├── services/
│   ├── __init__.py
│   ├── datahub_service.py
│   ├── metadata_service.py
│   ├── router_service.py
│   ├── storage_service.py
│   └── quality_service.py
├── models/
│   ├── __init__.py
│   ├── job.py
│   ├── dataset.py
│   ├── provider_health.py
│   └── quality_report.py
├── schemas/
│   ├── __init__.py
│   └── datahub.py
├── deps/
│   ├── __init__.py
│   └── datahub_deps.py
├── providers/
│   ├── __init__.py
│   ├── base.py
│   └── baostock_provider.py
├── storage/
│   ├── __init__.py
│   └── minio_parquet_store.py
├── catalog.py
├── normalize.py
├── enums.py
├── jobs/
│   ├── backfill.py
│   └── daily_incremental.py
└── cli.py
```

第一阶段目标：

- 跑通 `BackfillJob`。
- 跑通 `DailyIncrementalJob`。
- 支持 `security_master`、`trading_calendar`、`market_daily`。
- 支持 MinIO Parquet 存储。
- 支持 PostgreSQL 元数据、水位、对象索引和质量报告。
- 支持数据源失败后 fallback。
- 上层分析系统优先读取 DataHub 标准层。

第二阶段：

- 增加 `money_flow`、`sector_members`、`financial_summary`。
- 增加 feature store。
- 增加前端任务监控和数据质量看板。
- 增加更多 Provider 和跨源校验。

第三阶段：

- 独立部署为服务。
- 提供 REST API、Python SDK、SQL 查询入口。
- 支持更复杂的权限、审计、血缘和任务编排。

## 开发优先级

建议按以下顺序开发：

1. 定义 `dataset_catalog`、canonical schema 和 schema version。
2. 新增 PostgreSQL 元数据模型和 Alembic migration。
3. 实现 MinIO Parquet 存储与对象索引。
4. 实现 Provider 抽象和一个稳定 Provider。
5. 回填 `trading_calendar`、`security_master`、`symbol_mapping`。
6. 实现 `market_daily` 标准化、幂等写入和基础质量检查。
7. 实现 Router fallback 和 Provider 健康状态。
8. 实现 Backfill Job。
9. 实现 Daily Incremental Job。
10. 暴露 FastAPI 查询接口和任务状态接口。
11. 接入上层分析系统，优先读取 DataHub 标准层。

## 验收标准（Definition of Done）

第一阶段建议增加可量化验收项，避免“功能完成但不可运营”：

- 连续 7 个自然日每日增量任务成功率 >= 99%。
- 核心数据集在 `T+1 06:30` 前可查询，且质量分达标。
- 任一主 Provider 人工下线演练后，5 分钟内自动切换且链路不中断。
- 随机抽样 100 只证券，`normalized` 与 `raw` 可追溯链路完整。
- 回滚演练通过：可在 10 分钟内切回上一稳定版本。

## 关键原则

- 历史回填和每日增量必须幂等。
- 原始数据和标准数据都要保留在 MinIO。
- PostgreSQL 只保存元数据、索引、任务状态和质量状态。
- 外部接口只作为更新源，不作为分析时的强依赖。
- 多系统只能读 DataHub 标准接口，不直接调用外部数据源。
- 单数据源失败、单股票失败、单数据集失败，都不能阻断全局流程。
- 所有数据缺失和降级都要可观察、可追踪、可解释。
