from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class DatahubDatasetInfo(BaseModel):
    id: str
    dataset_key: str
    layer: str
    schema_version: str
    description: Optional[str] = None
    is_active: str
    updated_at: datetime


class DatahubJobRunInfo(BaseModel):
    id: str
    job_type: str
    dataset: Optional[str] = None
    status: str
    trigger_source: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    task_total: int
    task_success: int
    task_failed: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PurgeJobRunsRequest(BaseModel):
    status: str = Field(..., description="按该状态批量删除运行记录，如 failed")
    limit: int = Field(100, ge=1, le=500, description="最多删除条数")


class PurgeJobRunsResult(BaseModel):
    deleted_count: int


class DatahubFailureGroupInfo(BaseModel):
    error_message: str
    count: int
    symbols: list[str] = Field(default_factory=list)


class DatahubRunFailureDetailInfo(BaseModel):
    run_id: str
    failed_count: int
    groups: list[DatahubFailureGroupInfo]
    tasks: list["DatahubJobTaskInfo"]


class RetryFailedTasksRequest(BaseModel):
    strategy: str = Field("immediate", description="重试策略：immediate/by_error")
    max_retry_attempts: int = Field(3, ge=1, le=10, description="超过该重试次数的失败任务将跳过")


class RetryFailedTasksResult(BaseModel):
    created_runs: int
    skipped_tasks: int
    retried_tasks: int
    retried_symbols: list[str] = Field(default_factory=list)


class MarketDailyMissingScanResult(BaseModel):
    dataset: str = "market_daily"
    start_date: date
    end_date: date
    reference_date: date
    expected_count: int
    existing_count: int
    missing_count: int
    missing_symbols: list[str] = Field(default_factory=list)


class FillMarketDailyMissingRequest(BaseModel):
    start_date: date
    end_date: date
    reference_date: Optional[date] = None
    max_symbols: int = Field(500, ge=1, le=5000)
    batch_size: int = Field(200, ge=1, le=1000)


class FillMarketDailyMissingResult(BaseModel):
    created_runs: int
    filled_symbols: int
    symbols: list[str] = Field(default_factory=list)


class DatahubJobTaskInfo(BaseModel):
    id: str
    job_run_id: str
    dataset: str
    symbol: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    attempts: int
    last_error: Optional[str] = None
    locked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DatahubQualityReportInfo(BaseModel):
    id: str
    dataset: str
    symbol: Optional[str] = None
    biz_date: Optional[date] = None
    quality_score: float
    severity: str
    issues: Optional[list[dict]] = None
    object_key: Optional[str] = None
    checked_at: datetime
    created_at: datetime


class DatahubObjectIndexInfo(BaseModel):
    id: str
    bucket: str
    object_key: str
    dataset: str
    layer: str
    provider: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    row_count: int
    schema_version: str
    content_hash: Optional[str] = None
    quality_score: Optional[float] = None
    created_at: datetime


class DatahubWorkerHeartbeatInfo(BaseModel):
    worker_name: str
    status: str
    last_heartbeat_at: datetime
    last_run_id: Optional[str] = None
    processed_count: int
    last_error: Optional[str] = None
    is_online: bool
    offline_threshold_seconds: int


class TriggerBackfillRequest(BaseModel):
    dataset: str = Field(..., description="数据集")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    symbol: Optional[str] = Field(None, description="证券代码，可选")
    symbols: Optional[list[str]] = Field(None, description="证券代码列表，可选，优先于 symbol")

    @model_validator(mode="after")
    def validate_symbol_fields(self) -> "TriggerBackfillRequest":
        if self.symbol and self.symbols:
            raise ValueError("symbol 与 symbols 不能同时传入")
        return self


class TriggerDailyIncrementalRequest(BaseModel):
    dataset: str = Field("market_daily", description="数据集")
    symbol: Optional[str] = Field(None, description="证券代码，可选")
    window_days: int = Field(7, ge=1, le=30, description="回溯窗口天数")
